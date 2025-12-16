# 2장: 배치 변환과 스트리밍 변환

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. 배치 변환과 스트리밍 변환의 차이를 명확히 이해합니다
2. 각 변환 방식의 메모리 사용과 성능 특성을 이해합니다
3. 실제 코드 예제를 통해 차이를 확인합니다
4. 어떤 상황에서 어떤 방식을 사용해야 하는지 판단할 수 있습니다

---

## 2.1 배치 변환 (Batch Conversion)

### 정의

**배치 변환**은 **전체 입력 데이터를 한 번에 받아서 전체 출력 데이터를 한 번에 반환**하는 방식입니다.

### 특징

- ✅ **전체 데이터를 메모리에 로드**
- ✅ **변환 완료 후 결과 반환**
- ✅ **간단한 구현**
- ❌ **메모리 사용량이 큼**
- ❌ **응답 시간이 김** (전체 완료까지 대기)

### 실제 예제: Adapter 패턴

```python
from pydub import AudioSegment
import io

async def convert_to_linear16(
    audio_bytes: bytes,
    input_format: str,
) -> bytes:
    """
    오디오를 LINEAR16 PCM 형식으로 변환합니다.
    
    Args:
        audio_bytes: 입력 오디오 바이너리 데이터 (전체)
        input_format: 입력 오디오 형식 ("mp4", "wav", "webm", "mp3")
    
    Returns:
        LINEAR16 PCM 형식의 오디오 바이너리 데이터 (전체)
    """
    # 1. 전체 파일을 메모리에 로드
    audio_io = io.BytesIO(audio_bytes)
    audio_segment = AudioSegment.from_file(
        audio_io,
        format=input_format.lower(),
    )
    
    # 2. 변환 수행
    audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
    audio_segment = audio_segment.set_channels(1)        # 모노
    audio_segment = audio_segment.set_sample_width(2)     # 16비트
    
    # 3. 전체 결과를 한 번에 반환
    output_io = io.BytesIO()
    audio_segment.export(
        output_io,
        format="raw",
        codec="pcm_s16le",
    )
    
    return output_io.getvalue()  # 전체 결과 반환
```

### 사용 예시

```python
# 파일 업로드 후 변환
async def handle_file_upload(uploaded_file):
    # 1. 전체 파일 읽기
    audio_bytes = await uploaded_file.read()  # 전체 데이터
    
    # 2. 전체 변환
    pcm_data = await convert_to_linear16(
        audio_bytes,  # 전체 입력
        "webm"
    )  # 전체 출력
    
    # 3. 변환 완료 후 사용
    await save_to_database(pcm_data)
```

### 메모리 사용 분석

```
입력 파일: 10MB WebM
    ↓
메모리 사용:
  - 입력 버퍼: 10MB
  - AudioSegment 객체: ~15MB (압축 해제 후)
  - 출력 버퍼: ~5MB (PCM 변환 후)
  - 총 메모리: ~30MB
```

---

## 2.2 스트리밍 변환 (Streaming Conversion)

### 정의

**스트리밍 변환**은 **청크 단위로 입력을 받아서 청크 단위로 출력을 반환**하는 방식입니다.

### 특징

- ✅ **청크 단위로 처리**
- ✅ **실시간으로 결과 출력**
- ✅ **메모리 사용량이 적음**
- ✅ **응답 시간이 빠름** (첫 청크부터 출력)
- ❌ **구현이 복잡함**

### 실제 예제: Channel 패턴

