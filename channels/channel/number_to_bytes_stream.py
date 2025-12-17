import asyncio
from typing import AsyncIterator


class NumberToBytesStream:

    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[int | None] = asyncio.Queue()
        self._closed = False
        self._timeout = timeout

    async def send(self, number: int) -> None:
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다.")

        if not isinstance(number, int):
            return

        await self._queue.put(number)

    async def receive(self) -> AsyncIterator[bytes]:
        async for item in self:
            yield item

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)

    async def _generate(self) -> AsyncIterator[bytes]:
        while True:
            try:
                number = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._timeout,
                )

                if number is None:
                    break

                # int를 bytes로 변환 (4바이트, big-endian)
                bytes_data = number.to_bytes(4, byteorder="big")
                yield bytes_data

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._generate()
