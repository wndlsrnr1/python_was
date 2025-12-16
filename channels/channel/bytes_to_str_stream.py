import asyncio
from typing import AsyncIterator


class BytesToStrStream:

    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
        self._timeout = timeout

    async def _generate(self) -> AsyncIterator[str]:
        while True:
            try:
                bytes_args = await asyncio.wait_for(
                    self._queue.get(), timeout=self._timeout
                )

                if bytes_args is None:
                    break

                yield str(bytes_args)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break

    def __aiter__(self) -> AsyncIterator[str]:
        return self._generate()

    async def send(self, bytes_param: bytes) -> None:
        if self._closed:
            raise RuntimeError("Channel이 종료되었습니다.")

        if not bytes_param or not isinstance(bytes_param, bytes):
            return

        await self._queue.put(bytes_param)

    async def receive(self) -> AsyncIterator[str]:
        async for str_value in self:
            yield str_value

    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