```python
import asyncio
from collections.abc import AsyncIterator

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
        """
        WebM 청크를 내부 큐에 추가합니다.
        
        Args:
            chunk: WebM 오디오 청크 바이너리 데이터
        """
        if self._closed:
            raise RuntimeError("Channel이 이미 종료되었습니다")
        
        await self._queue.put(chunk)
    
    async def close(self) -> None:
        """Channel 종료 신호 전송"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """
        PCM 청크를 실시간으로 yield합니다.
        
        Yields:
            bytes: PCM 오디오 청크 바이너리 데이터
        """
        async for item in self:
            yield item
    
    def __aiter__(self) -> AsyncIterator[bytes]:
        """async for를 사용할 수 있도록 iterator 인터페이스 제공"""
        return self._generate()
    
    async def _generate(self) -> AsyncIterator[bytes]:
        """
        내부 generator
        
        큐에서 WebM 청크를 가져와 ffmpeg로 변환한 후 PCM 청크를 yield합니다.
        """
        from subprocess import Popen, PIPE
        
        # ffmpeg 프로세스 시작
        process = Popen(
            [
                "ffmpeg",
                "-i", "pipe:0",      # stdin에서 입력
                "-f", "s16le",        # 출력 형식
                "-ar", "16000",       # 샘플레이트 16kHz
                "-ac", "1",           # 모노
                "-acodec", "pcm_s16le",
                "pipe:1",             # stdout으로 출력
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
        )
        
        chunk_count = 0
        pcm_chunk_count = 0
        
        try:
            # 백그라운드 태스크: 큐에서 WebM 청크를 읽어 ffmpeg에 전송
            async def write_chunks() -> None:
                nonlocal chunk_count
                try:
                    while True:
                        try:
                            chunk = await asyncio.wait_for(
                                self._queue.get(), timeout=self._timeout
                            )
                            
                            if chunk is None:  # 종료 신호
                                break
                            
                            chunk_count += 1
                            process.stdin.write(chunk)
                            process.stdin.flush()
                        except asyncio.TimeoutError:
                            continue
                finally:
                    process.stdin.close()
            
            # 백그라운드 태스크 시작
            write_task = asyncio.create_task(write_chunks())
            
            # stdout에서 PCM 청크 읽기
            while True:
                pcm_chunk = process.stdout.read(8192)  # 8KB 청크
                if not pcm_chunk:
                    break
                
                pcm_chunk_count += 1
                yield pcm_chunk  # 실시간으로 yield
            
            # write_task 완료 대기
            await write_task
            
        finally:
            process.terminate()
            process.wait()
```

### 사용 예시

```python
# 실시간 스트리밍 변환
async def handle_realtime_stream(websocket):
    audio_channel = AudioChannel(input_format="webm")
    
    # 병렬 실행: WebSocket 수신과 변환을 동시에
    await asyncio.gather(
        # Producer: WebSocket에서 청크 수신
        async def producer():
            async for message in websocket:
                if isinstance(message, bytes):
                    await audio_channel.send(message)  # 청크 단위 입력
            await audio_channel.close()
        
        # Consumer: 변환된 PCM 청크 처리
        async def consumer():
            async for pcm_chunk in audio_channel.receive():
                await process_pcm_chunk(pcm_chunk)  # 실시간 처리
    )
```

### 메모리 사용 분석

```
입력 스트림: 10MB WebM (청크 단위)
    ↓
메모리 사용:
  - 큐 버퍼: ~64KB (청크 크기에 따라)
  - ffmpeg 프로세스 버퍼: ~128KB
  - 출력 버퍼: ~8KB (한 번에 yield하는 크기)
  - 총 메모리: ~200KB (고정)
```

---

## 2.3 비교표

| 항목 | 배치 변환 | 스트리밍 변환 |
|------|----------|--------------|
| **처리 단위** | 전체 데이터 | 청크 단위 |
| **메모리 사용** | 높음 (전체 로드) | 낮음 (청크 단위) |
| **응답 시간** | 전체 완료 후 | 실시간 (첫 청크부터) |
| **구현 복잡도** | 낮음 | 높음 |
| **사용 시나리오** | 파일 업로드 후 변환 | 실시간 오디오 스트리밍 |
| **구현 패턴** | Adapter | Channel |
| **예제** | `convert_to_linear16()` | `AudioChannel` |

---

## 2.4 언제 어떤 방식을 사용할까?

### 배치 변환을 사용하는 경우

✅ **파일 업로드 후 변환**
- 사용자가 파일을 업로드하고 변환 결과를 다운로드
- 전체 파일이 필요하므로 배치 변환이 적합

✅ **작은 파일 처리**
- 파일 크기가 작아 메모리 부담이 적음
- 구현이 간단하여 유지보수가 쉬움

✅ **일괄 처리 작업**
- 여러 파일을 한 번에 변환
- 배치 작업 스케줄러에서 실행

### 스트리밍 변환을 사용하는 경우

