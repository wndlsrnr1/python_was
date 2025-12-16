import asyncio
import queue
from typing import AsyncIterator


async def generate_from_queue(
    queue: asyncio.Queue[str], timeout: float = 1.0
) -> AsyncIterator[str]:
    """Queue에서 데이터를 가져와 비동기적으로 생성하는 제너레터
    Args:
        queue: 데이터 담는 비동기 큐
        timeout: 큐에서 데이터를 가져올때 타임아웃

    Yields:
        queue에서 가져온 데이터
    """
    count = 0

    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=timeout)

            # None이면 종료 신호 (제너레이터 종료 보장)
            if item is None:
                print(f"[제너레이터] 종료 신호 수신, 총 {count}개 처리")
                break

            count += 1
            yield item
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            break


async def producer(queue: asyncio.Queue[str], items: list[str], delay: float = 0.2):
    """큐에 데이터를 추가하는 프로듀서

    Args:
        queue: 데이터를 추가할 큐
        items: 추가할 데이터 리스트
        delay: 각 데이터 추가 간 지연 시간 (초)

    """

    for item in items:
        await asyncio.sleep(delay)
        await queue.put(item)

    await asyncio.sleep(0.1)
    await queue.put(None)


async def consumer(async_iterator: AsyncIterator[str]):
    async for item in async_iterator:
        print(f"{item}")
        # await asyncio.sleep(0.1)


async def app():
    queue: asyncio.Queue[str] = asyncio.Queue()
    data_items: list[str] = [f"데이터{i+1}" for i in range(5)]

    async_iterator: AsyncIterator[str] = generate_from_queue(queue, timeout=1.0)

    await asyncio.gather(
        producer(queue, data_items, delay=0.2), consumer(async_iterator)
    )


asyncio.run(app())
