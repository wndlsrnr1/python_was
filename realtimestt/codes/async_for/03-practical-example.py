"""
실용적인 예제: Queue 기반 비동기 제너레이터

이 예제는 실시간 STT 시스템에서 사용되는 Queue 기반 비동기 제너레이터 패턴을 구현합니다.
AudioHandler.generate_chunks() 패턴을 기반으로 작성되었습니다.
"""

import asyncio
from collections.abc import AsyncIterator


async def generate_from_queue(
    queue: asyncio.Queue[str],
    timeout: float = 1.0,
) -> AsyncIterator[str]:
    """Queue에서 데이터를 가져와 비동기적으로 생성하는 제너레이터

    실시간 STT 시스템의 AudioHandler.generate_chunks() 패턴을 기반으로 합니다.

    Args:
        queue: 데이터를 담는 비동기 큐
        timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초)

    Yields:
        큐에서 가져온 데이터

    예시:
        >>> queue = asyncio.Queue()
        >>> await queue.put("데이터1")
        >>> await queue.put("데이터2")
        >>> await queue.put(None)  # 종료 신호
        >>> async for item in generate_from_queue(queue):
        ...     print(item)
    """
    count = 0

    while True:
        try:
            # 큐에서 데이터 가져오기 (타임아웃 설정)
            item = await asyncio.wait_for(
                queue.get(),
                timeout=timeout,
            )

            # None이면 종료 신호 (제너레이터 종료 보장)
            if item is None:
                print(f"[제너레이터] 종료 신호 수신, 총 {count}개 처리")
                break

            count += 1
            print(f"[제너레이터] 데이터 생성: {item} (총 {count}개)")
            yield item

        except asyncio.TimeoutError:
            # 타임아웃 시 계속 대기 (실제로는 로깅 등 추가 처리 가능)
            print(f"[제너레이터] 타임아웃, 계속 대기...")
            continue
        except Exception as e:
            print(f"[제너레이터] 오류 발생: {e}")
            break


async def producer(queue: asyncio.Queue[str], items: list[str], delay: float = 0.2):
    """큐에 데이터를 추가하는 프로듀서

    Args:
        queue: 데이터를 추가할 큐
        items: 추가할 데이터 리스트
        delay: 각 데이터 추가 간 지연 시간 (초)
    """
    print(f"[프로듀서] 시작: {len(items)}개 데이터 추가 예정")

    for item in items:
        await asyncio.sleep(delay)
        await queue.put(item)
        print(f"[프로듀서] 큐에 추가: {item}")

    # 종료 신호 전송
    await asyncio.sleep(0.1)
    await queue.put(None)
    print("[프로듀서] 종료 신호 전송")


async def consumer(async_iterator: AsyncIterator[str]):
    """비동기 이터레이터에서 데이터를 소비하는 컨슈머

    Args:
        async_iterator: 데이터를 가져올 비동기 이터레이터
    """
    print("[컨슈머] 시작")

    async for item in async_iterator:
        print(f"[컨슈머] 처리 중: {item}")
        # 실제 처리 로직 (예: STT 전송, 파일 저장 등)
        await asyncio.sleep(0.1)

    print("[컨슈머] 완료")


async def main():
    """메인 함수: Queue 기반 비동기 제너레이터 패턴 시연"""
    print("=" * 50)
    print("실용적인 예제: Queue 기반 비동기 제너레이터")
    print("=" * 50)

    # 큐 생성
    queue: asyncio.Queue[str] = asyncio.Queue()

    # 데이터 준비
    data_items = [f"데이터{i+1}" for i in range(5)]

    # 비동기 제너레이터 생성
    async_iterator = generate_from_queue(queue, timeout=1.0)

    # 프로듀서와 컨슈머를 동시에 실행
    print("\n[시스템] 프로듀서와 컨슈머 동시 실행")
    await asyncio.gather(
        producer(queue, data_items, delay=0.2),
        consumer(async_iterator),
    )

    print("\n" + "=" * 50)
    print("패턴 설명:")
    print("=" * 50)
    print("1. Queue 기반 비동기 제너레이터:")
    print("   - 프로듀서가 큐에 데이터 추가")
    print("   - 제너레이터가 큐에서 데이터를 가져와 yield")
    print("   - 컨슈머가 async for로 데이터 처리")
    print()
    print("2. 종료 신호 처리:")
    print("   - None을 큐에 넣어 종료 신호 전송")
    print("   - 제너레이터가 None을 받으면 break로 종료")
    print()
    print("3. 실시간 STT 시스템 적용:")
    print("   - WebSocket에서 오디오 청크 수신 → Queue 추가")
    print("   - AudioHandler.generate_chunks() → Queue에서 가져와 yield")
    print("   - STT 처리 → async for로 청크 처리")


if __name__ == "__main__":
    asyncio.run(main())
