# 7장: 네이밍 규칙 및 용어 정리

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. 정확한 네이밍 규칙을 이해합니다
2. 배치 변환과 스트리밍 변환의 네이밍을 구분합니다
3. 오해하기 쉬운 용어를 정정합니다
4. 실제 프로젝트에 적용할 수 있습니다

---

## 7.1 추천 네이밍 규칙

### 배치 변환 (Batch Conversion)

배치 변환은 **전체 데이터를 한 번에 처리**하므로 다음과 같이 네이밍합니다:

#### FormatAdapter

```python
class AudioFormatAdapter:
    """오디오 형식 변환 Adapter"""
    
    async def convert(self, audio_bytes: bytes, input_format: str) -> bytes:
        """전체 데이터를 한 번에 변환"""
        ...
```

#### CodecAdapter

```python
class AudioCodecAdapter:
    """오디오 코덱 변환 Adapter"""
    
    async def convert(self, audio_bytes: bytes, input_codec: str) -> bytes:
        """전체 데이터를 한 번에 변환"""
        ...
```

#### BatchConverterAdapter

```python
class BatchAudioConverterAdapter:
    """배치 오디오 변환 Adapter"""
    
    async def convert_batch(self, audio_bytes: bytes) -> bytes:
        """배치 변환"""
        ...
```

### 스트리밍 변환 (Streaming Conversion)

스트리밍 변환은 **청크 단위로 실시간 처리**하므로 다음과 같이 네이밍합니다:

#### StreamingPipeline

```python
class AudioStreamingPipeline:
    """오디오 스트리밍 Pipeline"""
    
    async def process_stream(self, chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """청크 단위로 실시간 처리"""
        ...
```

#### ChannelPipeline

```python
class AudioChannelPipeline:
    """오디오 Channel Pipeline"""
    
    def __init__(self) -> None:
        self.input_channel = AudioChannel()
        self.output_channel = AudioChannel()
    
    async def start(self) -> None:
        """Pipeline 시작"""
        ...
```

#### StreamingChannel

```python
class AudioStreamingChannel:
    """오디오 스트리밍 Channel"""
    
    async def send(self, chunk: bytes) -> None:
        """청크 단위 전송"""
        ...
    
    async def receive(self) -> AsyncIterator[bytes]:
        """청크 단위 수신"""
        ...
```

---

## 7.2 용어 정리표

### 처리 단위

| 용어 | 의미 | 예제 |
|------|------|------|
| **배치 (Batch)** | 전체 데이터를 한 번에 처리 | `convert_to_linear16(audio_bytes: bytes) -> bytes` |
| **스트리밍 (Streaming)** | 청크 단위로 실시간 처리 | `async for chunk in channel.receive(): ...` |

### 실행 모델

| 용어 | 의미 | 예제 |
|------|------|------|
| **블로킹 (Blocking)** | 호출자가 완료까지 대기 | `def convert(audio: bytes) -> bytes` |
| **비동기 (Async)** | 처리 중에도 다른 작업 가능 | `async def convert(audio: bytes) -> bytes` |

### 구현 패턴

| 용어 | 의미 | 예제 |
|------|------|------|
| **Adapter** | 형식/인터페이스 변환 | `AudioFormatAdapter` |
| **Channel** | 스트리밍/파이프라인 | `AudioChannel` |
| **Pipeline** | 여러 Channel 연결 | `RealtimeSTTPipeline` |

---

## 7.3 오해하기 쉬운 용어 정정

### ❌ 잘못된 구분

| 구분 | 동기 | 비동기 |
|------|------|--------|
| **구현 패턴** | Adapter | Channel |

이 구분은 **잘못되었습니다**. 실행 모델과 구현 패턴은 **독립적**입니다.

### ✅ 올바른 구분

| 구분 | 배치 변환 | 스트리밍 변환 |
|------|----------|--------------|
| **처리 단위** | 전체 데이터 | 청크 단위 |
| **구현 패턴** | Adapter | Channel |
| **실행 모델** | 동기/비동기 모두 가능 | 동기/비동기 모두 가능 |

### 실제 예제

#### 1. 배치 + 블로킹

