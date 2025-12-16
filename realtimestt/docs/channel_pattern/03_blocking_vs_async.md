# 3장: 블로킹과 비동기 실행 모델

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. 블로킹과 비동기 실행 모델의 차이를 이해합니다
2. 동기 스트리밍도 가능함을 이해합니다
3. 비동기 스트리밍이 흔한 이유를 이해합니다
4. 실제 코드 예제를 통해 차이를 확인합니다

---

## 3.1 블로킹 (Blocking) 실행 모델

### 정의

**블로킹**은 **호출자가 작업이 완료될 때까지 대기**하는 실행 모델입니다.

### 특징

- ✅ **호출자가 완료까지 대기**
- ✅ **다른 작업 불가능**
- ✅ **간단한 구현**
- ❌ **동시성 낮음**

### 실제 예제

```python
# 동기 함수: 블로킹
def convert_sync(audio_bytes: bytes) -> bytes:
    """
    오디오를 변환합니다.
    
    호출자는 변환이 완료될 때까지 여기서 대기합니다.
    """
    # 변환이 완료될 때까지 대기 (블로킹)
    result = do_conversion(audio_bytes)
    return result  # 완료 후 반환
```

### 사용 예시

```python
# 블로킹 방식
audio_bytes = read_file("input.webm")  # 파일 읽기 (블로킹)
pcm_data = convert_sync(audio_bytes)   # 변환 (블로킹)
save_file("output.pcm", pcm_data)      # 저장 (블로킹)

# 각 단계가 완료될 때까지 다음 단계로 진행하지 않음
```

---

## 3.2 비동기 (Async/Non-blocking) 실행 모델

### 정의

**비동기**는 **작업이 완료되기를 기다리는 동안 다른 작업을 수행**할 수 있는 실행 모델입니다.

### 특징

- ✅ **처리 중에도 다른 작업 가능**
- ✅ **동시성 향상**
- ✅ **효율적인 리소스 사용**
- ❌ **복잡한 구현**

### 실제 예제

```python
# 비동기 함수: 논블로킹
async def convert_async(audio_bytes: bytes) -> bytes:
    """
    오디오를 비동기로 변환합니다.
    
    변환 중에도 다른 작업을 수행할 수 있습니다.
    """
    # 변환 중에도 다른 작업 가능 (논블로킹)
    result = await do_conversion_async(audio_bytes)
    return result
```

### 사용 예시

```python
# 비동기 방식
async def process_multiple_files():
    tasks = []
    for filename in ["file1.webm", "file2.webm", "file3.webm"]:
        # 여러 파일을 동시에 처리
        task = asyncio.create_task(
            convert_file_async(filename)
        )
        tasks.append(task)
    
    # 모든 작업이 완료될 때까지 대기
    results = await asyncio.gather(*tasks)
    return results
```

---

## 3.3 동기 스트리밍도 가능합니다

### 중요한 개념

**스트리밍은 동기로도 구현 가능합니다.**

스트리밍의 핵심은 **"청크 단위로 데이터가 흘러간다"**는 것이지, **"비동기"**가 필수 조건은 아닙니다.

### 동기 스트리밍 예제

```python
# 동기 스트리밍 (블로킹 파이프라인)
def sync_streaming():
    """
    동기적으로 스트리밍 처리
    
    각 단계는 블로킹이지만, 데이터는 청크 단위로 흘러갑니다.
    """
    while True:
        chunk = read_chunk()        # 블로킹 (다음 청크까지 대기)
        if not chunk:
            break
        
        converted = convert(chunk)   # 블로킹 (변환 완료까지 대기)
        write_chunk(converted)      # 블로킹 (쓰기 완료까지 대기)
        
        # 데이터는 청크 단위로 흘러감 (스트리밍)
        # 하지만 각 단계는 블로킹 (동기)
```

### 비동기 스트리밍 예제

```python
# 비동기 스트리밍
async def async_streaming():
    """
    비동기적으로 스트리밍 처리
    
    각 단계는 논블로킹이며, 데이터는 청크 단위로 흘러갑니다.
    """
    async for chunk in read_chunks():
        converted = await convert_async(chunk)  # 논블로킹
        await write_chunk(converted)            # 논블로킹
        
        # 데이터는 청크 단위로 흘러감 (스트리밍)
        # 각 단계는 논블로킹 (비동기)
        # 동시에 다른 작업도 가능
```

