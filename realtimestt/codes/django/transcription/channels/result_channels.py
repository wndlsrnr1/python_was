"""
Result Channel 구현

STT 결과를 버퍼링하는 Result Channel.
Channel 패턴을 따르며, STT 결과를 입력받아 버퍼링하고 출력합니다.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


class ResultChannel:
    """
    STT 결과를 버퍼링하는 Result Channel

    Channel 패턴을 따르며, STT 결과를 입력받아 버퍼링하고 출력합니다.
    변환 없이 단순히 큐를 통해 버퍼링만 수행합니다.
    """

    def __init__(self, timeout: float = 1.0) -> None:
        """
        Args:
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
        """
        self._timeout = timeout
        self._queue: asyncio.Queue[dict[str, str | bool | float] | None] = (
            asyncio.Queue()
        )
        self._closed = False

    async def send(self, result: dict[str, str | bool | float]) -> None:
        """
        STT 결과를 내부 큐에 추가합니다.

        Args:
            result: STT 결과 딕셔너리
                - transcript: str - 인식된 텍스트
                - is_final: bool - 최종 결과 여부
                - language_code: str - 언어 코드
                - total_duration: float - 전체 오디오 지속 시간 (초)
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")

        if not result:
            logger.warning("[ResultChannel] 빈 결과 수신, 무시합니다")
            return

        await self._queue.put(result)

    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if self._closed:
            return

        self._closed = True
        await self._queue.put(None)

    async def receive(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """
        async for에서 사용 가능한 receive 메서드

        send()에 대응하는 메서드로, STT 결과를 받습니다.

        Yields:
            dict[str, str | bool | float]: STT 결과 딕셔너리
                - transcript: str - 인식된 텍스트
                - is_final: bool - 최종 결과 여부
                - language_code: str - 언어 코드
                - total_duration: float - 전체 오디오 지속 시간 (초)
        """
        async for item in self:
            yield item

    def __aiter__(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()

    async def _generate(self) -> AsyncIterator[dict[str, str | bool | float]]:
        """
        내부 generator

        큐에서 STT 결과를 가져와 yield합니다.
        """
        result_count = 0

        try:
            while True:
                try:
                    result = await asyncio.wait_for(
                        self._queue.get(), timeout=self._timeout
                    )

                    if result is None:
                        logger.info(
                            f"[ResultChannel] 종료 신호 수신, "
                            f"총 {result_count}개 결과 처리"
                        )
                        break

                    result_count += 1
                    logger.debug(
                        f"[ResultChannel] STT 결과 처리: "
                        f"result={result_count}, "
                        f"transcript={result.get('transcript', '')[:50]}..., "
                        f"is_final={result.get('is_final', False)}"
                    )
                    yield result

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(
                        f"[ResultChannel] STT 결과 처리 중 오류: {str(e)}",
                        exc_info=True,
                    )
                    break

        except Exception as e:
            logger.error(
                f"[ResultChannel] 제너레이터 실행 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
