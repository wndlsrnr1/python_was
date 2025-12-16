import asyncio
from collections.abc import AsyncIterator
from multiprocessing import Value


class NumberAsyncIterator(AsyncIterator):
    """숫자를 비동기적으로 생성하는 AsyncIterator"""

    def __init__(self, start: int, end: int, delay: float = 0.1) -> None:
        self.start = start
        self.end = end
        self.delay = delay
        self.current = start

    def __aiter__(self) -> "NumberAsyncIterator":
        return self

    async def __anext__(self) -> int:
        if self.current >= self.end:
            raise StopAsyncIteration

        await asyncio.sleep(self.delay)

        value: int = self.current
        self.current += 1
        return value


async def run():
    async_iterator: NumberAsyncIterator = NumberAsyncIterator(0, 5, delay=0.1)

    async for number in async_iterator:
        print(f"[메인] 받은 숫자: {number}")


asyncio.run(run())
