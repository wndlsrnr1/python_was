# 6장: Pipeline 패턴

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. Pipeline 패턴의 정의와 목적을 이해합니다
2. 여러 Channel을 연결하는 방법을 학습합니다
3. 비동기로 계속 제공하고 소모하는 구조를 이해합니다
4. asyncio.gather()를 통한 병렬 실행을 학습합니다
5. 실제 Pipeline 구현 예제를 실습합니다

---

## 6.1 Pipeline 패턴의 정의

### 정의

**Pipeline 패턴**은 **여러 Channel을 순차적으로 연결**하여 데이터를 처리하는 패턴입니다.

### 핵심 개념

- **단계별 처리**: 각 단계가 독립적인 Channel을 가짐
- **순차적 연결**: 이전 단계의 출력이 다음 단계의 입력
- **병렬 실행**: 모든 단계를 동시에 실행하여 효율성 향상

### Pipeline의 특징

- ✅ **여러 단계를 연결**
- ✅ **각 단계가 독립적**
- ✅ **병렬 실행으로 효율성 향상**
- ✅ **생명주기 관리**

---

## 6.2 기본 Pipeline 구현

### 기본 구조

```python
import asyncio
from collections.abc import AsyncIterator

class Pipeline:
    """기본 Pipeline 클래스"""
    
    def __init__(self) -> None:
        self.channels = {
            'input': Channel(),
            'process': Channel(),
            'output': Channel(),
        }
        self._running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        if self._running:
            return
        
        self._running = True
        
        # 모든 단계를 병렬로 실행
        await asyncio.gather(
            self._step1(),
            self._step2(),
            self._step3(),
        )
    
    async def _step1(self) -> None:
        """단계 1: 입력 → 처리"""
        async for data in self.channels['input'].receive():
            processed = await process_data(data)
            await self.channels['process'].send(processed)
        await self.channels['process'].close()
    
    async def _step2(self) -> None:
        """단계 2: 처리 → 출력"""
        async for data in self.channels['process'].receive():
            result = await format_data(data)
            await self.channels['output'].send(result)
        await self.channels['output'].close()
    
    async def _step3(self) -> None:
        """단계 3: 출력 소비"""
        async for result in self.channels['output'].receive():
            await save_result(result)
```

---

## 6.3 비동기로 계속 제공하고 소모하는 구조

### 핵심 개념

Pipeline은 **비동기로 계속 제공하고 소모하는 구조**입니다:

- **Producer**: 각 단계가 이전 단계의 데이터를 소비
- **Consumer**: 각 단계가 다음 단계에 데이터를 제공
- **병렬 실행**: 모든 단계가 동시에 실행

### 실제 예제

```python
class RealtimeSTTPipeline:
    """실시간 STT Pipeline"""
    
    def __init__(self) -> None:
        self.websocket_channel = WebSocketChannel()
        self.audio_channel = AudioChannel()
        self.grpc_channel = gRPCChannel()
        self.result_channel = ResultChannel()
        self._running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        if self._running:
            return
        
        self._running = True
        
        # 모든 단계를 병렬로 실행
        await asyncio.gather(
            self._websocket_to_audio(),    # 단계 1
            self._audio_to_grpc(),         # 단계 2
            self._grpc_to_result(),        # 단계 3
            self._result_to_websocket(),   # 단계 4
        )
    
    async def _websocket_to_audio(self) -> None:
        """WebSocket → Audio Channel"""
        async for message in self.websocket_channel.receive():
            if isinstance(message, bytes):
                await self.audio_channel.send(message)
        await self.audio_channel.close()
    
    async def _audio_to_grpc(self) -> None:
        """Audio → gRPC Channel"""
        async for pcm_chunk in self.audio_channel.receive():
            await self.grpc_channel.send(pcm_chunk)
        await self.grpc_channel.close()
    
    async def _grpc_to_result(self) -> None:
        """gRPC → Result Channel"""
        async for stt_result in self.grpc_channel.receive():
            await self.result_channel.send(stt_result)
        await self.result_channel.close()
    
    async def _result_to_websocket(self) -> None:
        """Result → WebSocket"""
        async for result in self.result_channel.receive():
            await self.websocket_channel.send(result)
        await self.websocket_channel.close()
```

### 데이터 흐름