### 비교표

| 항목 | 동기 스트리밍 | 비동기 스트리밍 |
|------|-------------|---------------|
| **처리 단위** | 청크 단위 | 청크 단위 |
| **데이터 흐름** | 스트리밍 | 스트리밍 |
| **실행 모델** | 블로킹 | 논블로킹 |
| **동시성** | 낮음 | 높음 |
| **구현 복잡도** | 낮음 | 높음 |

---

## 3.4 비동기 스트리밍이 흔한 이유

### 실시간 시스템의 요구사항

실시간 시스템에서는 다음과 같은 요구사항이 있습니다:

1. **입력 수신**: WebSocket에서 오디오 청크 수신
2. **변환 처리**: 오디오 형식 변환
3. **전송 처리**: gRPC로 STT 서버에 전송
4. **결과 수신**: STT 결과 수신
5. **응답 전송**: WebSocket으로 클라이언트에 응답

이 모든 작업을 **동시에** 수행해야 지연이 줄고 안정적입니다.

### 비동기 스트리밍의 장점

```python
# 비동기 스트리밍: 여러 작업을 동시에 수행
async def realtime_stt_pipeline():
    websocket_channel = WebSocketChannel(websocket)
    audio_channel = AudioChannel()
    grpc_channel = gRPCChannel()
    result_channel = ResultChannel()
    
    # 모든 단계를 동시에 실행
    await asyncio.gather(
        # 1. WebSocket 수신 (백그라운드)
        _websocket_to_audio(websocket_channel, audio_channel),
        
        # 2. 오디오 변환 (백그라운드)
        _audio_to_grpc(audio_channel, grpc_channel),
        
        # 3. gRPC 전송 (백그라운드)
        _grpc_to_result(grpc_channel, result_channel),
        
        # 4. 결과 전송 (백그라운드)
        _result_to_websocket(result_channel, websocket_channel),
    )
```

### 동기 스트리밍의 한계

```python
# 동기 스트리밍: 순차적으로만 처리
def sync_stt_pipeline():
    while True:
        # 1. WebSocket 수신 (블로킹)
        chunk = websocket.receive()
        
        # 2. 오디오 변환 (블로킹)
        converted = convert_audio(chunk)
        
        # 3. gRPC 전송 (블로킹)
        result = grpc.send(converted)
        
        # 4. 결과 전송 (블로킹)
        websocket.send(result)
        
        # 각 단계가 완료될 때까지 다음 단계로 진행하지 않음
        # 동시에 여러 작업을 수행할 수 없음
```

---

## 3.5 실행 모델과 처리 단위는 독립적

### 핵심 개념

**실행 모델(블로킹/비동기)과 처리 단위(배치/스트리밍)는 독립적입니다.**

### 조합 가능한 경우

| 처리 단위 | 실행 모델 | 예제 |
|----------|----------|------|
| **배치** | **블로킹** | `def convert(audio: bytes) -> bytes` |
| **배치** | **비동기** | `async def convert(audio: bytes) -> bytes` |
| **스트리밍** | **블로킹** | `def stream(): for chunk in chunks: ...` |
| **스트리밍** | **비동기** | `async def stream(): async for chunk in chunks: ...` |

### 실제 예제

#### 1. 배치 + 블로킹

```python
# 배치 변환 (전체 데이터) + 블로킹 (동기)
def convert_to_linear16(audio_bytes: bytes) -> bytes:
    """전체 데이터를 한 번에 변환 (블로킹)"""
    audio_segment = AudioSegment.from_file(...)
    return audio_segment.export(...)
```

#### 2. 배치 + 비동기

```python
# 배치 변환 (전체 데이터) + 비동기 (논블로킹)
async def convert_to_linear16(audio_bytes: bytes) -> bytes:
    """전체 데이터를 한 번에 변환 (비동기)"""
    audio_segment = await load_audio_async(...)
    return await export_audio_async(audio_segment)
```

#### 3. 스트리밍 + 블로킹

