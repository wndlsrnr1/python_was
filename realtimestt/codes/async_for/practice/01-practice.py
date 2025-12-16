import asyncio
from typing import AsyncIterator


async def simple_async_generator(count: int) -> AsyncIterator[int]:
    for i in range(count):
        await asyncio.sleep(0.1)
        yield i


async def app():
    async for number in simple_async_generator(5):
        print(f"받은 숫자: f{number}")


asyncio.run(app())
