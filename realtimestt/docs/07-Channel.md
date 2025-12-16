# Channel 패턴

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. Channel 패턴의 본질과 핵심 원칙을 이해합니다
2. Queue 기반 비동기 Producer-Consumer 패턴을 구현할 수 있습니다
3. 여러 Channel을 통합 관리하는 Pipeline 패턴을 적용할 수 있습니다
4. WebSocket, Django Channels 등 실제 기술들이 Channel 패턴의 구현임을 이해합니다
5. 실시간 STT 시스템에 Channel 패턴을 적용하는 방법을 학습합니다

## Channel 패턴이란?

### 정의

**Channel 패턴**은 비동기 스트리밍 데이터를 처리하기 위한 설계 패턴입니다. 내부적으로 queue를 사용하여 Producer와 Consumer를 분리하고, `async for`를 통해 데이터를 소비할 수 있도록 합니다.

### 핵심 원칙

Channel 패턴은 다음 원칙을 따릅니다:

1. **Queue 기반 비동기 통신**: 내부적으로 `asyncio.Queue`를 사용하여 데이터를 버퍼링
2. **Producer-Consumer 분리**: 데이터를 보내는 Producer와 받는 Consumer를 독립적으로 동작
3. **Iterator 인터페이스**: `__aiter__()`를 구현하여 `async for`로 데이터 소비 가능
4. **명시적 종료 신호**: `None`을 통해 채널 종료를 명시적으로 처리
5. **생명주기 관리**: `close()` 메서드로 채널의 생명주기를 제어

### 일반화된 원칙

**중요**: 하나의 queue를 사용하여 비동기로 push/consume하는 구조는 모두 Channel 패턴입니다.

```python
# 모든 비동기 스트리밍 구조

# 1. WebSocket
websocket.send() → queue → async for message in websocket

# 2. gRPC Stream
grpc_stream.send() → queue → async for item in grpc_stream

# 3. FFmpeg Stream  
ffmpeg_output → queue → async for chunk in stream

# 4. File Reading
file.read() → queue → async for line in file

# 5. Database Cursor
cursor.fetch() → queue → async for row in cursor
```

따라서:
- **WebSocket** → Channel
- **gRPC Stream** → Channel  
- **FFmpeg** → Channel
- **Django Channels** → Channel Layer
- **asyncio.Queue** → Channel 구현체

**결론**: 비동기 producer-consumer 구조는 모두 Channel 패턴의 변형입니다.

## 기본 Channel 구현

### Channel 클래스

기본 Channel 클래스는 queue를 내부에 캡슐화하고, `send()`와 `__aiter__()` 메서드를 제공합니다:

```python
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
```

### 주요 메서드

#### `__init__(timeout: float = 1.0)`

- 내부 `asyncio.Queue` 초기화
- `timeout`: queue에서 데이터를 가져올 때의 타임아웃 (초)

#### `async def send(item: str) -> None`

- Producer가 채널에 데이터를 보낼 때 사용
- 내부적으로 `queue.put()`을 호출

#### `async def close() -> None`

- 채널 종료 신호 전송
- `None`을 queue에 넣어 종료 신호 전달

#### `__aiter__() -> AsyncIterator[str]`

- `async for`를 사용할 수 있도록 iterator 인터페이스 제공
- 내부 `_generate()` 메서드를 반환

#### `async def _generate() -> AsyncIterator[str]`

- 실제 데이터 생성 로직
- queue에서 데이터를 가져와 yield
- `None`을 받으면 종료
- 타임아웃 시 계속 대기

### Producer-Consumer 패턴

Channel을 사용한 기본 Producer-Consumer 패턴:

```python
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
```

### 실행 결과

```
데이터1
데이터2
데이터3
데이터4
데이터5
[제너레이터] 종료 신호 수신, 총 5개 처리
```

### 종료 신호 처리

Channel은 `None`을 종료 신호로 사용합니다:

1. Producer가 모든 데이터 전송 완료 후 `channel.close()` 호출
2. `close()`는 내부적으로 `None`을 queue에 넣음
3. Consumer가 `None`을 받으면 `async for` 루프 종료

이 방식으로 명시적이고 안전한 종료가 보장됩니다.

## Pipeline 패턴 (Composite Channel)

### 개념

실제 시스템에서는 여러 단계를 거쳐 데이터를 처리해야 합니다. 각 단계별로 Channel을 분리하고, 상위 Pipeline이 이를 통합 관리하는 패턴입니다.

예시: **Socket → FFmpeg 변환 → gRPC 전송**

### StreamPipeline 구현

