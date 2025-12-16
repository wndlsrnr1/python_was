"""
기본 async for 사용법 예제

이 예제는 간단한 비동기 제너레이터를 만들고 async for로 순회하는 방법을 보여줍니다.
"""

import asyncio
from collections.abc import AsyncIterator


async def simple_async_generator(count: int) -> AsyncIterator[int]:
    """간단한 비동기 제너레이터

    Args:
        count: 생성할 숫자의 개수

    Yields:
        0부터 count-1까지의 숫자
    """
    print(f"[제너레이터] 시작: {count}개 숫자 생성")

    for i in range(count):
        # 비동기 작업 시뮬레이션 (I/O 대기)
        await asyncio.sleep(0.1)
        print(f"[제너레이터] 생성: {i}")
        yield i

    print(f"[제너레이터] 완료")


async def main():
    """메인 함수: async for로 비동기 제너레이터 순회"""
    print("=" * 50)
    print("기본 async for 예제")
    print("=" * 50)

    print("\n1. async for로 순회:")
    async for number in simple_async_generator(5):
        print(f"[메인] 받은 숫자: {number}")

    print("\n2. 동기 for와의 차이:")
    print("   - 동기 for: 각 항목을 가져오는 동안 블로킹됨")
    print("   - async for: 각 항목을 가져오는 동안 다른 코루틴 실행 가능")

    print("\n3. 비동기 제너레이터의 장점:")
    print("   - I/O 대기 중에도 다른 작업 처리 가능")
    print("   - 메모리 효율적 (한 번에 하나씩 생성)")
    print("   - 실시간 스트리밍에 적합")


if __name__ == "__main__":
    asyncio.run(main())
