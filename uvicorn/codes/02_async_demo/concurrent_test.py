import asyncio
import aiohttp
import time

async def fetch(session, url):
    """비동기 HTTP 요청"""
    async with session.get(url) as response:
        return await response.json()

async def main():
    """동시 요청 테스트"""
    url = "http://127.0.0.1:8000/async"
    
    print("10개 동시 요청 시작...")
    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for _ in range(10)]
        results = await asyncio.gather(*tasks)
    end = time.time()
    
    print(f"10개 요청 처리 시간: {end - start:.2f}초")
    print(f"첫 번째 결과: {results[0]}")
    print(f"마지막 결과: {results[-1]}")

if __name__ == "__main__":
    asyncio.run(main())

