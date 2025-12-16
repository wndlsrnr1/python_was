import asyncio
from collections.abc import AsyncIterator
from time import sleep
import time
from tkinter import YES
from unittest import result


async def fetch_data(item: int, delay: float = 0.5) -> str:
    await asyncio.sleep(delay)
    return item


async def async_generator() -> AsyncIterator[str]:
    for i in range(5):
        data = await fetch_data(i, delay=0.5)
        yield data


async def background_task():
    for i in range(10):
        await asyncio.sleep(0.1)


async def demonstrate_async_for_benefic():
    start = time.time()
    bg_task = asyncio.create_task(background_task())

    results = []

    async for item in async_generator():
        results.append(item)

    await bg_task
    elapsed = time.time() - start
    print(f"{elapsed}")


async def demonstrate_sequential_processing():
    start = time.time()
    results = []
    gen = async_generator()

    try:
        while True:
            item = await gen.__anext__()
            results.append(item)
    except StopAsyncIteration:
        pass

    elapsed = time.time() - start
    print(f"{elapsed} sequential")


async def app():
    await demonstrate_sequential_processing()
    await demonstrate_async_for_benefic()


asyncio.run(app())
