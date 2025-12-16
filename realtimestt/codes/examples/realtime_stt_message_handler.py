"""
실시간 STT WebSocket 메시지 처리 Handler
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from asgiref.sync import sync_to_async
from django.utils import timezone

from datetime import datetime

from projects.models import Session
from projects.services import ServiceError
from shared_kernel.user import User
from transcription.services.realtime_stt_service import RealtimeSTTService
from transcription.consumers.exceptions import (
    RealtimeSTTValidationError,
    RealtimeSTTAuthenticationError,
)
from transcription.consumers.realtime_stt_helpers import (
    extract_session_id,
    extract_input_format,
)
from transcription.consumers.session_context import SessionContext

if TYPE_CHECKING:
    from transcription.consumers.realtime_stt_consumer import RealtimeSTTConsumer

logger = logging.getLogger(__name__)


class MessageHandler:
    """WebSocket 메시지 처리 Handler"""

    def __init__(self, consumer: "RealtimeSTTConsumer"):
        self.consumer = consumer
        self.audio_queue: asyncio.Queue[bytes] | None = None

    async def handle_text(
        self,
        data: dict[str, Any],
        context: SessionContext | None,
        send_error_func: callable,
    ) -> SessionContext | None:
        """텍스트 메시지 처리"""
        message_type = data.get("type")

        if message_type == "start":
            return await self.handle_start(data, send_error_func)
        elif message_type == "end":
            if context:
                await self.handle_end(context)
            return None
        elif message_type == "audio":
            sequence = data.get("sequence")
            size = data.get("size")
            timestamp = data.get("timestamp")
            logger.debug(
                f"Audio chunk metadata 수신: sequence={sequence}, size={size}, timestamp={timestamp}"
            )
            return context
        else:
            logger.warning(f"알 수 없는 메시지 타입: {message_type}")
            await send_error_func(f"Unknown message type: {message_type}")
            return context

    async def handle_start(
        self,
        data: dict[str, Any],
        send_error_func: callable,
    ) -> SessionContext | None:
        """시작 메시지 처리

        Args:
            data: 시작 메시지 데이터
            send_error_func: 에러 전송 함수

        Returns:
            SessionContext 또는 None (오류 시)
        """
        logger.info("세션 시작 요청 수신")

        try:
            mime_type = data.get("mimeType", "audio/webm;codecs=opus")
            config = data.get("config", {})

            try:
                session_id = extract_session_id(data)
            except RealtimeSTTValidationError as e:
                await send_error_func(str(e))
                return None

            user = self.consumer.scope.get("user")
            if not user or not user.is_authenticated:
                raise RealtimeSTTAuthenticationError("Authentication required")

            try:
                session = await sync_to_async(RealtimeSTTService.validate_session)(
                    session_id, user
                )
            except ServiceError as e:
                raise RealtimeSTTValidationError(str(e)) from e

            start_time = timezone.now()
            base_path = await sync_to_async(
                RealtimeSTTService.AudioPipeline.build_path
            )(session_id, start_time)

            input_format = extract_input_format(mime_type)
            language_code = session.language
            interim_results = config.get("interim_results", True)

            metadata = {
                "session_id": str(session_id),
                "mime_type": mime_type,
                "config": config,
                "start_time": start_time.isoformat(),
                "chunks": [],
            }

            try:
                metadata = await sync_to_async(
                    RealtimeSTTService.MetadataPipeline.validate
                )(metadata)
            except ServiceError as e:
                raise RealtimeSTTValidationError(str(e)) from e

            context = SessionContext(
                session_id=session_id,
                session=session,
                base_path=base_path,
                input_format=input_format,
                language_code=language_code,
                interim_results=interim_results,
                metadata=metadata,
                start_time=start_time,
                config=config,
                chunk_count=0,
                sequence_number=0,
            )

            self.audio_queue = asyncio.Queue()
            return context

        except RealtimeSTTValidationError as e:
            await send_error_func(str(e))
            return None
        except RealtimeSTTAuthenticationError as e:
            await send_error_func(str(e))
            return None
        except Exception as e:
            logger.error(
                f"Start message 처리 중 오류: {str(e)}",
                exc_info=True,
            )
            await send_error_func(f"Failed to start session: {str(e)}")
            return None

    async def handle_end(
        self,
        context: SessionContext,
        send_ack_func: callable,
        send_error_func: callable,
    ) -> None:
        """종료 메시지 처리

        Args:
            context: 세션 컨텍스트
            send_ack_func: ACK 전송 함수
            send_error_func: 에러 전송 함수
        """
        try:
            updated_metadata = context.metadata.copy()
            updated_metadata["total_chunks"] = context.chunk_count
            updated_metadata["end_time"] = timezone.now().isoformat()
            updated_metadata["duration_seconds"] = (
                timezone.now() - context.start_time
            ).total_seconds()

            await sync_to_async(RealtimeSTTService.MetadataPipeline.save_json)(
                context.base_path, updated_metadata
            )

            await send_ack_func("Session ended successfully")

            logger.info(
                f"Session ended: session_id={context.session_id}, "
                f"chunks={context.chunk_count}"
            )

        except Exception as e:
            logger.error(
                f"End message 처리 중 오류: {str(e)}",
                exc_info=True,
            )
            await send_error_func(f"Failed to end session: {str(e)}")

    async def handle_audio(
        self,
        bytes_data: bytes,
        context: SessionContext,
        audio_queue: asyncio.Queue[bytes],
        send_error_func: callable,
    ) -> SessionContext:
        """오디오 청크 처리

        Args:
            bytes_data: 오디오 청크 데이터
            context: 세션 컨텍스트
            audio_queue: 오디오 큐
            send_error_func: 에러 전송 함수

        Returns:
            업데이트된 SessionContext
        """
        if not bytes_data or len(bytes_data) == 0:
            logger.warning("Empty audio chunk received")
            return context

        chunk_size = len(bytes_data)
        logger.info(
            f"오디오 청크 수신: size={chunk_size} bytes, "
            f"session_id={context.session_id}"
        )

        try:
            await sync_to_async(RealtimeSTTService.AudioPipeline.append_chunk)(
                context.base_path, bytes_data
            )

            context = context.increment_chunk_count()
            context = context.increment_sequence_number()

            chunk_info = {
                "sequence": context.sequence_number,
                "size": chunk_size,
                "timestamp": timezone.now().isoformat(),
            }
            new_chunks = context.metadata.get("chunks", []) + [chunk_info]
            context = context.update_metadata({"chunks": new_chunks})

            if context.chunk_count % 10 == 0:
                await sync_to_async(RealtimeSTTService.MetadataPipeline.save_json)(
                    context.base_path, context.metadata
                )

            await audio_queue.put(bytes_data)

            return context

        except Exception as e:
            logger.error(
                f"Audio chunk 처리 중 오류: {str(e)}",
                exc_info=True,
            )
            await send_error_func(f"Failed to process audio chunk: {str(e)}")
            return context

    async def close_queue(self) -> None:
        """오디오 큐 종료 신호 전송"""
        if self.audio_queue:
            try:
                self.audio_queue.put_nowait(None)
            except Exception:
                pass
