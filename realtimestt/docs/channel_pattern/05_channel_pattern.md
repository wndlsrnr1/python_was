# 5장: Channel 패턴 상세

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. Channel 패턴의 정의와 목적을 이해합니다
2. CSP/Producer-Consumer 개념을 이해합니다
3. 스트리밍 Channel을 구현할 수 있습니다
4. send/receive 메서드 패턴을 이해합니다
5. 실제 사용 시나리오를 이해합니다

---

## 5.1 Channel 패턴의 정의

### 정의

**Channel 패턴**은 **스트리밍/파이프라인**을 구현하는 패턴입니다.

핵심은 **"데이터를 흘려보내는 통로(파이프)"**입니다.

### CSP (Communicating Sequential Processes)

Channel 패턴은 **CSP** 개념에서 유래했습니다:

- **Producer**: 데이터를 생성하여 Channel에 전송
- **Channel**: 데이터를 버퍼링하는 통로
- **Consumer**: Channel에서 데이터를 소비

### Channel의 특징

- ✅ **스트리밍/파이프라인**이 핵심
- ✅ **청크 단위로 데이터 처리**
- ✅ **Producer-Consumer 분리**
- ✅ **동기/비동기 모두 가능**

---

## 5.2 기본 Channel 구현

### 기본 구조

```python
import asyncio
from collections.abc import AsyncIterator

class Channel:
    """기본 Channel 클래스"""
    
    def __init__(self, timeout: float = 1.0) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._timeout = timeout
        self._closed = False
    
    async def send(self, item: bytes) -> None:
        """데이터를 Channel에 전송 (Producer)"""
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")
        await self._queue.put(item)
    
    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """데이터를 Channel에서 수신 (Consumer)"""
        async for item in self:
            yield item
    
    def __aiter__(self) -> AsyncIterator[bytes]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()
    
    async def _generate(self) -> AsyncIterator[bytes]:
        """내부 generator"""
        while True:
            try:
                item = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._timeout,
                )
                
                if item is None:  # 종료 신호
                    break
                
                yield item
            except asyncio.TimeoutError:
                continue
```

### 주요 메서드

#### `__init__(timeout: float = 1.0)`

- 내부 `asyncio.Queue` 초기화
- `timeout`: queue에서 데이터를 가져올 때의 타임아웃 (초)

#### `async def send(item: bytes) -> None`

- Producer가 Channel에 데이터를 보낼 때 사용
- 내부적으로 `queue.put()`을 호출

#### `async def close() -> None`

- Channel 종료 신호 전송
- `None`을 queue에 넣어 종료 신호 전달

#### `async def receive() -> AsyncIterator[bytes]`

- Consumer가 Channel에서 데이터를 받을 때 사용
- `async for`로 사용 가능

#### `__aiter__() -> AsyncIterator[bytes]`

- `async for`를 사용할 수 있도록 iterator 인터페이스 제공
- 내부 `_generate()` 메서드를 반환

---

## 5.3 Producer-Consumer 패턴

### 기본 사용법

```python
async def producer(channel: Channel, items: list[bytes]) -> None:
    """Producer: 데이터를 Channel에 전송"""
    for item in items:
        await channel.send(item)
        await asyncio.sleep(0.1)  # 시뮬레이션
    
    await channel.close()  # 종료 신호

async def consumer(channel: Channel) -> None:
    """Consumer: Channel에서 데이터를 수신"""
    async for item in channel.receive():
        print(f"수신: {item}")

# 사용
async def main():
    channel = Channel()
    items = [b"chunk1", b"chunk2", b"chunk3"]
    
    await asyncio.gather(
        producer(channel, items),
        consumer(channel),
    )

asyncio.run(main())
```

### 실행 결과

```
수신: b'chunk1'
수신: b'chunk2'
수신: b'chunk3'
```

---

## 5.4 스트리밍 Channel 구현

### AudioChannel 예제

