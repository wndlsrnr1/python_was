"""
실시간 STT Consumer 헬퍼 함수
"""

from typing import Any
from uuid import UUID

from transcription.consumers.exceptions import RealtimeSTTValidationError


def extract_session_id(data: dict[str, Any]) -> UUID:
    """세션 ID 추출 및 검증"""
    session_id_str = data.get("session_id")
    if not session_id_str:
        raise RealtimeSTTValidationError("session_id is required")
    try:
        return UUID(session_id_str)
    except ValueError as e:
        raise RealtimeSTTValidationError(
            f"Invalid session_id format: {session_id_str}"
        ) from e


def extract_input_format(mime_type: str) -> str:
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