```python
class StreamPipeline:
    """여러 Channel을 통합 관리하는 Pipeline"""
    
    def __init__(self) -> None:
        # 각 단계별 Channel
        self.socket_channel = Channel()
        self.ffmpeg_channel = Channel()
        self.grpc_channel = Channel()
        
        # Pipeline 전체 생명주기 관리
        self._is_running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        self._is_running = True
        # 모든 Channel을 병렬로 실행
        await asyncio.gather(
            self._socket_to_ffmpeg(),
            self._ffmpeg_to_grpc(),
            self._consume_grpc(),
        )
    
    async def _socket_to_ffmpeg(self) -> None:
        """Socket → FFmpeg 파이프라인"""
        async for data in self.socket_channel:
            # FFmpeg 변환 로직
            converted = f"[FFmpeg 변환] {data}"
            await self.ffmpeg_channel.send(converted)
        await self.ffmpeg_channel.close()
    
    async def _ffmpeg_to_grpc(self) -> None:
        """FFmpeg → gRPC 파이프라인"""
        async for data in self.ffmpeg_channel:
            # gRPC 전송 준비
            ready = f"[gRPC 준비] {data}"
            await self.grpc_channel.send(ready)
        await self.grpc_channel.close()
    
    async def _consume_grpc(self) -> None:
        """gRPC 소비"""
        async for data in self.grpc_channel:
            print(f"[gRPC 전송] {data}")
    
    async def close_all(self) -> None:
        """모든 Channel 종료"""
        await self.socket_channel.close()


# 사용 예시
async def socket_reader(pipeline: StreamPipeline) -> None:
    """Socket에서 데이터 읽기"""
    items = [f"데이터{i+1}" for i in range(5)]
    for item in items:
        await asyncio.sleep(0.2)
        await pipeline.socket_channel.send(item)
    await pipeline.socket_channel.close()


async def app() -> None:
    pipeline = StreamPipeline()
    
    # Socket Reader와 Pipeline을 병렬 실행
    await asyncio.gather(
        socket_reader(pipeline),
        pipeline.start(),
    )


asyncio.run(app())
```

### 단순화된 버전

더 간단한 구현도 가능합니다:

```python
class StreamPipeline:
    """단순화된 Pipeline"""
    
    def __init__(self) -> None:
        self.channels = {
            'socket': Channel(),
            'ffmpeg': Channel(),
            'grpc': Channel(),
        }
    
    async def close_all(self) -> None:
        """모든 Channel 한 번에 종료"""
        await asyncio.gather(*[ch.close() for ch in self.channels.values()])
```

### 장점

1. **관심사 분리**: 각 Channel이 독립적으로 관리됨
2. **재사용성**: 각 Channel을 다른 파이프라인에서도 사용 가능
3. **테스트 용이성**: 각 단계를 독립적으로 테스트 가능
4. **생명주기 관리**: `StreamPipeline`이 전체를 제어

### 실시간 STT 시스템 적용 예시

실시간 STT 시스템에서:

```python
class RealtimeSTTPipeline:
    """실시간 STT 파이프라인"""
    
    def __init__(self) -> None:
        self.websocket_channel = Channel()      # WebSocket 수신
        self.audio_channel = Channel()          # 오디오 데이터
        self.ffmpeg_channel = Channel()         # FFmpeg 변환
        self.grpc_channel = Channel()           # gRPC STT 전송
        self.result_channel = Channel()         # STT 결과
    
    async def start(self) -> None:
        """전체 파이프라인 시작"""
        await asyncio.gather(
            self._websocket_to_audio(),
            self._audio_to_ffmpeg(),
            self._ffmpeg_to_grpc(),
            self._grpc_to_result(),
        )
```

이렇게 각 단계가 독립적인 Channel을 가지면서도, 전체 파이프라인은 하나의 생명주기를 공유합니다.

## WebSocket과 Django Channels

### WebSocket = Channel 패턴

WebSocket 자체가 Channel 패턴의 구현입니다. WebSocket을 Channel로 추상화하면:

```python
from typing import AsyncIterator

class WebSocketChannel:
    """WebSocket을 Channel 패턴으로 추상화"""
    
    def __init__(self, websocket) -> None:
        self._websocket = websocket
    
    async def send(self, data: str) -> None:
        """클라이언트로 데이터 전송"""
        await self._websocket.send(data)
    
    async def receive(self) -> str:
        """클라이언트로부터 데이터 수신"""
        return await self._websocket.receive()
    
    def __aiter__(self) -> AsyncIterator[str]:
        """async for로 메시지 수신"""
        return self._receive_loop()
    
    async def _receive_loop(self) -> AsyncIterator[str]:
        while True:
            try:
                data = await self.receive()
                yield data
            except WebSocketDisconnect:
                break
    
    async def close(self) -> None:
        """WebSocket 종료"""
        await self._websocket.close()
```

### Django Channels = Channel 패턴

**Django Channels**의 "Channel" 이름은 Channel 패턴에서 유래했습니다.

