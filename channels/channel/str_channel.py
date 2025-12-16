import asyncio
from typing import AsyncIterator


class StrChannel:
    """
    문자열을 받아서 내부 큐에 저장하고, receive로 받을 수 있는 기본 Channel
    """

    def __init__(self, timeout: float = 1.0) -> None:
        """
        Args:
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
        """
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._closed = False
        self._timeout = timeout

    async def send(self, text: str) -> None:
        """
        문자열을 내부 큐에 추가합니다.

        Args:
            text: 전송할 문자열
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다.")

        if not text or len(text) == 0:
            return

        await self._queue.put(text)

    async def receive(self) -> AsyncIterator[str]:
        """
        async for에서 사용 가능한 receive 메서드

        Yields:
            str: 문자열
        """
        async for item in self:
            yield item

    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    def __aiter__(self) -> AsyncIterator[str]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()

    async def _generate(self) -> AsyncIterator[str]:
        """
        내부 generator

        큐에서 문자열을 가져와 yield합니다.
        """
        while True:
            try:
                text = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._timeout,
                )

                if text is None:
                    break

                yield text

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break
