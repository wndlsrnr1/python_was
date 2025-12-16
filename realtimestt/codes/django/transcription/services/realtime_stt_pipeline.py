"""
실시간 STT Pipeline 구현

여러 Channel을 연결하여 비동기로 데이터를 흘려보내는 Pipeline입니다.
WebSocket → Audio → gRPC → Result → WebSocket 순서로 데이터를 처리합니다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from transcription.channels.audio_channels import AudioChannel
from transcription.channels.grpc_channels import gRPCChannel
from transcription.channels.result_channels import ResultChannel
from transcription.channels.websocket_channels import WebSocketChannel

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from channels.generic.websocket import AsyncWebsocketConsumer


class RealtimeSTTPipeline:
    """
    실시간 STT 전체 파이프라인

    여러 Channel을 연결하여 비동기로 데이터를 흘려보냅니다.
    WebSocket → Audio → gRPC → Result → WebSocket 순서로 처리합니다.
    """

    def __init__(
        self,
        websocket: "AsyncWebsocketConsumer",
        api_token: str,
        input_format: str = "webm",
        language_code: str = "ko-KR",
        interim_results: bool = True,
        server_address: str = "apis.daglo.ai:443",
        timeout: float = 1.0,
    ) -> None:
        """
        Args:
            websocket: Django Channels AsyncWebsocketConsumer 인스턴스
            api_token: gRPC API 인증 토큰 (필수)
            input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")
            language_code: 언어 코드 ("ko-KR", "en-US", "mixed")
            interim_results: 임시 결과 반환 여부 (기본값: True)
            server_address: gRPC 서버 주소 (기본값: "apis.daglo.ai:443")
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
        """
        if not api_token:
            raise ValueError("api_token은 필수입니다")

        # 각 단계별 Channel 생성
        self.websocket_channel = WebSocketChannel(websocket, timeout=timeout)
        self.audio_channel = AudioChannel(input_format=input_format, timeout=timeout)
        self.grpc_channel = gRPCChannel(
            api_token=api_token,
            server_address=server_address,
            language_code=language_code,
            interim_results=interim_results,
            timeout=10800,
        )
        self.result_channel = ResultChannel(timeout=timeout)

        self._running = False
        self._tasks: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        """
        전체 파이프라인 시작

        모든 Channel 연결 함수를 병렬로 실행합니다.
        """
        if self._running:
            logger.warning("[RealtimeSTTPipeline] Pipeline이 이미 실행 중입니다")
            return

        self._running = True
        logger.info("[RealtimeSTTPipeline] Pipeline 시작")

        try:
            # 모든 연결 함수를 병렬로 실행
            self._tasks = [
                asyncio.create_task(self._websocket_to_audio()),
                asyncio.create_task(self._audio_to_grpc()),
                asyncio.create_task(self._grpc_to_result()),
                asyncio.create_task(self._result_to_websocket()),
            ]

            # 모든 태스크 완료 대기
            await asyncio.gather(*self._tasks, return_exceptions=True)

            logger.info("[RealtimeSTTPipeline] Pipeline 완료")

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Pipeline 실행 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            self._running = False

    async def _websocket_to_audio(self) -> None:
        """
        WebSocket → Audio Channel 연결

        WebSocket 메시지를 받아 AudioChannel로 전달합니다.
        """
        logger.info("[RealtimeSTTPipeline] WebSocket → Audio 연결 시작")

        try:
            async for message in self.websocket_channel.receive():
                # 바이너리 메시지만 AudioChannel로 전달
                if isinstance(message, bytes):
                    await self.audio_channel.send(message)
                    logger.debug(
                        f"[RealtimeSTTPipeline] WebSocket → Audio: "
                        f"size={len(message)} bytes"
                    )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] WebSocket → Audio 연결 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            await self.audio_channel.close()
            logger.info("[RealtimeSTTPipeline] WebSocket → Audio 연결 종료")

    async def _audio_to_grpc(self) -> None:
        """
        Audio → gRPC Channel 연결

        AudioChannel의 PCM 청크를 받아 gRPCChannel로 전달합니다.
        """
        logger.info("[RealtimeSTTPipeline] Audio → gRPC 연결 시작")

        try:
            async for pcm_chunk in self.audio_channel.receive():
                if pcm_chunk and len(pcm_chunk) > 0:
                    await self.grpc_channel.send(pcm_chunk)
                    logger.debug(
                        f"[RealtimeSTTPipeline] Audio → gRPC: "
                        f"size={len(pcm_chunk)} bytes"
                    )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Audio → gRPC 연결 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            await self.grpc_channel.close()
            logger.info("[RealtimeSTTPipeline] Audio → gRPC 연결 종료")

    async def _grpc_to_result(self) -> None:
        """
        gRPC → Result Channel 연결

        gRPCChannel의 STT 결과를 받아 ResultChannel로 전달합니다.
        """
        logger.info("[RealtimeSTTPipeline] gRPC → Result 연결 시작")

        try:
            async for stt_result in self.grpc_channel.receive():
                await self.result_channel.send(stt_result)
                logger.debug(
                    f"[RealtimeSTTPipeline] gRPC → Result: "
                    f"transcript={stt_result.get('transcript', '')[:50]}..., "
                    f"is_final={stt_result.get('is_final', False)}"
                )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] gRPC → Result 연결 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            await self.result_channel.close()
            logger.info("[RealtimeSTTPipeline] gRPC → Result 연결 종료")

    async def _result_to_websocket(self) -> None:
        """
        Result → WebSocket 연결

        ResultChannel의 STT 결과를 받아 WebSocketChannel로 전달합니다.
        """
        logger.info("[RealtimeSTTPipeline] Result → WebSocket 연결 시작")

        try:
            async for result in self.result_channel.receive():
                await self.websocket_channel.send(data=result)
                logger.debug(
                    f"[RealtimeSTTPipeline] Result → WebSocket: "
                    f"transcript={result.get('transcript', '')[:50]}..."
                )

        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Result → WebSocket 연결 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
        finally:
            logger.info("[RealtimeSTTPipeline] Result → WebSocket 연결 종료")

    async def close_all(self) -> None:
        """
        모든 Channel 종료

        Pipeline의 모든 Channel을 안전하게 종료합니다.
        """
        logger.info("[RealtimeSTTPipeline] 모든 Channel 종료 시작")

        # 실행 중인 태스크 취소
        if self._tasks:
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # 태스크 완료 대기
            try:
                await asyncio.gather(*self._tasks, return_exceptions=True)
            except Exception as e:
                logger.warning(f"[RealtimeSTTPipeline] 태스크 취소 중 오류: {str(e)}")

        # 모든 Channel 종료
        try:
            await self.websocket_channel.close()
        except Exception as e:
            logger.warning(
                f"[RealtimeSTTPipeline] WebSocketChannel 종료 중 오류: {str(e)}"
            )

        try:
            await self.audio_channel.close()
        except Exception as e:
            logger.warning(f"[RealtimeSTTPipeline] AudioChannel 종료 중 오류: {str(e)}")

        try:
            await self.grpc_channel.close()
        except Exception as e:
            logger.warning(f"[RealtimeSTTPipeline] gRPCChannel 종료 중 오류: {str(e)}")

        try:
            await self.result_channel.close()
        except Exception as e:
            logger.warning(
                f"[RealtimeSTTPipeline] ResultChannel 종료 중 오류: {str(e)}"
            )

        self._running = False
        logger.info("[RealtimeSTTPipeline] 모든 Channel 종료 완료")