```
WebSocket 수신
    ↓ (비동기로 계속 제공)
Audio Channel
    ↓ (비동기로 계속 제공)
gRPC Channel
    ↓ (비동기로 계속 제공)
Result Channel
    ↓ (비동기로 계속 제공)
WebSocket 전송
```

---

## 6.4 asyncio.gather()를 통한 병렬 실행

### 병렬 실행의 필요성

Pipeline의 각 단계는 **독립적으로 실행**되어야 합니다:

- **단계 1**: WebSocket에서 데이터 수신
- **단계 2**: 오디오 변환
- **단계 3**: gRPC 전송
- **단계 4**: 결과 전송

이 모든 단계를 **동시에 실행**해야 효율적입니다.

### asyncio.gather() 사용법

```python
async def start(self) -> None:
    """Pipeline 시작"""
    # 모든 단계를 병렬로 실행
    await asyncio.gather(
        self._step1(),
        self._step2(),
        self._step3(),
        self._step4(),
    )
```

### 실행 순서

```
시작
    ↓
모든 단계 동시 실행
    ├─→ 단계 1 (백그라운드)
    ├─→ 단계 2 (백그라운드)
    ├─→ 단계 3 (백그라운드)
    └─→ 단계 4 (백그라운드)
    ↓
모든 단계 완료 대기
    ↓
종료
```

---

## 6.5 실제 Pipeline 구현 예제

### 실시간 STT Pipeline

```python
class RealtimeSTTPipeline:
    """실시간 STT Pipeline"""
    
    def __init__(
        self,
        websocket,
        api_token: str,
        input_format: str = "webm",
        language_code: str = "ko-KR",
    ) -> None:
        self.websocket_channel = WebSocketChannel(websocket)
        self.audio_channel = AudioChannel(input_format=input_format)
        self.grpc_channel = gRPCChannel(
            api_token=api_token,
            language_code=language_code,
        )
        self.result_channel = ResultChannel()
        
        self._running = False
        self._tasks: list[asyncio.Task] = []
    
    async def start(self) -> None:
        """Pipeline 시작"""
        if self._running:
            return
        
        self._running = True
        
        # 모든 단계를 병렬로 실행
        self._tasks = [
            asyncio.create_task(self._websocket_to_audio()),
            asyncio.create_task(self._audio_to_grpc()),
            asyncio.create_task(self._grpc_to_result()),
            asyncio.create_task(self._result_to_websocket()),
        ]
        
        await asyncio.gather(*self._tasks)
    
    async def _websocket_to_audio(self) -> None:
        """WebSocket → Audio Channel"""
        try:
            async for message in self.websocket_channel.receive():
                if isinstance(message, bytes):
                    await self.audio_channel.send(message)
        finally:
            await self.audio_channel.close()
    
    async def _audio_to_grpc(self) -> None:
        """Audio → gRPC Channel"""
        try:
            async for pcm_chunk in self.audio_channel.receive():
                await self.grpc_channel.send(pcm_chunk)
        finally:
            await self.grpc_channel.close()
    
    async def _grpc_to_result(self) -> None:
        """gRPC → Result Channel"""
        try:
            async for stt_result in self.grpc_channel.receive():
                await self.result_channel.send(stt_result)
        finally:
            await self.result_channel.close()
    
    async def _result_to_websocket(self) -> None:
        """Result → WebSocket"""
        try:
            async for result in self.result_channel.receive():
                await self.websocket_channel.send(result)
        finally:
            await self.websocket_channel.close()
    
    async def close_all(self) -> None:
        """모든 Channel 종료"""
        await self.websocket_channel.close()
        await self.audio_channel.close()
        await self.grpc_channel.close()
        await self.result_channel.close()
```

---

## 6.6 Spring Pipeline과의 비교

### Spring Pipeline

Spring의 `Flux`를 사용한 Pipeline:

```java
// Spring Pipeline
public Flux<Result> processPipeline(Flux<Input> source) {
    return source
        .map(this::step1)      // 단계 1
        .map(this::step2)      // 단계 2
        .map(this::step3)      // 단계 3
        .doOnNext(this::save); // 단계 4
}
```

### Python Pipeline

Python의 Pipeline도 동일한 패턴:

```python
# Python Pipeline
class Pipeline:
    async def start(self) -> None:
        await asyncio.gather(
            self._step1(),  # 단계 1
            self._step2(),  # 단계 2
            self._step3(),  # 단계 3
            self._step4(),  # 단계 4
        )
```

### 공통점

