"""
실시간 STT Pipeline 기반 WebSocket Consumer

Pipeline을 사용하여 WebSocket → Audio → gRPC → Result → WebSocket 흐름을 처리합니다.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from transcription.services.realtime_stt_config_service import (
    RealtimeSTTConfigService,
)
from transcription.services.realtime_stt_pipeline import RealtimeSTTPipeline
from transcription.consumers.exceptions import (
    RealtimeSTTConfigurationError,
    RealtimeSTTNotFoundError,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


class RealtimeSTTPipelineConsumer(AsyncWebsocketConsumer):
    """
    실시간 STT Pipeline 기반 WebSocket Consumer

    Pipeline을 사용하여 여러 Channel을 연결하고 비동기로 데이터를 흘려보냅니다.
    """

    async def connect(self) -> None:
        """WebSocket 연결 수립"""
        scope = self.scope
        client_host = (
            scope.get("client", [None, None])[0] if scope.get("client") else "unknown"
        )

        logger.info(
            f"[RealtimeSTTPipelineConsumer] WebSocket 연결 시도: client={client_host}"
        )

        try:
            await self.accept()

            # Pipeline 초기화 (아직 시작하지 않음)
            self.pipeline: RealtimeSTTPipeline | None = None
            self.pipeline_task: asyncio.Task[None] | None = None
            self._session_started = False

            user = scope.get("user")
            if user and user.is_authenticated:
                logger.info(
                    f"[RealtimeSTTPipelineConsumer] WebSocket 연결 수립 성공: user_id={user.id}"
                )
            else:
                logger.warning(
                    f"[RealtimeSTTPipelineConsumer] WebSocket 연결 수립 (인증 없음): "
                    f"client={client_host}"
                )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipelineConsumer] WebSocket 연결 수립 실패: "
                f"client={client_host}, error={str(e)}",
                exc_info=True,
            )
            raise

    async def disconnect(self, close_code: int) -> None:
        """WebSocket 연결 종료"""
        logger.info(
            f"[RealtimeSTTPipelineConsumer] WebSocket 연결 종료 시작: close_code={close_code}"
        )

        try:
            # Pipeline 종료
            if self.pipeline:
                try:
                    await self.pipeline.close_all()
                except Exception as e:
                    logger.warning(
                        f"[RealtimeSTTPipelineConsumer] Pipeline 종료 중 오류: {str(e)}"
                    )

            # Pipeline 태스크 취소
            if self.pipeline_task and not self.pipeline_task.done():
                self.pipeline_task.cancel()
                try:
                    await self.pipeline_task
                except asyncio.CancelledError:
                    logger.info("[RealtimeSTTPipelineConsumer] Pipeline 태스크 취소됨")

            logger.info(
                f"[RealtimeSTTPipelineConsumer] WebSocket 연결 종료 완료: close_code={close_code}"
            )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipelineConsumer] 연결 종료 중 오류: close_code={close_code}, "
                f"error={str(e)}",
                exc_info=True,
            )

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        """메시지 수신 처리"""

        if text_data:
            try:
                data = json.loads(text_data)
                message_type = data.get("type")

                if message_type == "start":
                    await self._handle_start(data)
                elif message_type == "end":
                    await self._handle_end()
                else:
                    logger.warning(
                        f"[RealtimeSTTPipelineConsumer] 알 수 없는 메시지 타입: {message_type}"
                    )

            except json.JSONDecodeError as e:
                logger.error(
                    f"[RealtimeSTTPipelineConsumer] JSON 파싱 실패: "
                    f"text_data={text_data[:200]}, error={str(e)}"
                )
                await self._send_error("Invalid JSON format")

        elif bytes_data:
            # 오디오 청크를 Pipeline의 WebSocketChannel로 전달
            if self.pipeline and self._session_started:
                await self.pipeline.websocket_channel.receive_message(
                    bytes_data=bytes_data
                )
            else:
                logger.warning(
                    "[RealtimeSTTPipelineConsumer] 세션이 시작되지 않았습니다. "
                    "'start' 메시지를 먼저 보내주세요."
                )
                await self._send_error(
                    "Session not started. Send 'start' message first."
                )

        else:
            logger.warning(
                "[RealtimeSTTPipelineConsumer] 빈 메시지 수신: "
                "text_data와 bytes_data가 모두 None입니다"
            )

    async def _handle_start(self, data: dict) -> None:
        """세션 시작 처리"""
        if self._session_started:
            logger.warning("[RealtimeSTTPipelineConsumer] 세션이 이미 시작되었습니다")
            return

        try:
            # STT 설정 조회
            stt_config = await sync_to_async(RealtimeSTTConfigService.get_active)()
            if not stt_config:
                raise RealtimeSTTNotFoundError("활성 STT 설정을 찾을 수 없습니다")

            if stt_config.provider != "DAGLO":
                raise RealtimeSTTConfigurationError(
                    f"실시간 STT는 DAGLO만 지원합니다. 현재 provider: {stt_config.provider}"
                )

            api_token = await sync_to_async(
                RealtimeSTTConfigService.get_decrypted_api_key
            )(stt_config)
            if not api_token:
                raise RealtimeSTTConfigurationError("API 키를 찾을 수 없습니다")

            # 설정 추출
            mime_type = data.get("mimeType", "audio/webm;codecs=opus")
            config = data.get("config", {})
            input_format = self._extract_input_format(mime_type)
            language_code = config.get("language_code", "ko-KR")
            interim_results = config.get("interim_results", True)

            # Pipeline 생성
            self.pipeline = RealtimeSTTPipeline(
                websocket=self,
                api_token=api_token,
                input_format=input_format,
                language_code=language_code,
                interim_results=interim_results,
            )

            # Pipeline 시작
            self.pipeline_task = asyncio.create_task(self.pipeline.start())
            self._session_started = True

            logger.info(
                f"[RealtimeSTTPipelineConsumer] 세션 시작 완료: "
                f"input_format={input_format}, language_code={language_code}, "
                f"interim_results={interim_results}"
            )

            # ACK 전송
            await self._send_ack("Session started successfully", 0)

        except RealtimeSTTNotFoundError as e:
            logger.error(f"[RealtimeSTTPipelineConsumer] {str(e)}")
            await self._send_error(str(e))
        except RealtimeSTTConfigurationError as e:
            logger.error(f"[RealtimeSTTPipelineConsumer] {str(e)}")
            await self._send_error(str(e))
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipelineConsumer] 세션 시작 중 오류: {str(e)}",
                exc_info=True,
            )
            await self._send_error(f"Failed to start session: {str(e)}")

    async def _handle_end(self) -> None:
        """세션 종료 처리"""
        if not self._session_started:
            logger.warning("[RealtimeSTTPipelineConsumer] 세션이 시작되지 않았습니다")
            return

        try:
            # Pipeline 종료
            if self.pipeline:
                await self.pipeline.close_all()

            # Pipeline 태스크 취소
            if self.pipeline_task and not self.pipeline_task.done():
                self.pipeline_task.cancel()
                try:
                    await self.pipeline_task
                except asyncio.CancelledError:
                    pass

            self._session_started = False

            logger.info("[RealtimeSTTPipelineConsumer] 세션 종료 완료")

            # ACK 전송
            await self._send_ack("Session ended successfully", 0)

            # WebSocket 연결 종료
            await self.close()

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipelineConsumer] 세션 종료 중 오류: {str(e)}",
                exc_info=True,
            )
            await self._send_error(f"Failed to end session: {str(e)}")

    def _extract_input_format(self, mime_type: str) -> str:
        """MIME 타입에서 입력 형식 추출"""
        mime_lower = mime_type.lower()
        if "webm" in mime_lower:
            return "webm"
        elif "mp4" in mime_lower:
            return "mp4"
        elif "wav" in mime_lower:
            return "wav"
        elif "mp3" in mime_lower:
            return "mp3"
        else:
            return "webm"  # 기본값

    async def _send_ack(self, message: str, sequence: int) -> None:
        """ACK 메시지 전송"""
        ack_data = {
            "type": "ack",
            "message": message,
            "sequence": sequence,
        }
        ack_json = json.dumps(ack_data, ensure_ascii=False)
        await self.send(text_data=ack_json)

    async def _send_error(self, error_message: str) -> None:
        """에러 메시지 전송"""
        error_data = {
            "type": "error",
            "data": error_message,
        }
        error_json = json.dumps(error_data, ensure_ascii=False)
        await self.send(text_data=error_json)
