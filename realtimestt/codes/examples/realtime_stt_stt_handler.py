"""
실시간 STT 스트림 처리 Handler
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async

from transcription.services.realtime_stt_config_service import (
    RealtimeSTTConfigService,
)
from transcription.services.realtime_stt_service import RealtimeSTTService
from transcription.consumers.exceptions import (
    RealtimeSTTConfigurationError,
    RealtimeSTTNotFoundError,
)

logger = logging.getLogger(__name__)


class STTHandler:
    """STT 스트림 처리 Handler"""

    async def process_stream(
        self,
        audio_queue: asyncio.Queue[bytes],
        session_id: UUID,
        language_code: str,
        interim_results: bool,
        input_format: str,
        send_func: Callable[[str], Awaitable[None]],
        send_error_func: Callable[[str], Awaitable[None]],
        get_sequence_number: Callable[[], int],
    ) -> None:
        """STT 스트림을 처리하고 결과를 WebSocket으로 전송합니다

        Args:
            audio_queue: 오디오 청크를 담는 큐
            session_id: 세션 ID
            language_code: 언어 코드
            interim_results: 임시 결과 반환 여부
            input_format: 입력 오디오 형식
            send_func: WebSocket 전송 함수
            send_error_func: 에러 전송 함수
            get_sequence_number: 시퀀스 번호 조회 함수
        """
        try:
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

            result_count = 0
            async for result in RealtimeSTTService.STTPipeline.process_stream(
                audio_queue,
                session_id,
                stt_config=stt_config,
                api_token=api_token,
                language_code=language_code,
                interim_results=interim_results,
                input_format=input_format,
            ):
                result_count += 1
                transcript = result.get("transcript", "")

                transcription_data = {
                    "type": "transcription",
                    "data": {
                        "transcript": transcript,
                        "is_final": result.get("is_final", False),
                        "language_code": result.get("language_code", ""),
                        "total_duration": result.get("total_duration", 0.0),
                    },
                    "sequence": get_sequence_number(),
                }
                transcription_json = json.dumps(transcription_data, ensure_ascii=False)

                try:
                    await send_func(transcription_json)
                except Exception as send_error:
                    logger.error(
                        f"WebSocket 전송 중 오류: session_id={session_id}, "
                        f"error={str(send_error)}",
                        exc_info=True,
                    )

            logger.info(
                f"STT 스트림 처리 완료: session_id={session_id}, "
                f"총 결과 수={result_count}"
            )

        except asyncio.CancelledError:
            logger.debug(f"STT 처리 태스크 취소됨: session_id={session_id}")
            raise
        except Exception as e:
            logger.error(
                f"STT 스트림 처리 중 예외 발생: session_id={session_id}, "
                f"error={str(e)}",
                exc_info=True,
            )
            try:
                await send_error_func(f"STT 처리 실패: {str(e)}")
            except Exception as send_error:
                logger.error(
                    f"오류 메시지 전송 실패: session_id={session_id}, "
                    f"error={str(send_error)}",
                    exc_info=True,
                )
