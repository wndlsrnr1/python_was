import asyncio
from typing import AsyncIterator


class NumberChannel:

    def __init__(self, timeout) -> None:
        self._queue = asyncio.Queue[int] = asyncio.Queue()
        self._closed = False
        self._timeout = timeout

    async def send(self, number: int):

        pass

    async def close(self):
        pass

    async def receive(self) -> AsyncIterator[int]:
        pass

    async def _generate(self) -> AsyncIterator[int]:
        pass

    async def __aiter__(self) -> AsyncIterator[int]:
        return self._generate()
