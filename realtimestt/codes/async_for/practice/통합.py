import asyncio
from itertools import chain
from typing import AsyncIterator


class Channel:

    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._timeout = timeout

    async def send(self, item: str) -> None:
        await self._queue.put(item)

    async def close(self) -> None:
        await self._queue.put(None)

    def __aiter__(self) -> AsyncIterator[str]:
        return self._generate()

    async def _generate(self) -> AsyncIterator[str]:
        count = 0
        while True:
            item = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)

            if item is None:
                break

            count += 1
            yield item


async def producer(channel: Channel, items: list[str], delay: float = 0.2) -> None:
    for item in items:
        await asyncio.sleep(delay)
        await channel.send(item)

    await asyncio.sleep(0.1)
    await channel.close()


async def consumer(async_iterator: AsyncIterator[str]) -> None:
    async for item in async_iterator:
        print(f"{item}")


async def app() -> None:
    channel = Channel(timeout=1.0)
    data_items: list[str] = [f"데이터{i + 1}" for i in range(5)]
    await asyncio.gather(
        producer(channel=channel, data_items=data_items, delay=0.2), consumer(channel)
    )


asyncio.run(app())
