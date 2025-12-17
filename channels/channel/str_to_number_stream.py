import asyncio
from typing import AsyncIterator


class StrToNumberStream:
    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._closed = False
        self._timeout = timeout

    async def send(self, word: str) -> None:
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다.")

        if not word or len(word) == 0:
            return

        await self._queue.put(word)

    async def receive(self) -> AsyncIterator[int]:
        async for item in self:
            yield item

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    async def _generate(self) -> AsyncIterator[int]:
        while True:
            try:
                word = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)

                if word is None:
                    break

                number = int(word)
                yield number

            except asyncio.TimeoutError:
                # 타임아웃 발생 시 계속 대기
                continue
            except ValueError:
                # 숫자로 변환할 수 없으면 스킵
                continue

    def __aiter__(self) -> AsyncIterator[int]:
        return self._generate()
