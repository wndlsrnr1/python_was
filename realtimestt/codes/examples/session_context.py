"""
실시간 STT 세션 컨텍스트 DTO
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from projects.models import Session


@dataclass
class SessionContext:
    """실시간 STT 세션 컨텍스트

    세션 처리에 필요한 모든 상태를 담는 불변 데이터 구조입니다.
    """

    session_id: UUID
    session: Session
    base_path: str
    input_format: str
    language_code: str
    interim_results: bool
    metadata: dict[str, Any]
    start_time: datetime
    config: dict[str, Any] = field(default_factory=dict)
    chunk_count: int = 0
    sequence_number: int = 0

    def increment_chunk_count(self) -> "SessionContext":
        """청크 개수를 증가시킨 새로운 컨텍스트 반환"""
        return SessionContext(
            session_id=self.session_id,
            session=self.session,
            base_path=self.base_path,
            input_format=self.input_format,
            language_code=self.language_code,
            interim_results=self.interim_results,
            metadata=self.metadata.copy(),
            start_time=self.start_time,
            config=self.config.copy(),
            chunk_count=self.chunk_count + 1,
            sequence_number=self.sequence_number,
        )

    def increment_sequence_number(self) -> "SessionContext":
        """시퀀스 번호를 증가시킨 새로운 컨텍스트 반환"""
        return SessionContext(
            session_id=self.session_id,
            session=self.session,
            base_path=self.base_path,
            input_format=self.input_format,
            language_code=self.language_code,
            interim_results=self.interim_results,
            metadata=self.metadata.copy(),
            start_time=self.start_time,
            config=self.config.copy(),
            chunk_count=self.chunk_count,
            sequence_number=self.sequence_number + 1,
        )

    def update_metadata(self, updates: dict[str, Any]) -> "SessionContext":
        """메타데이터를 업데이트한 새로운 컨텍스트 반환"""
        new_metadata = self.metadata.copy()
        new_metadata.update(updates)
        return SessionContext(
            session_id=self.session_id,
            session=self.session,
            base_path=self.base_path,
            input_format=self.input_format,
            language_code=self.language_code,
            interim_results=self.interim_results,
            metadata=new_metadata,
            start_time=self.start_time,
            config=self.config.copy(),
            chunk_count=self.chunk_count,
            sequence_number=self.sequence_number,
        )
