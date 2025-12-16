import asyncio
from typing import AsyncIterator


class Channel:
    """queue를 내부에 캡슐화하고 send 메서드로 데이터를 넣을 수 있는 Channel"""

    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[str | None] = asyncio.Queue()
        self._timeout = timeout

    async def send(self, item: str) -> None:
        """데이터를 채널에 보냄"""
        await self._queue.put(item)

    async def close(self) -> None:
        """종료 신호 전송"""
        await self._queue.put(None)

    def __aiter__(self) -> AsyncIterator[str]:
        return self._generate()

    async def _generate(self) -> AsyncIterator[str]:
        """내부 generator"""
        count = 0

        while True:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)

                if item is None:
                    print(f"[제너레이터] 종료 신호 수신, 총 {count}개 처리")
                    break

                count += 1
                yield item
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break


async def producer(channel: Channel, items: list[str], delay: float = 0.2) -> None:
    """채널에 데이터를 보내는 프로듀서

    Args:
        channel: 데이터를 보낼 채널
        items: 추가할 데이터 리스트
        delay: 각 데이터 추가 간 지연 시간 (초)
    """
    for item in items:
        await asyncio.sleep(delay)
        await channel.send(item)

    await asyncio.sleep(0.1)
    await channel.close()


async def consumer(async_iterator: AsyncIterator[str]) -> None:
    """이터레이터에서 데이터를 소비"""
    async for item in async_iterator:
        print(f"{item}")


async def app() -> None:
    channel = Channel(timeout=1.0)
    data_items: list[str] = [f"데이터{i+1}" for i in range(5)]

    await asyncio.gather(
        producer(channel, data_items, delay=0.2),
        consumer(channel),
    )


asyncio.run(app())