```python
import asyncio
from collections.abc import AsyncIterator
from subprocess import Popen, PIPE

class AudioChannel:
    """
    스트리밍 오디오 변환 Channel
    
    WebM 청크를 입력받아 PCM 청크를 실시간으로 출력합니다.
    """
    
    def __init__(self, input_format: str = "webm", timeout: float = 1.0) -> None:
        self.input_format = input_format
        self._timeout = timeout
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, chunk: bytes) -> None:
        """WebM 청크를 내부 큐에 추가"""
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")
        
        await self._queue.put(chunk)
    
    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """PCM 청크를 실시간으로 yield"""
        async for item in self:
            yield item
    
    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._generate()
    
    async def _generate(self) -> AsyncIterator[bytes]:
        """내부 generator: ffmpeg를 사용한 스트리밍 변환"""
        # ffmpeg 프로세스 시작
        process = Popen(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-f", "s16le",
                "-ar", "16000",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "pipe:1",
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        
        try:
            # 백그라운드 태스크: 큐에서 WebM 청크를 읽어 ffmpeg에 전송
            async def write_chunks() -> None:
                try:
                    while True:
                        chunk = await asyncio.wait_for(
                            self._queue.get(),
                            timeout=self._timeout,
                        )
                        
                        if chunk is None:  # 종료 신호
                            break
                        
                        process.stdin.write(chunk)
                        process.stdin.flush()
                finally:
                    process.stdin.close()
            
            # 백그라운드 태스크 시작
            write_task = asyncio.create_task(write_chunks())
            
            # stdout에서 PCM 청크 읽기
            while True:
                pcm_chunk = process.stdout.read(8192)  # 8KB 청크
                if not pcm_chunk:
                    break
                
                yield pcm_chunk  # 실시간으로 yield
            
            # write_task 완료 대기
            await write_task
            
        finally:
            process.terminate()
            process.wait()
```

### 사용 예시

```python
async def handle_realtime_stream(websocket):
    """실시간 오디오 스트리밍 처리"""
    audio_channel = AudioChannel(input_format="webm")
    
    # 병렬 실행
    await asyncio.gather(
        # Producer: WebSocket에서 청크 수신
        async def producer():
            async for message in websocket:
                if isinstance(message, bytes):
                    await audio_channel.send(message)
            await audio_channel.close()
        
        # Consumer: 변환된 PCM 청크 처리
        async def consumer():
            async for pcm_chunk in audio_channel.receive():
                await process_pcm_chunk(pcm_chunk)
    )
```

---

## 5.5 send/receive 메서드 패턴

### 패턴 구조

```python
class Channel:
    async def send(self, data: T) -> None:
        """Producer: 데이터 전송"""
        ...
    
    async def receive(self) -> AsyncIterator[T]:
        """Consumer: 데이터 수신"""
        async for item in self:
            yield item
```

### 타입 안전성

```python
from typing import TypeVar, Generic
from collections.abc import AsyncIterator

T = TypeVar('T')

class Channel(Generic[T]):
    """타입 안전한 Channel"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[T | None] = asyncio.Queue()
    
    async def send(self, item: T) -> None:
        """타입 안전한 전송"""
        await self._queue.put(item)
    
    async def receive(self) -> AsyncIterator[T]:
        """타입 안전한 수신"""
        async for item in self:
            yield item
```

### 사용 예시

```python
# 타입 안전한 Channel 사용
bytes_channel: Channel[bytes] = Channel()
str_channel: Channel[str] = Channel()

# 타입 체크 통과
await bytes_channel.send(b"data")
await str_channel.send("text")

# 타입 체크 실패 (컴파일 에러)
# await bytes_channel.send("text")  # 에러!
```

---

## 5.6 Spring Stream과의 비교

### Spring Stream

Spring의 `Flux`는 Channel 패턴의 구현입니다:

```java
// Spring Stream (Channel 패턴)
public Flux<PCM> convertStream(Flux<WebM> source) {
    return source
        .map(this::convertToPCM)  // 청크 단위 변환
        .doOnNext(this::process);  // 실시간 처리
}
```

### Python Channel

Python의 Channel도 동일한 패턴:

```python
# Python Channel
class AudioChannel:
    async def receive(self) -> AsyncIterator[bytes]:
        async for chunk in self:
            converted = convert_to_pcm(chunk)
            yield converted  # 실시간 yield
```

### 공통점

- ✅ **스트리밍 처리**가 핵심
- ✅ **청크 단위 처리**
- ✅ **Producer-Consumer 분리**

---

## 5.7 실습 예제

### 실습 1: 기본 Channel 구현

다음 코드를 따라쳐서 실행해보세요:

```python
import asyncio
from collections.abc import AsyncIterator

class SimpleChannel:
    """간단한 Channel 구현"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, item: bytes) -> None:
        """데이터 전송"""
        if not self._closed:
            await self._queue.put(item)
    
    async def close(self) -> None:
        """종료 신호"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """데이터 수신"""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

# 사용 예시
async def main():
    channel = SimpleChannel()
    
    # Producer
    async def producer():
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        for chunk in chunks:
            await channel.send(chunk)
            await asyncio.sleep(0.1)
        await channel.close()
    
    # Consumer
    async def consumer():
        async for chunk in channel.receive():
            print(f"수신: {chunk}")
    
    # 병렬 실행
    await asyncio.gather(producer(), consumer())

asyncio.run(main())
```

