"""
async for를 왜 사용하는가? - 비교 예제

이 예제는 동기 for와 async for의 차이를 실제로 보여줍니다.
async for의 필요성과 장점을 명확히 이해할 수 있습니다.
"""

import asyncio
import time
from collections.abc import AsyncIterator


async def fetch_data(item: int, delay: float = 0.5) -> str:
    """네트워크 요청 시뮬레이션 (I/O 대기)
    
    실제로는 HTTP 요청, 데이터베이스 쿼리, 파일 읽기 등의 I/O 작업을 시뮬레이션합니다.
    
    Args:
        item: 데이터 항목 번호
        delay: 대기 시간 (초)
        
    Returns:
        가져온 데이터 문자열
    """
    await asyncio.sleep(delay)  # 네트워크 대기 시뮬레이션
    return f"데이터{item}"


async def async_generator() -> AsyncIterator[str]:
    """비동기 제너레이터: 각 항목을 가져올 때 I/O 대기
    
    실제로는 Queue에서 데이터를 가져오거나, 네트워크 스트림을 읽는 등의
    비동기 작업을 수행하는 제너레이터입니다.
    
    Yields:
        비동기적으로 가져온 데이터
    """
    for i in range(5):
        data = await fetch_data(i, delay=0.5)  # I/O 대기 (각 항목마다 0.5초)
        yield data


async def background_task():
    """백그라운드 작업: async for 사용 시 동시에 실행됨
    
    실제로는 로깅, 모니터링, 다른 데이터 처리 등의 작업을 의미합니다.
    """
    for i in range(10):
        await asyncio.sleep(0.1)
        print(f"[백그라운드] 작업 {i+1}/10")


async def demonstrate_sync_problem():
    """동기 for의 문제점 시연
    
    동기 for는 await를 사용할 수 없으므로 비동기 제너레이터를 직접 사용할 수 없습니다.
    """
    print("=" * 60)
    print("❌ 동기 for의 문제점")
    print("=" * 60)
    
    print("\n1. 동기 for에서 비동기 제너레이터 사용 시도:")
    print("   코드: for item in async_generator():")
    print("   결과: TypeError 발생!")
    print("   이유: async_generator()는 awaitable 객체를 반환하므로")
    print("         동기 for로는 직접 사용할 수 없음")
    
    print("\n2. 해결 방법 (비효율적):")
    print("   gen = async_generator()")
    print("   item = await gen.__anext__()  # 수동으로 await 필요")
    print("   → 코드가 복잡해지고, 동시성 이점을 잃음")


async def demonstrate_async_for_benefit():
    """async for의 장점 시연
    
    async for는 I/O 대기 중에도 다른 코루틴을 실행할 수 있습니다.
    """
    print("\n" + "=" * 60)
    print("✅ async for의 장점: 동시 처리")
    print("=" * 60)
    
    start = time.time()
    
    # 백그라운드 작업과 동시에 실행
    bg_task = asyncio.create_task(background_task())
    
    results = []
    # async for는 I/O 대기 중에도 다른 코루틴 실행 가능
    async for item in async_generator():
        results.append(item)
        print(f"[메인] 받음: {item}")
    
    await bg_task  # 백그라운드 작업 완료 대기
    
    elapsed = time.time() - start
    print(f"\n총 소요 시간: {elapsed:.2f}초")
    print("→ I/O 대기 중에도 백그라운드 작업이 동시에 처리됨!")
    print(f"→ 순차 처리였다면: {5 * 0.5 + 10 * 0.1:.2f}초 이상 소요")


async def demonstrate_sequential_processing():
    """순차 처리 시뮬레이션 (async for 없이)
    
    async for를 사용하지 않고 순차적으로 처리하면
    백그라운드 작업을 동시에 실행할 수 없습니다.
    """
    print("\n" + "=" * 60)
    print("❌ 순차 처리 (async for 없이)")
    print("=" * 60)
    
    start = time.time()
    
    # 순차적으로 처리 (백그라운드 작업 없이)
    results = []
    gen = async_generator()
    
    try:
        while True:
            item = await gen.__anext__()  # 수동으로 await
            results.append(item)
            print(f"[순차] 받음: {item}")
    except StopAsyncIteration:
        pass
    
    elapsed = time.time() - start
    print(f"\n총 소요 시간: {elapsed:.2f}초")
    print("→ 각 항목을 기다리는 동안 다른 작업 불가능")
    print("→ 백그라운드 작업을 추가하면 더 오래 걸림")


async def main():
    """메인: async for의 필요성과 장점 시연"""
    print("=" * 60)
    print("async for를 왜 사용하는가?")
    print("=" * 60)
    
    # 1. 동기 for의 문제점 설명
    await demonstrate_sync_problem()
    
    # 2. 순차 처리 시뮬레이션
    await demonstrate_sequential_processing()
    
    # 3. async for의 장점 시연
    await demonstrate_async_for_benefit()
    
    # 4. 핵심 차이점 정리
    print("\n" + "=" * 60)
    print("핵심 차이점 정리")
    print("=" * 60)
    print("\n1. 동기 for:")
    print("   ❌ await를 사용할 수 없음")
    print("   ❌ 비동기 제너레이터를 직접 사용 불가")
    print("   ❌ 각 항목을 기다리는 동안 블로킹됨")
    print("   ❌ 다른 작업을 동시에 처리할 수 없음")
    
    print("\n2. async for:")
    print("   ✅ await를 내부적으로 처리")
    print("   ✅ 비동기 제너레이터를 직접 사용 가능")
    print("   ✅ I/O 대기 중에도 다른 코루틴 실행 가능")
    print("   ✅ 실시간 스트리밍, Queue 처리에 필수!")
    
    print("\n3. 실시간 STT 시스템에서의 활용:")
    print("   - WebSocket에서 오디오 청크 수신 (I/O 대기)")
    print("   - Queue에서 데이터 가져오기 (I/O 대기)")
    print("   - STT 결과 처리 중에도 다른 작업 가능")
    print("   → async for 없이는 실시간 처리가 불가능!")


if __name__ == "__main__":
    asyncio.run(main())

