"""
AsyncIterator 직접 구현 예제

이 예제는 AsyncIterator를 클래스로 직접 구현하는 방법을 보여줍니다.
"""

import asyncio
from collections.abc import AsyncIterator


class NumberAsyncIterator:
    """숫자를 비동기적으로 생성하는 AsyncIterator"""
    
    def __init__(self, start: int, end: int, delay: float = 0.1):
        """초기화
        
        Args:
            start: 시작 숫자
            end: 끝 숫자 (미포함)
            delay: 각 숫자 생성 간 지연 시간 (초)
        """
        self.start = start
        self.end = end
        self.delay = delay
        self.current = start
    
    def __aiter__(self) -> "NumberAsyncIterator":
        """비동기 이터레이터 반환
        
        Returns:
            자기 자신 (AsyncIterator)
        """
        return self
    
    async def __anext__(self) -> int:
        """다음 항목 반환
        
        Returns:
            다음 숫자
            
        Raises:
            StopAsyncIteration: 더 이상 항목이 없을 때
        """
        if self.current >= self.end:
            raise StopAsyncIteration
        
        # 비동기 작업 시뮬레이션
        await asyncio.sleep(self.delay)
        
        value = self.current
        self.current += 1
        return value


async def main():
    """메인 함수: AsyncIterator 사용"""
    print("=" * 50)
    print("AsyncIterator 직접 구현 예제")
    print("=" * 50)
    
    print("\n1. AsyncIterator 생성 및 사용:")
    async_iterator = NumberAsyncIterator(0, 5, delay=0.1)
    
    async for number in async_iterator:
        print(f"[메인] 받은 숫자: {number}")
    
    print("\n2. AsyncIterator 인터페이스:")
    print("   - __aiter__(): 비동기 이터레이터 반환")
    print("   - __anext__(): 다음 항목 반환 (비동기)")
    print("   - StopAsyncIteration: 더 이상 항목이 없을 때 발생")
    
    print("\n3. 비동기 제너레이터 vs AsyncIterator 클래스:")
    print("   - 비동기 제너레이터: 간단한 경우에 적합")
    print("   - AsyncIterator 클래스: 복잡한 상태 관리가 필요할 때 적합")


if __name__ == "__main__":
    asyncio.run(main())