#### Django Channels의 구조

Django Channels는 내부적으로:
- 각 WebSocket 연결을 **Channel Layer**(Redis/RabbitMQ 등)로 관리
- 메시지를 **queue**에 넣고 비동기로 처리
- Producer-Consumer 패턴 구현

#### Consumer 예제

```python
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """연결 수락"""
        await self.accept()
    
    async def receive(self, text_data: str) -> None:
        """메시지 수신 (Channel에 데이터를 받음 - queue.put과 유사)"""
        await self.send(text_data=text_data)  # Channel로 데이터 전송
    
    async def disconnect(self, close_code: int) -> None:
        """연결 종료 (Channel 종료)"""
        pass
```

#### Channel Layer

Django Channels는 분산 환경에서도 동작하도록 Channel Layer를 사용합니다:

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

Channel Layer는 여러 워커 프로세스 간에 메시지를 공유할 수 있게 해줍니다. 이는 본질적으로 분산된 Channel 패턴입니다.

### ASGI와의 관계

**ASGI**(Asynchronous Server Gateway Interface)는 WebSocket과 같은 비동기 스트리밍을 지원합니다:

```python
async def asgi_app(scope, receive, send):
    """ASGI 애플리케이션"""
    if scope['type'] == 'websocket':
        await send({'type': 'websocket.accept'})
        
        while True:
            message = await receive()  # Channel로부터 수신
            if message['type'] == 'websocket.receive':
                await send({  # Channel로 전송
                    'type': 'websocket.send',
                    'text': message['text']
                })
```

ASGI의 `receive`와 `send`는 본질적으로 Channel의 `receive`와 `send`와 동일한 패턴입니다.

### 통합 관점

모든 비동기 스트리밍은 동일한 패턴을 따릅니다:

```python
# 공통 패턴
class StreamChannel:
    async def send(self, data): ...  # Producer
    def __aiter__(self): ...          # Consumer (async for)
    async def close(self): ...        # 종료
```

실제 기술들의 매핑:

| 기술 | Channel 패턴 관점 |
|------|------------------|
| WebSocket | Channel (양방향 통신) |
| gRPC Stream | Channel (단방향/양방향 스트림) |
| FFmpeg | Channel (프로세스 출력 스트림) |
| Django Channels | Channel Layer (분산 Channel) |
| asyncio.Queue | Channel 구현체 |
| Database Cursor | Channel (쿼리 결과 스트림) |

### 실전 적용 예시

실시간 STT 시스템에서는:

```python
# WebSocket 수신 → Channel → FFmpeg → Channel → gRPC
class RealtimeSTTService:
    def __init__(self, websocket):
        self.websocket_channel = WebSocketChannel(websocket)
        self.audio_channel = Channel()
        self.grpc_channel = Channel()
    
    async def process(self):
        await asyncio.gather(
            self._websocket_to_audio(),  # WebSocket → Audio Channel
            self._audio_to_ffmpeg(),     # Audio → FFmpeg
            self._ffmpeg_to_grpc(),      # FFmpeg → gRPC Channel
        )
```

이렇게 WebSocket도 Channel 패턴으로 일관되게 처리할 수 있습니다.

## 요약 및 핵심 정리

### Channel 패턴의 핵심

1. **Queue 기반 비동기 통신**: 내부적으로 `asyncio.Queue`를 사용하여 Producer와 Consumer 분리
2. **Iterator 인터페이스**: `__aiter__()`를 통해 `async for`로 데이터 소비
3. **명시적 종료**: `None`을 통해 안전한 종료 처리
4. **일반화된 원칙**: 모든 비동기 스트리밍은 Channel 패턴의 변형

### 실시간 STT 시스템 적용

실시간 STT 시스템에서 Channel 패턴은 다음과 같이 적용됩니다:

#### 전체 파이프라인

```
WebSocket 수신 
  → Audio Channel 
  → FFmpeg 변환 
  → Converted Audio Channel 
  → gRPC STT 전송 
  → STT Result Channel 
  → WebSocket 응답
```

#### 구현 예시