### 실습 2: 타입 안전한 Channel

```python
from typing import TypeVar, Generic
from collections.abc import AsyncIterator

T = TypeVar('T')

class TypedChannel(Generic[T]):
    """타입 안전한 Channel"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[T | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, item: T) -> None:
        """타입 안전한 전송"""
        if not self._closed:
            await self._queue.put(item)
    
    async def close(self) -> None:
        """종료 신호"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[T]:
        """타입 안전한 수신"""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

# 사용 예시
async def main():
    # 타입 안전한 Channel
    bytes_channel: TypedChannel[bytes] = TypedChannel()
    str_channel: TypedChannel[str] = TypedChannel()
    
    # 타입 체크 통과
    await bytes_channel.send(b"data")
    await str_channel.send("text")
    
    # Consumer
    async def bytes_consumer():
        async for chunk in bytes_channel.receive():
            print(f"Bytes: {chunk}")
    
    async def str_consumer():
        async for chunk in str_channel.receive():
            print(f"String: {chunk}")
    
    # 종료
    await bytes_channel.close()
    await str_channel.close()
    
    await asyncio.gather(bytes_consumer(), str_consumer())

asyncio.run(main())
```

### 실습 3: 실시간 스트리밍 Channel

```python
class RealtimeChannel:
    """실시간 스트리밍 Channel"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, chunk: bytes) -> None:
        """청크 전송"""
        if not self._closed:
            await self._queue.put(chunk)
    
    async def close(self) -> None:
        """종료"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """청크 수신"""
        while True:
            chunk = await self._queue.get()
            if chunk is None:
                break
            yield chunk

# 사용 예시
async def main():
    channel = RealtimeChannel()
    
    # Producer: 실시간 데이터 생성
    async def producer():
        for i in range(10):
            chunk = f"chunk_{i}".encode()
            await channel.send(chunk)
            await asyncio.sleep(0.1)  # 실시간 시뮬레이션
        await channel.close()
    
    # Consumer: 실시간 데이터 처리
    async def consumer():
        async for chunk in channel.receive():
            print(f"처리: {chunk}")
            await asyncio.sleep(0.05)  # 처리 시뮬레이션
    
    # 병렬 실행
    await asyncio.gather(producer(), consumer())

asyncio.run(main())
```

---

## 5.8 실제 사용 시나리오

### 시나리오 1: 실시간 오디오 스트리밍

```python
async def handle_realtime_audio(websocket):
    """실시간 오디오 스트리밍 처리"""
    audio_channel = AudioChannel(input_format="webm")
    
    # Producer: WebSocket에서 오디오 청크 수신
    async def producer():
        async for message in websocket:
            if isinstance(message, bytes):
                await audio_channel.send(message)
        await audio_channel.close()
    
    # Consumer: 변환된 PCM 청크 처리
    async def consumer():
        async for pcm_chunk in audio_channel.receive():
            await send_to_grpc(pcm_chunk)
    
    # 병렬 실행
    await asyncio.gather(producer(), consumer())
```

### 시나리오 2: 파이프라인 처리

```python
async def process_pipeline():
    """여러 Channel을 연결한 파이프라인"""
    input_channel = Channel()
    process_channel = Channel()
    output_channel = Channel()
    
    # 단계 1: 입력 → 처리
    async def step1():
        async for data in input_channel.receive():
            processed = await process_data(data)
            await process_channel.send(processed)
        await process_channel.close()
    
    # 단계 2: 처리 → 출력
    async def step2():
        async for data in process_channel.receive():
            result = await format_data(data)
            await output_channel.send(result)
        await output_channel.close()
    
    # 단계 3: 출력 소비
    async def step3():
        async for result in output_channel.receive():
            await save_result(result)
    
    # 모든 단계 병렬 실행
    await asyncio.gather(step1(), step2(), step3())
```

---

## 5.9 핵심 정리

### Channel 패턴의 특징

- ✅ **스트리밍/파이프라인**이 핵심
- ✅ **청크 단위 처리**
- ✅ **Producer-Consumer 분리**
- ✅ **동기/비동기 모두 가능**

### 사용 시나리오

- ✅ **실시간 오디오 스트리밍**
- ✅ **파이프라인 처리**
- ✅ **큰 파일 처리**

### Spring과의 비교

- Spring의 `Flux`와 동일한 패턴
- 스트리밍 처리가 핵심 목적
- 청크 단위 처리에 적합

---

## 다음 단계

다음 문서인 [06_pipeline_pattern.md](./06_pipeline_pattern.md)에서 여러 Channel을 연결하는 Pipeline 패턴을 학습합니다.

