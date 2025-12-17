# 1장: 개요 및 핵심 개념

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. Adapter 패턴의 본질을 이해합니다
2. Channel 패턴의 본질을 이해합니다
3. "동기=Adapter / 비동기=Channel"이라는 오해를 해소합니다
4. 배치 변환과 스트리밍 변환을 구분합니다
5. 블로킹과 비동기 실행 모델을 구분합니다

---

## 1.1 Adapter 패턴의 본질

### 정의

**Adapter 패턴(GoF)**은 **인터페이스나 형식(Format)을 변환**하는 패턴입니다.

핵심은 **"변환"**이며, **동기/비동기와는 무관**합니다.

### Adapter의 역할

Adapter는 다음과 같은 변환을 수행합니다:

- **형식 변환**: `webm(bytes) → pcm(bytes)`
- **인터페이스 변환**: 외부 라이브러리 인터페이스를 우리 코드에 맞춤
- **코덱 변환**: 오디오/비디오 코덱 변환

### 실제 예제

```python
# Adapter: 전체 파일을 한 번에 변환
async def convert_to_linear16(
    audio_bytes: bytes,  # 전체 데이터
    input_format: str,
) -> bytes:  # 전체 결과
    """오디오를 LINEAR16 PCM 형식으로 변환"""
    # 전체 파일을 메모리에 로드
    audio_segment = AudioSegment.from_file(...)
    # 변환 후 전체 결과 반환
    return output_bytes
```

이 함수는 `async def`로 작성되었지만, **전체 데이터를 한 번에 처리**하므로 **배치 변환**입니다.

### Adapter의 특징

- ✅ **형식/인터페이스 변환**이 핵심
- ✅ **동기 함수로도 구현 가능**
- ✅ **비동기 함수로도 구현 가능**
- ❌ **"동기"가 본질이 아님**

---

## 1.2 Channel 패턴의 본질

### 정의

**Channel 패턴**은 **스트리밍/파이프라인**을 구현하는 패턴입니다.

핵심은 **"데이터를 흘려보내는 통로(파이프)"**이며, **동기/비동기와는 무관**합니다.

### Channel의 역할

Channel은 다음과 같은 역할을 수행합니다:

- **스트리밍**: 청크 단위로 데이터를 흘려보냄
- **파이프라인 연결**: 여러 단계를 연결하여 데이터 처리
- **Producer-Consumer 분리**: 데이터 생성과 소비를 분리

### 실제 예제

```python
# Channel: 청크 단위로 실시간 변환
class AudioChannel:
    async def send(self, chunk: bytes) -> None:
        """청크 단위 입력"""
        await self._queue.put(chunk)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """청크 단위 출력"""
        async for pcm_chunk in self:
            yield pcm_chunk  # 실시간으로 yield
```

이 Channel은 `async`를 사용하지만, 핵심은 **청크 단위로 실시간 처리**하는 것입니다.

### Channel의 특징

- ✅ **스트리밍/파이프라인**이 핵심
- ✅ **동기적으로도 구현 가능** (버퍼 0, send가 receive를 기다림)
- ✅ **비동기적으로도 구현 가능** (버퍼/큐/백그라운드 워커)
- ❌ **"비동기"가 본질이 아님**

---

## 1.3 왜 "동기=Adapter / 비동기=Channel"이 잘못되었나?

### 오해의 원인

실제 프로젝트에서:
- Adapter는 보통 **동기 함수**로 구현됨
- Channel은 보통 **비동기 함수**로 구현됨

하지만 이것은 **우연의 일치**일 뿐, **본질이 아닙니다**.

### 정확한 구분

| 구분 | Adapter | Channel |
|------|---------|---------|
| **본질** | 형식/인터페이스 변환 | 스트리밍/파이프라인 |
| **처리 단위** | 전체 데이터 | 청크 단위 |
| **실행 모델** | 동기/비동기 모두 가능 | 동기/비동기 모두 가능 |

### 올바른 이해

```python
# Adapter를 비동기로 구현 가능
async def convert_to_linear16(...) -> bytes:
    # 비동기이지만 전체 데이터를 한 번에 처리 (배치)
    ...

# Channel을 동기로 구현 가능
class SyncChannel:
    def send(self, chunk: bytes) -> None:
        # 동기이지만 청크 단위로 처리 (스트리밍)
        ...
```

---

## 1.4 배치 변환 vs 스트리밍 변환

### 배치 변환 (Batch Conversion)

**전체 입력 → 전체 출력**

```python
# 전체 파일을 한 번에 변환
audio_file = await upload_file()  # 전체 파일
pcm_data = await convert_to_linear16(
    audio_file.read(),  # 전체 데이터
    "webm"
)
# 전체 변환 완료 후 사용
```

**특징:**
- 전체 데이터를 메모리에 로드
- 변환 완료 후 결과 반환
- 메모리 사용량이 큼
- 파일 업로드 후 변환에 적합

### 스트리밍 변환 (Streaming Conversion)

**청크 입력 → 청크 출력**

