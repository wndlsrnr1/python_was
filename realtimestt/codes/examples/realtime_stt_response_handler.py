"""
실시간 STT WebSocket 응답 전송 Handler
"""

import json
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class ResponseHandler:
    """WebSocket 응답 전송 Handler"""

    async def send_ack(
        self,
        message: str,
        sequence_number: int,
        send_func: Callable[[str], Awaitable[None]],
    ) -> None:
        """확인 메시지 전송

        Args:
            message: ACK 메시지
            sequence_number: 시퀀스 번호
            send_func: WebSocket 전송 함수
        """
        ack_data = {
            "type": "ack",
            "message": message,
            "sequence": sequence_number,
        }
        ack_json = json.dumps(ack_data, ensure_ascii=False)
        await send_func(ack_json)

    async def send_error(
        self,
        error_message: str,
        send_func: Callable[[str], Awaitable[None]],
    ) -> None:
        """에러 메시지 전송

        Args:
            error_message: 에러 메시지
            send_func: WebSocket 전송 함수
        """
        error_data = {
            "type": "error",
            "data": error_message,
        }
        error_json = json.dumps(error_data, ensure_ascii=False)
        await send_func(error_json)