```python
# 스트리밍 변환 (청크 단위) + 블로킹 (동기)
def stream_convert(chunks: list[bytes]) -> list[bytes]:
    """청크 단위로 변환 (블로킹)"""
    results = []
    for chunk in chunks:
        converted = convert_chunk(chunk)  # 블로킹
        results.append(converted)
    return results
```

#### 4. 스트리밍 + 비동기

```python
# 스트리밍 변환 (청크 단위) + 비동기 (논블로킹)
async def stream_convert(chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
    """청크 단위로 변환 (비동기)"""
    async for chunk in chunks:
        converted = await convert_chunk_async(chunk)  # 논블로킹
        yield converted
```

---

## 3.6 실습 예제

### 실습 1: 블로킹 배치 변환

```python
import time

def convert_blocking(audio_bytes: bytes) -> bytes:
    """블로킹 배치 변환"""
    print("변환 시작...")
    time.sleep(2)  # 변환 시뮬레이션
    print("변환 완료")
    return b"converted_data"

# 사용
audio = b"input_data"
result = convert_blocking(audio)  # 2초 대기
print(f"결과: {result}")
```

### 실습 2: 비동기 배치 변환

```python
import asyncio

async def convert_async(audio_bytes: bytes) -> bytes:
    """비동기 배치 변환"""
    print("변환 시작...")
    await asyncio.sleep(2)  # 비동기 대기
    print("변환 완료")
    return b"converted_data"

# 사용
async def main():
    audio = b"input_data"
    result = await convert_async(audio)  # 다른 작업 가능
    print(f"결과: {result}")

asyncio.run(main())
```

### 실습 3: 동기 스트리밍

```python
def stream_sync(chunks: list[bytes]) -> list[bytes]:
    """동기 스트리밍"""
    results = []
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1} 처리 중...")
        time.sleep(0.5)  # 블로킹
        results.append(f"converted_{chunk}".encode())
    return results

# 사용
chunks = [b"chunk1", b"chunk2", b"chunk3"]
results = stream_sync(chunks)  # 순차 처리
for result in results:
    print(result)
```

### 실습 4: 비동기 스트리밍

```python
import asyncio
from collections.abc import AsyncIterator

async def stream_async(chunks: list[bytes]) -> AsyncIterator[bytes]:
    """비동기 스트리밍"""
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1} 처리 중...")
        await asyncio.sleep(0.5)  # 논블로킹
        yield f"converted_{chunk}".encode()

# 사용
async def main():
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    async for result in stream_async(chunks):
        print(result)  # 실시간 출력

asyncio.run(main())
```

### 실습 5: 비동기 스트리밍의 동시성

```python
import asyncio

async def process_chunk(chunk: bytes, chunk_id: int) -> bytes:
    """청크 처리 (비동기)"""
    print(f"청크 {chunk_id} 처리 시작")
    await asyncio.sleep(1)  # 처리 시뮬레이션
    print(f"청크 {chunk_id} 처리 완료")
    return f"processed_{chunk_id}".encode()

async def main():
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    
    # 여러 청크를 동시에 처리
    tasks = [
        process_chunk(chunk, i+1)
        for i, chunk in enumerate(chunks)
    ]
    
    results = await asyncio.gather(*tasks)
    for result in results:
        print(result)

asyncio.run(main())
```

---

## 3.7 핵심 정리

### 블로킹 vs 비동기

| 항목 | 블로킹 | 비동기 |
|------|--------|--------|
| **대기 방식** | 완료까지 대기 | 다른 작업 수행 |
| **동시성** | 낮음 | 높음 |
| **구현 복잡도** | 낮음 | 높음 |
| **사용 시나리오** | 단순 작업 | 실시간 시스템 |

### 실행 모델과 처리 단위는 독립적

- **배치 변환**은 블로킹/비동기 모두 가능
- **스트리밍 변환**은 블로킹/비동기 모두 가능
- **비동기 스트리밍**이 실시간 시스템에서 흔한 이유는 **동시성** 때문

### 선택 기준

1. **단순한 작업?** → 블로킹
2. **여러 작업을 동시에?** → 비동기
3. **전체 데이터가 필요?** → 배치
4. **실시간 처리가 필요?** → 스트리밍

---

## 다음 단계

다음 문서인 [04_adapter_pattern.md](./04_adapter_pattern.md)에서 Adapter 패턴의 구현과 사용법을 실습으로 학습합니다.