```python
# 청크 단위로 실시간 변환
async for webm_chunk in websocket_channel.receive():
    await audio_channel.send(webm_chunk)  # 청크 단위

async for pcm_chunk in audio_channel.receive():
    await grpc_channel.send(pcm_chunk)  # 실시간 처리
```

**특징:**
- 청크 단위로 처리
- 실시간으로 결과 출력
- 메모리 사용량이 적음
- 실시간 스트리밍에 적합

### 비교표

| 항목 | 배치 변환 | 스트리밍 변환 |
|------|----------|--------------|
| **처리 단위** | 전체 데이터 | 청크 단위 |
| **메모리 사용** | 높음 (전체 로드) | 낮음 (청크 단위) |
| **응답 시간** | 전체 완료 후 | 실시간 |
| **사용 시나리오** | 파일 업로드 후 변환 | 실시간 오디오 스트리밍 |
| **구현 패턴** | Adapter | Channel |

---

## 1.5 블로킹 vs 비동기 실행 모델

### 블로킹 (Blocking)

**호출자가 완료까지 대기**

```python
# 동기 함수: 호출자가 완료까지 기다림
def convert_sync(audio_bytes: bytes) -> bytes:
    # 변환이 완료될 때까지 여기서 대기
    result = do_conversion(audio_bytes)
    return result  # 완료 후 반환
```

**특징:**
- 호출자가 완료까지 대기
- 다른 작업 불가능
- 간단한 구현

### 비동기 (Async/Non-blocking)

**처리 중에도 다른 작업 가능**

```python
# 비동기 함수: 처리 중에도 다른 작업 가능
async def convert_async(audio_bytes: bytes) -> bytes:
    # 변환 중에도 다른 작업 가능
    result = await do_conversion_async(audio_bytes)
    return result
```

**특징:**
- 처리 중에도 다른 작업 가능
- 동시성 향상
- 복잡한 구현

### 중요한 구분

**스트리밍은 동기로도 가능합니다:**

```python
# 동기 스트리밍 (블로킹 파이프라인)
def sync_streaming():
    while True:
        chunk = read_chunk()      # 블로킹
        converted = convert(chunk)  # 블로킹
        write_chunk(converted)      # 블로킹
        # 데이터는 청크 단위로 흘러감 (스트리밍)
```

**비동기 스트리밍:**

```python
# 비동기 스트리밍
async def async_streaming():
    async for chunk in read_chunks():
        converted = await convert_async(chunk)
        await write_chunk(converted)
        # 데이터는 청크 단위로 흘러감 (스트리밍)
        # 동시에 다른 작업도 가능 (비동기)
```

---

## 1.6 Spring/Tomcat과의 비교

### Spring Converter vs Adapter

Spring의 `Converter`는 Adapter 패턴의 구현입니다:

```java
// Spring Converter (Adapter 패턴)
@Component
public class AudioConverter implements Converter<WebM, PCM> {
    @Override
    public PCM convert(WebM source) {
        // 전체 데이터를 한 번에 변환
        return convertToPCM(source);
    }
}
```

Python의 Adapter도 동일한 패턴:

```python
# Python Adapter
async def convert_to_linear16(audio_bytes: bytes) -> bytes:
    # 전체 데이터를 한 번에 변환
    return convert_to_pcm(audio_bytes)
```

### Spring Stream vs Channel

Spring의 `Stream`은 Channel 패턴의 구현입니다:

```java
// Spring Stream (Channel 패턴)
public Flux<PCM> convertStream(Flux<WebM> source) {
    return source
        .map(this::convertToPCM)  // 청크 단위 변환
        .doOnNext(this::process); // 실시간 처리
}
```

Python의 Channel도 동일한 패턴:

```python
# Python Channel
async def receive(self) -> AsyncIterator[bytes]:
    async for chunk in self:
        converted = convert_to_pcm(chunk)
        yield converted  # 실시간 yield
```

---

## 1.7 핵심 정리

### 올바른 구분

| 구분 | 배치 변환 | 스트리밍 변환 |
|------|----------|--------------|
| **처리 단위** | 전체 데이터 | 청크 단위 |
| **구현 패턴** | Adapter | Channel |
| **실행 모델** | 동기/비동기 모두 가능 | 동기/비동기 모두 가능 |

### 잘못된 구분 (오해)

| 구분 | 동기 | 비동기 |
|------|------|--------|
| **구현 패턴** | Adapter ❌ | Channel ❌ |

이 구분은 **잘못되었습니다**. 실행 모델과 구현 패턴은 **독립적**입니다.

### 정확한 이해

1. **Adapter**: 형식/인터페이스 변환 (배치 변환에 주로 사용)
2. **Channel**: 스트리밍/파이프라인 (스트리밍 변환에 주로 사용)
3. **배치 vs 스트리밍**: 처리 단위의 차이
4. **블로킹 vs 비동기**: 실행 모델의 차이

---

## 다음 단계

다음 문서인 [02_batch_vs_streaming.md](./02_batch_vs_streaming.md)에서 배치 변환과 스트리밍 변환의 차이를 더 자세히 학습합니다.

