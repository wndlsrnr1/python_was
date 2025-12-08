"""
실시간 STT WebSocket Consumer
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from projects.models import Session
from shared_kernel.user import User
from transcription.services.realtime_stt_service import RealtimeSTTService
from transcription.consumers.realtime_stt_message_handler import MessageHandler
from transcription.consumers.realtime_stt_response_handler import ResponseHandler
from transcription.consumers.realtime_stt_stt_handler import STTHandler
from transcription.consumers.session_context import SessionContext

logger = logging.getLogger(__name__)


class RealtimeSTTConsumer(AsyncWebsocketConsumer):
    """실시간 STT WebSocket Consumer

    오디오 데이터를 실시간으로 수신하고 파일 시스템에 저장합니다.
    """

    async def connect(self) -> None:
        """WebSocket 연결 수립"""
        scope = self.scope
        client_host = (
            scope.get("client", [None, None])[0] if scope.get("client") else "unknown"
        )

        logger.info(f"WebSocket 연결 시도: client={client_host}")

        try:
            await self.accept()

            # 세션 컨텍스트 초기화
            self.session_context: SessionContext | None = None
            self.stt_processing_task: asyncio.Task[None] | None = None

            # Handler 초기화
            self.message_handler = MessageHandler(self)
            self.response_handler = ResponseHandler()
            self.stt_handler = STTHandler()

            user = scope.get("user")
            if user and user.is_authenticated:
                logger.info(f"WebSocket 연결 수립 성공: user_id={user.id}")
            else:
                logger.warning(f"WebSocket 연결 수립 (인증 없음): client={client_host}")

        except Exception as e:
            logger.error(
                f"WebSocket 연결 수립 실패: client={client_host}, error={str(e)}",
                exc_info=True,
            )
            raise

    async def disconnect(self, close_code: int) -> None:
        """WebSocket 연결 종료"""
        session_id = self.session_context.session_id if self.session_context else None
        chunk_count = self.session_context.chunk_count if self.session_context else 0

        logger.info(
            f"WebSocket 연결 종료 시작: session_id={session_id}, "
            f"close_code={close_code}, chunks={chunk_count}"
        )

        try:
            if self.stt_processing_task and not self.stt_processing_task.done():
                self.stt_processing_task.cancel()
                try:
                    await self.stt_processing_task
                except asyncio.CancelledError:
                    logger.info("STT 처리 태스크 취소됨")

            await self.message_handler.close_queue()

            if self.session_context:
                updated_metadata = self.session_context.metadata.copy()
                updated_metadata["total_chunks"] = self.session_context.chunk_count
                updated_metadata["end_time"] = timezone.now().isoformat()
                updated_metadata["duration_seconds"] = (
                    timezone.now() - self.session_context.start_time
                ).total_seconds()

                await sync_to_async(RealtimeSTTService.MetadataPipeline.save_json)(
                    self.session_context.base_path, updated_metadata
                )

                logger.info(
                    f"최종 메타데이터 저장 완료: session_id={session_id}, "
                    f"path={self.session_context.base_path}"
                )

            logger.info(
                f"WebSocket 연결 종료 완료: session_id={session_id}, "
                f"close_code={close_code}, chunks={chunk_count}"
            )
        except Exception as e:
            logger.error(
                f"연결 종료 중 오류: session_id={session_id}, "
                f"close_code={close_code}, error={str(e)}",
                exc_info=True,
            )

    async def receive(
        self, text_data: str | None = None, bytes_data: bytes | None = None
    ) -> None:
        """메시지 수신 처리"""

        async def send_func(text: str) -> None:
            await self.send(text_data=text)

        async def send_error_func(message: str) -> None:
            await self.response_handler.send_error(message, send_func)

        async def send_ack_func(message: str) -> None:
            sequence = (
                self.session_context.sequence_number if self.session_context else 0
            )
            await self.response_handler.send_ack(message, sequence, send_func)

        if text_data:
            try:
                data = json.loads(text_data)
                result = await self.message_handler.handle_text(
                    data, self.session_context, send_error_func
                )
                if result is not None:
                    self.session_context = result
                    if data.get("type") == "start":
                        await send_ack_func("Session started successfully")
                        self.stt_processing_task = asyncio.create_task(
                            self.stt_handler.process_stream(
                                self.message_handler.audio_queue,
                                self.session_context.session_id,
                                self.session_context.language_code,
                                self.session_context.interim_results,
                                self.session_context.input_format,
                                send_func,
                                send_error_func,
                                lambda: (
                                    self.session_context.sequence_number
                                    if self.session_context
                                    else 0
                                ),
                            )
                        )
                elif data.get("type") == "end" and self.session_context:
                    await self.message_handler.handle_end(
                        self.session_context, send_ack_func, send_error_func
                    )
                    await self.close()
            except json.JSONDecodeError as e:
                logger.error(
                    f"JSON 파싱 실패: text_data={text_data[:200]}, error={str(e)}"
                )
                await send_error_func("Invalid JSON format")

        elif bytes_data:
            if self.session_context:
                self.session_context = await self.message_handler.handle_audio(
                    bytes_data,
                    self.session_context,
                    self.message_handler.audio_queue,
                    send_error_func,
                )
            else:
                await send_error_func(
                    "Session not started. Send 'start' message first."
                )
        else:
            logger.warning("빈 메시지 수신: text_data와 bytes_data가 모두 None입니다")
