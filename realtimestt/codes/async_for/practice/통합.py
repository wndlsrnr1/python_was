import asyncio
import queue
from typing import AsyncIterator


async def generate_from_queue(
    queue: asyncio.Queue[str], timeout: float = 1.0
) -> AsyncIterator[str]:
    count = 0
    while True:
        item = await asyncio.wait_for(queue.get(), timeout=timeout)
        if item is None:
            break
        count += 1
        yield item


async def consumer(async_iterator: AsyncIterator[str]):
    async for item in async_iterator:
        print(f"{item}")


async def provider(queue: asyncio.Queue[str]):
    for item in range("5"):
        await asyncio.sleep(delay=1)
        await queue.put()

    await queue.put(None)


async def background():
    async for i in range(100):
        print(i)
        asyncio.sleep(0.1)


async def app():
    queue: asyncio.Queue[str] = asyncio.Queue()
    async_iterator: AsyncIterator[str] = generate_from_queue(queue=queue, timeout=1.0)
    await asyncio.gather(producer(queue))