```python
class RealtimeSTTPipeline:
    """실시간 STT 전체 파이프라인"""
    
    def __init__(self, websocket) -> None:
        # 각 단계별 Channel
        self.websocket_channel = WebSocketChannel(websocket)
        self.audio_channel = Channel[bytes]()
        self.ffmpeg_channel = Channel[bytes]()
        self.grpc_channel = Channel[bytes]()
        self.result_channel = Channel[str]()
    
    async def start(self) -> None:
        """전체 파이프라인 시작"""
        await asyncio.gather(
            self._websocket_to_audio(),
            self._audio_to_ffmpeg(),
            self._ffmpeg_to_grpc(),
            self._grpc_to_result(),
            self._result_to_websocket(),
        )
    
    async def _websocket_to_audio(self) -> None:
        """WebSocket → Audio Channel"""
        async for message in self.websocket_channel:
            audio_data = self._parse_audio(message)
            await self.audio_channel.send(audio_data)
        await self.audio_channel.close()
    
    async def _audio_to_ffmpeg(self) -> None:
        """Audio → FFmpeg 변환"""
        async for audio in self.audio_channel:
            converted = await self._convert_with_ffmpeg(audio)
            await self.ffmpeg_channel.send(converted)
        await self.ffmpeg_channel.close()
    
    async def _ffmpeg_to_grpc(self) -> None:
        """FFmpeg → gRPC 전송"""
        async for audio in self.ffmpeg_channel:
            await self.grpc_channel.send(audio)
        await self.grpc_channel.close()
    
    async def _grpc_to_result(self) -> None:
        """gRPC STT 결과 수신"""
        async for audio in self.grpc_channel:
            result = await self._stt_request(audio)
            await self.result_channel.send(result)
        await self.result_channel.close()
    
    async def _result_to_websocket(self) -> None:
        """STT 결과 → WebSocket 응답"""
        async for result in self.result_channel:
            await self.websocket_channel.send(result)
```

### Channel 패턴의 장점

1. **관심사 분리**: 각 단계가 독립적인 Channel을 가져 명확한 책임 분리
2. **재사용성**: 각 Channel을 다른 파이프라인에서도 재사용 가능
3. **테스트 용이성**: 각 단계를 독립적으로 테스트 가능
4. **생명주기 관리**: Pipeline이 전체 생명주기를 제어
5. **확장성**: 새로운 단계를 쉽게 추가 가능
6. **일관성**: 모든 비동기 스트리밍을 동일한 패턴으로 처리

### 언제 Channel 패턴을 사용할까?

Channel 패턴은 다음 상황에서 특히 유용합니다:

- ✅ **스트리밍 데이터 처리**: WebSocket, gRPC Stream, 파일 읽기 등
- ✅ **다단계 파이프라인**: 여러 단계를 거쳐 데이터를 변환하는 경우
- ✅ **Producer-Consumer 패턴**: 비동기로 데이터를 생성하고 소비하는 경우
- ✅ **생명주기 관리**: 연결, 변환, 전송 등이 같은 생명주기를 공유하는 경우

### 주의사항

1. **메모리 관리**: Channel이 버퍼링하므로 메모리 사용량을 주의
2. **타임아웃 설정**: 무한 대기를 방지하기 위해 적절한 타임아웃 설정
3. **에러 처리**: 각 단계에서 에러 발생 시 적절한 처리 필요
4. **종료 신호**: 반드시 `close()`를 호출하여 안전한 종료 보장

## 관련 코드 파일

### 예제 코드

- `realtimestt/codes/async_for/practice/04-practice.py`: 기본 Channel 구현
- `realtimestt/codes/async_for/04-channel.py`: Channel 클래스 예제
- `realtimestt/codes/async_for/03-practical-example.py`: Queue 기반 비동기 제너레이터

### 관련 문서

- `realtimestt/docs/channel_pattern.md`: Channel 패턴 대화 내용
- `realtimestt/codes/async_for/README.md`: async for 패턴 설명

### 실전 적용

실시간 STT 시스템의 각 구성 요소도 Channel 패턴으로 이해할 수 있습니다:

- **WebSocket 연결** (`01-웹소켓-연결-및-인증.md`): WebSocket Channel
- **오디오 스트림 수신** (`02-오디오-스트림-수신-및-저장.md`): Audio Channel
- **오디오 형식 변환** (`03-오디오-형식-변환.md`): FFmpeg Channel
- **gRPC 스트리밍 STT** (`04-gRPC-스트리밍-STT.md`): gRPC Channel
- **STT 결과 처리** (`05-STT-결과-처리-및-전송.md`): Result Channel

## 추가 학습 자료

1. **Python asyncio 공식 문서**: `asyncio.Queue` 사용법
2. **Django Channels 문서**: Channel Layer와 Consumer 패턴
3. **ASGI 스펙**: 비동기 서버 게이트웨이 인터페이스
4. **Go Channels**: Channel 패턴의 원조인 Go 언어의 Channel

## 결론

Channel 패턴은 비동기 스트리밍 데이터를 처리하는 강력하고 일관된 방법입니다. 실시간 STT 시스템뿐만 아니라 모든 비동기 스트리밍 애플리케이션에서 적용할 수 있는 범용적인 패턴입니다.

핵심은 **queue를 사용한 비동기 producer-consumer 구조**를 **추상화**하여 **일관된 인터페이스**로 제공하는 것입니다. 이를 통해 복잡한 파이프라인도 명확하고 관리하기 쉬운 코드로 구현할 수 있습니다.