```python
# 배치 변환 (전체 데이터) + 블로킹 (동기)
def convert_to_linear16(audio_bytes: bytes) -> bytes:
    """전체 데이터를 한 번에 변환 (블로킹)"""
    ...
```

#### 2. 배치 + 비동기

```python
# 배치 변환 (전체 데이터) + 비동기 (논블로킹)
async def convert_to_linear16(audio_bytes: bytes) -> bytes:
    """전체 데이터를 한 번에 변환 (비동기)"""
    ...
```

#### 3. 스트리밍 + 블로킹

```python
# 스트리밍 변환 (청크 단위) + 블로킹 (동기)
def stream_convert(chunks: list[bytes]) -> list[bytes]:
    """청크 단위로 변환 (블로킹)"""
    ...
```

#### 4. 스트리밍 + 비동기

```python
# 스트리밍 변환 (청크 단위) + 비동기 (논블로킹)
async def stream_convert(chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    """청크 단위로 변환 (비동기)"""
    ...
```

---

## 7.4 실제 프로젝트 적용 예제

### 예제 1: 배치 변환 Adapter

```python
class AudioFormatAdapter:
    """오디오 형식 변환 Adapter (배치 변환)"""
    
    async def convert(
        self,
        audio_bytes: bytes,
        input_format: str,
    ) -> bytes:
        """
        전체 오디오를 한 번에 변환합니다.
        
        Args:
            audio_bytes: 전체 오디오 바이너리 데이터
            input_format: 입력 오디오 형식
        
        Returns:
            변환된 전체 오디오 바이너리 데이터
        """
        ...
```

### 예제 2: 스트리밍 변환 Channel

```python
class AudioChannel:
    """오디오 스트리밍 Channel (스트리밍 변환)"""
    
    async def send(self, chunk: bytes) -> None:
        """
        오디오 청크를 전송합니다.
        
        Args:
            chunk: 오디오 청크 바이너리 데이터
        """
        ...
    
    async def receive(self) -> AsyncIterator[bytes]:
        """
        오디오 청크를 실시간으로 수신합니다.
        
        Yields:
            bytes: 오디오 청크 바이너리 데이터
        """
        ...
```

### 예제 3: Pipeline

```python
class RealtimeSTTPipeline:
    """실시간 STT Pipeline (여러 Channel 연결)"""
    
    def __init__(self) -> None:
        self.websocket_channel = WebSocketChannel()
        self.audio_channel = AudioChannel()
        self.grpc_channel = gRPCChannel()
        self.result_channel = ResultChannel()
    
    async def start(self) -> None:
        """Pipeline 시작"""
        ...
```

---

## 7.5 네이밍 체크리스트

### ✅ 좋은 네이밍

- `AudioFormatAdapter`: 형식 변환 Adapter (배치)
- `AudioChannel`: 스트리밍 Channel
- `RealtimeSTTPipeline`: 실시간 STT Pipeline
- `BatchAudioConverterAdapter`: 배치 변환 Adapter
- `StreamingAudioPipeline`: 스트리밍 Pipeline

### ❌ 나쁜 네이밍

- `SyncAdapter`: 동기/비동기와 무관
- `AsyncChannel`: 비동기가 본질이 아님
- `AudioConverter`: 배치/스트리밍 구분 불명확
- `AudioStream`: Channel과 구분 불명확

---

## 7.6 핵심 정리

### 네이밍 규칙

1. **배치 변환**: `*Adapter`, `*BatchConverter`
2. **스트리밍 변환**: `*Channel`, `*StreamingPipeline`
3. **Pipeline**: `*Pipeline`

### 용어 정리

- **배치 vs 스트리밍**: 처리 단위의 차이
- **블로킹 vs 비동기**: 실행 모델의 차이
- **Adapter vs Channel**: 구현 패턴의 차이

### 오해 방지

- ❌ "동기=Adapter / 비동기=Channel"은 잘못된 구분
- ✅ "배치=Adapter / 스트리밍=Channel"이 올바른 구분

---

## 다음 단계

다음 문서인 [08_practical_example.md](./08_practical_example.md)에서 실제 프로젝트에서 사용하는 전체 예제를 학습합니다.

