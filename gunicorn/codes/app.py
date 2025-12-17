# SessionContext 패턴ㅌ의 장점

# 기존 방식(상태값 직접 참조)

# 문제: 여러 곳에서 상태를 수정할 수 있음.

# 상태 동기화 보장: 상태 변경이 항상 새 객체 생성으로 표현된다
# 예측 가능성: 어떤 상태 변경이 발생했는지 명확히 추적 가능하다.
# 디버깅 용이: 각 상태 변경 시점의 컨텍스트를 보존

# 오디오 청크 큐 관리

# 비동기 큐

# asyncio.Queue 는 비동기 환경에서 스레드 안전한 큐를 제공합니다 오디오 청크를 큐에 넣고  STT 처리 태스크 큐에서 가져와 처리합니다.

# 큐 초기화(MessageHandler에서)

# self.audio_queue=asyncio.Queue()

# await self.audio_queue.put(bytes_data)

# chunk = await self.audio_queue.get()

# Queue 재사용 불가능

# Queue 재사용 불가능

# 중요: asyncio.Queue는 한번 종료되면 재사용할 수 없습니다 .재시작 시 반드시 새로운 Queue0를 생성하애햐합니다.

# 왜?? 그냥 이렇게 만들어서?

# 재사용 불가능한 이유?

# Queue에 None 종료 신호를 보내면 제너레이터가 조욜됨

# 종료된 Queue는 다시 사용할 수 없음

# 재시작 시 기존 Queue를 재사용하면 제너레이터가 종료 신호를 받지 못함.

# generator는 한번 소진되면 재사용 불가능하다


import asyncio
from typing import AsyncIterator


async def close_queue(self) -> None:
    if self.audio_queue:
        try:
            self.audio_queue.put_nowiat(None)
        except Exception:
            pass


## 제너레이터 종료 보장

### 제너레이터 None을 종료 신호로 받아 안전하게 종료됩니다.

### 종료 신호: None을 큐에 넣으면 제너레이터가종료됨

# 종료보장: 명시적으로 종료 처리

# 예외 처리: 옙외 발생시에도 break로 종료 보장

# 오치오 청크 처리 및 SessionContext 업데이트

# 오디오 청크가 수신되면 다음을 수행합니다.

# 파일 저장

# SessionContext 업데이터(불변 객체로 새로 생성)

# 큐에 추가 (STT 처리용)


async def handle_audio(
    self,
    bytes_data: bytes,
    context: SessionContext,
    audio_queue: asyncio.Queue[bytes],
    send_error_func: callable,
) -> SessionContext:
    """오디오 청크 처리 및 SessionContext 업데이트


    Args:
        bytes_data: 오디오 청크 데이터
        context: 세션 컨텍스트
        audio_qeuue: 오디오 큐
        send_error_func: 에러 전송 함수

    Returns:
        업데이트 된 SessionContext(새 객체)
    """

    if not bytes_data or len(bytes_data) == 0:
        return context