✅ **실시간 오디오 스트리밍**
- WebSocket을 통한 실시간 오디오 전송
- 첫 청크부터 처리해야 함

✅ **큰 파일 처리**
- 파일 크기가 커서 메모리에 전체 로드 불가
- 메모리 효율성이 중요

✅ **파이프라인 처리**
- 여러 단계를 거쳐 데이터를 처리
- 각 단계가 실시간으로 연결되어야 함

---

## 2.5 실습 예제

### 실습 1: 배치 변환 구현

다음 코드를 따라쳐서 실행해보세요:

```python
import asyncio
from pydub import AudioSegment
import io

async def convert_to_linear16(
    audio_bytes: bytes,
    input_format: str,
) -> bytes:
    """배치 변환: 전체 입력 → 전체 출력"""
    audio_io = io.BytesIO(audio_bytes)
    audio_segment = AudioSegment.from_file(audio_io, format=input_format)
    
    audio_segment = audio_segment.set_frame_rate(16000)
    audio_segment = audio_segment.set_channels(1)
    audio_segment = audio_segment.set_sample_width(2)
    
    output_io = io.BytesIO()
    audio_segment.export(output_io, format="raw", codec="pcm_s16le")
    
    return output_io.getvalue()

# 사용 예시
async def main():
    # 전체 파일 읽기
    with open("input.webm", "rb") as f:
        audio_bytes = f.read()  # 전체 데이터
    
    # 전체 변환
    pcm_data = await convert_to_linear16(audio_bytes, "webm")
    
    # 결과 저장
    with open("output.pcm", "wb") as f:
        f.write(pcm_data)  # 전체 결과
    
    print(f"변환 완료: {len(audio_bytes)} bytes → {len(pcm_data)} bytes")

asyncio.run(main())
```

### 실습 2: 스트리밍 변환 구현

다음 코드를 따라쳐서 실행해보세요:

```python
import asyncio
from collections.abc import AsyncIterator

class SimpleAudioChannel:
    """간단한 스트리밍 변환 Channel"""
    
    def __init__(self) -> None:
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._closed = False
    
    async def send(self, chunk: bytes) -> None:
        """청크 단위 입력"""
        if not self._closed:
            await self._queue.put(chunk)
    
    async def close(self) -> None:
        """종료 신호"""
        if not self._closed:
            self._closed = True
            await self._queue.put(None)
    
    async def receive(self) -> AsyncIterator[bytes]:
        """청크 단위 출력"""
        while True:
            chunk = await self._queue.get()
            if chunk is None:
                break
            yield chunk  # 실시간 yield

# 사용 예시
async def main():
    channel = SimpleAudioChannel()
    
    # Producer: 청크 단위로 데이터 전송
    async def producer():
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        for chunk in chunks:
            await channel.send(chunk)
            await asyncio.sleep(0.1)  # 시뮬레이션
        await channel.close()
    
    # Consumer: 청크 단위로 데이터 수신
    async def consumer():
        async for chunk in channel.receive():
            print(f"수신: {chunk}")
    
    # 병렬 실행
    await asyncio.gather(producer(), consumer())

asyncio.run(main())
```

---

## 2.6 핵심 정리

### 배치 변환

- **처리 단위**: 전체 데이터
- **메모리**: 높음 (전체 로드)
- **응답 시간**: 전체 완료 후
- **구현 패턴**: Adapter
- **사용 시나리오**: 파일 업로드 후 변환

### 스트리밍 변환

- **처리 단위**: 청크 단위
- **메모리**: 낮음 (청크 단위)
- **응답 시간**: 실시간 (첫 청크부터)
- **구현 패턴**: Channel
- **사용 시나리오**: 실시간 오디오 스트리밍

### 선택 기준

1. **전체 데이터가 필요한가?** → 배치 변환
2. **실시간 처리가 필요한가?** → 스트리밍 변환
3. **메모리가 제한적인가?** → 스트리밍 변환
4. **구현이 간단해야 하는가?** → 배치 변환

---

## 다음 단계

다음 문서인 [03_blocking_vs_async.md](./03_blocking_vs_async.md)에서 블로킹과 비동기 실행 모델의 차이를 학습합니다.