- ✅ **여러 단계를 연결**
- ✅ **병렬 실행**
- ✅ **스트리밍 처리**

---

## 6.7 실습 예제

### 실습 1: 기본 Pipeline 구현

다음 코드를 따라쳐서 실행해보세요:

```python
import asyncio
from collections.abc import AsyncIterator

class SimpleChannel:
    """간단한 Channel"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, item: bytes) -> None:
        if not self._closed:
            await self._queue.put(item)
    
    async def close(self) -> None:
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

class SimplePipeline:
    """간단한 Pipeline"""
    
    def __init__(self) -> None:
        self.input_channel = SimpleChannel()
        self.process_channel = SimpleChannel()
        self.output_channel = SimpleChannel()
        self._running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        if self._running:
            return
        
        self._running = True
        
        # 모든 단계를 병렬로 실행
        await asyncio.gather(
            self._step1(),
            self._step2(),
            self._step3(),
        )
    
    async def _step1(self) -> None:
        """단계 1: 입력 → 처리"""
        async for data in self.input_channel.receive():
            processed = f"processed_{data.decode()}".encode()
            await self.process_channel.send(processed)
        await self.process_channel.close()
    
    async def _step2(self) -> None:
        """단계 2: 처리 → 출력"""
        async for data in self.process_channel.receive():
            result = f"result_{data.decode()}".encode()
            await self.output_channel.send(result)
        await self.output_channel.close()
    
    async def _step3(self) -> None:
        """단계 3: 출력 소비"""
        async for result in self.output_channel.receive():
            print(f"결과: {result.decode()}")

# 사용 예시
async def main():
    pipeline = SimplePipeline()
    
    # Producer: 입력 데이터 생성
    async def producer():
        for i in range(5):
            await pipeline.input_channel.send(f"data_{i}".encode())
            await asyncio.sleep(0.1)
        await pipeline.input_channel.close()
    
    # Pipeline과 Producer를 병렬로 실행
    await asyncio.gather(
        producer(),
        pipeline.start(),
    )

asyncio.run(main())
```

### 실습 2: 실시간 스트리밍 Pipeline

```python
class RealtimePipeline:
    """실시간 스트리밍 Pipeline"""
    
    def __init__(self) -> None:
        self.channels = {
            'input': SimpleChannel(),
            'transform': SimpleChannel(),
            'output': SimpleChannel(),
        }
        self._running = False
    
    async def start(self) -> None:
        """Pipeline 시작"""
        if self._running:
            return
        
        self._running = True
        
        await asyncio.gather(
            self._transform_step(),
            self._output_step(),
        )
    
    async def _transform_step(self) -> None:
        """변환 단계"""
        async for data in self.channels['input'].receive():
            transformed = f"transformed_{data.decode()}".encode()
            await self.channels['transform'].send(transformed)
        await self.channels['transform'].close()
    
    async def _output_step(self) -> None:
        """출력 단계"""
        async for data in self.channels['transform'].receive():
            print(f"출력: {data.decode()}")
    
    async def send(self, data: bytes) -> None:
        """입력 데이터 전송"""
        await self.channels['input'].send(data)
    
    async def close(self) -> None:
        """Pipeline 종료"""
        await self.channels['input'].close()

# 사용 예시
async def main():
    pipeline = RealtimePipeline()
    
    # Producer와 Pipeline을 병렬로 실행
    async def producer():
        for i in range(10):
            await pipeline.send(f"chunk_{i}".encode())
            await asyncio.sleep(0.1)
        await pipeline.close()
    
    await asyncio.gather(
        producer(),
        pipeline.start(),
    )

asyncio.run(main())
```

---

## 6.8 핵심 정리

### Pipeline 패턴의 특징

- ✅ **여러 단계를 연결**
- ✅ **각 단계가 독립적**
- ✅ **병렬 실행으로 효율성 향상**
- ✅ **비동기로 계속 제공하고 소모**

### 사용 시나리오

- ✅ **실시간 오디오 스트리밍**
- ✅ **다단계 데이터 처리**
- ✅ **파이프라인 처리**

### Spring과의 비교

- Spring의 `Flux`와 동일한 패턴
- 여러 단계를 연결하여 처리
- 병렬 실행으로 효율성 향상

---

## 다음 단계

다음 문서인 [07_naming_conventions.md](./07_naming_conventions.md)에서 네이밍 규칙과 용어 정리를 학습합니다.

