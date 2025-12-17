# 4장: Adapter 패턴 상세

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. Adapter 패턴의 정의와 목적을 이해합니다
2. FormatAdapter, CodecAdapter를 구현할 수 있습니다
3. 배치 변환 Adapter를 실습으로 학습합니다
4. 실제 사용 시나리오를 이해합니다

---

## 4.1 Adapter 패턴의 정의

### GoF Adapter 패턴

**Adapter 패턴**은 **서로 호환되지 않는 인터페이스를 연결**하는 디자인 패턴입니다.

### 핵심 목적

- **인터페이스 변환**: 외부 라이브러리 인터페이스를 우리 코드에 맞춤
- **형식 변환**: 데이터 형식을 변환 (예: WebM → PCM)
- **코덱 변환**: 오디오/비디오 코덱 변환

### Adapter의 특징

- ✅ **변환**이 핵심 목적
- ✅ **동기/비동기 모두 가능**
- ✅ **배치 변환에 주로 사용** (전체 데이터 처리)

---

## 4.2 FormatAdapter 구현

### 기본 구조

```python
from typing import Protocol

class FormatAdapter(Protocol):
    """형식 변환 Adapter 인터페이스"""
    
    async def convert(self, data: bytes, input_format: str) -> bytes:
        """데이터 형식을 변환합니다"""
        ...
```

### 실제 구현: 오디오 형식 변환

```python
from pydub import AudioSegment
import io

class AudioFormatAdapter:
    """오디오 형식 변환 Adapter"""
    
    SUPPORTED_FORMATS = ["mp4", "wav", "webm", "mp3"]
    TARGET_SAMPLE_RATE = 16000  # 16kHz
    TARGET_CHANNELS = 1          # 모노
    TARGET_SAMPLE_WIDTH = 2       # 16비트
    
    async def convert(
        self,
        audio_bytes: bytes,
        input_format: str,
    ) -> bytes:
        """
        오디오를 LINEAR16 PCM 형식으로 변환합니다.
        
        Args:
            audio_bytes: 입력 오디오 바이너리 데이터
            input_format: 입력 오디오 형식
        
        Returns:
            LINEAR16 PCM 형식의 오디오 바이너리 데이터
        """
        if input_format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"지원하지 않는 형식: {input_format}. "
                f"지원 형식: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # 1. 전체 파일을 메모리에 로드
        audio_io = io.BytesIO(audio_bytes)
        audio_segment = AudioSegment.from_file(
            audio_io,
            format=input_format.lower(),
        )
        
        # 2. 형식 변환
        audio_segment = audio_segment.set_frame_rate(self.TARGET_SAMPLE_RATE)
        audio_segment = audio_segment.set_channels(self.TARGET_CHANNELS)
        audio_segment = audio_segment.set_sample_width(self.TARGET_SAMPLE_WIDTH)
        
        # 3. 전체 결과 반환
        output_io = io.BytesIO()
        audio_segment.export(
            output_io,
            format="raw",
            codec="pcm_s16le",
        )
        
        return output_io.getvalue()
```

---

## 4.3 CodecAdapter 구현

### 기본 구조

```python
class CodecAdapter:
    """코덱 변환 Adapter"""
    
    async def convert(
        self,
        data: bytes,
        input_codec: str,
        output_codec: str,
    ) -> bytes:
        """코덱을 변환합니다"""
        ...
```

### 실제 구현: 오디오 코덱 변환

```python
class AudioCodecAdapter:
    """오디오 코덱 변환 Adapter"""
    
    def __init__(self) -> None:
        self.format_adapter = AudioFormatAdapter()
    
    async def convert(
        self,
        audio_bytes: bytes,
        input_codec: str,
        output_codec: str = "pcm_s16le",
    ) -> bytes:
        """
        오디오 코덱을 변환합니다.
        
        Args:
            audio_bytes: 입력 오디오 바이너리 데이터
            input_codec: 입력 코덱 (예: "opus", "aac")
            output_codec: 출력 코덱 (기본값: "pcm_s16le")
        
        Returns:
            변환된 오디오 바이너리 데이터
        """
        # 코덱에서 형식 추출
        input_format = self._codec_to_format(input_codec)
        
        # 형식 변환 Adapter 사용
        return await self.format_adapter.convert(
            audio_bytes,
            input_format,
        )
    
    def _codec_to_format(self, codec: str) -> str:
        """코덱을 형식으로 변환"""
        codec_map = {
            "opus": "webm",
            "aac": "mp4",
            "mp3": "mp3",
            "pcm": "wav",
        }
        return codec_map.get(codec.lower(), "webm")
```

---

## 4.4 배치 변환 Adapter 구현

### 파일 업로드 후 변환 시나리오

```python
class FileUploadAdapter:
    """파일 업로드 후 변환 Adapter"""
    
    def __init__(self) -> None:
        self.format_adapter = AudioFormatAdapter()
    
    async def process_upload(
        self,
        uploaded_file: bytes,
        filename: str,
    ) -> bytes:
        """
        업로드된 파일을 처리합니다.
        
        Args:
            uploaded_file: 업로드된 파일 바이너리 데이터
            filename: 파일명 (확장자로 형식 추출)
        
        Returns:
            변환된 오디오 바이너리 데이터
        """
        # 파일 확장자에서 형식 추출
        input_format = self._extract_format(filename)
        
        # 전체 파일 변환
        converted = await self.format_adapter.convert(
            uploaded_file,
            input_format,
        )
        
        return converted
    
    def _extract_format(self, filename: str) -> str:
        """파일명에서 형식 추출"""
        extension = filename.split(".")[-1].lower()
        return extension
```

### 사용 예시

```python
async def handle_file_upload(uploaded_file: bytes, filename: str):
    """파일 업로드 처리"""
    adapter = FileUploadAdapter()
    
    # 전체 파일 변환
    pcm_data = await adapter.process_upload(
        uploaded_file,
        filename,
    )
    
    # 변환 완료 후 저장
    await save_to_database(pcm_data)
    return {"status": "success", "size": len(pcm_data)}
```

---

## 4.5 Spring Converter와의 비교

### Spring Converter

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

### Python Adapter

Python의 Adapter도 동일한 패턴:

```python
# Python Adapter
class AudioFormatAdapter:
    async def convert(self, audio_bytes: bytes, input_format: str) -> bytes:
        # 전체 데이터를 한 번에 변환
        return convert_to_pcm(audio_bytes, input_format)
```

### 공통점

- ✅ **형식 변환**이 핵심
- ✅ **전체 데이터 처리**
- ✅ **인터페이스 추상화**

---

## 4.6 실습 예제

### 실습 1: 기본 FormatAdapter 구현

다음 코드를 따라쳐서 실행해보세요:

```python
import asyncio
from pydub import AudioSegment
import io

class SimpleAudioAdapter:
    """간단한 오디오 형식 변환 Adapter"""
    
    async def convert(
        self,
        audio_bytes: bytes,
        input_format: str,
    ) -> bytes:
        """오디오를 PCM 형식으로 변환"""
        # 전체 파일 로드
        audio_io = io.BytesIO(audio_bytes)
        audio_segment = AudioSegment.from_file(
            audio_io,
            format=input_format.lower(),
        )
        
        # 형식 변환
        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)
        
        # 결과 반환
        output_io = io.BytesIO()
        audio_segment.export(
            output_io,
            format="raw",
            codec="pcm_s16le",
        )
        
        return output_io.getvalue()

# 사용 예시
async def main():
    adapter = SimpleAudioAdapter()
    
    # 파일 읽기
    with open("input.webm", "rb") as f:
        audio_bytes = f.read()
    
    # 변환
    pcm_data = await adapter.convert(audio_bytes, "webm")
    
    # 결과 저장
    with open("output.pcm", "wb") as f:
        f.write(pcm_data)
    
    print(f"변환 완료: {len(audio_bytes)} → {len(pcm_data)} bytes")

asyncio.run(main())
```

### 실습 2: CodecAdapter 구현

```python
class SimpleCodecAdapter:
    """간단한 코덱 변환 Adapter"""
    
    def __init__(self) -> None:
        self.format_adapter = SimpleAudioAdapter()
    
    async def convert(
        self,
        audio_bytes: bytes,
        input_codec: str,
    ) -> bytes:
        """코덱 변환"""
        # 코덱 → 형식 매핑
        codec_map = {
            "opus": "webm",
            "aac": "mp4",
            "mp3": "mp3",
        }
        
        input_format = codec_map.get(input_codec.lower(), "webm")
        return await self.format_adapter.convert(audio_bytes, input_format)

# 사용 예시
async def main():
    adapter = SimpleCodecAdapter()
    
    with open("input.webm", "rb") as f:
        audio_bytes = f.read()
    
    # 코덱 변환
    pcm_data = await adapter.convert(audio_bytes, "opus")
    
    with open("output.pcm", "wb") as f:
        f.write(pcm_data)
    
    print("코덱 변환 완료")

asyncio.run(main())
```

### 실습 3: 파일 업로드 Adapter

```python
class FileUploadAdapter:
    """파일 업로드 Adapter"""
    
    def __init__(self) -> None:
        self.format_adapter = SimpleAudioAdapter()
    
    async def process_upload(
        self,
        uploaded_file: bytes,
        filename: str,
    ) -> bytes:
        """업로드된 파일 처리"""
        # 확장자에서 형식 추출
        extension = filename.split(".")[-1].lower()
        
        # 변환
        return await self.format_adapter.convert(
            uploaded_file,
            extension,
        )

# 사용 예시
async def main():
    adapter = FileUploadAdapter()
    
    # 파일 업로드 시뮬레이션
    with open("input.webm", "rb") as f:
        uploaded_file = f.read()
    
    # 처리
    pcm_data = await adapter.process_upload(
        uploaded_file,
        "audio.webm",
    )
    
    # 저장
    with open("output.pcm", "wb") as f:
        f.write(pcm_data)
    
    print("파일 업로드 처리 완료")

asyncio.run(main())
```

---

## 4.7 실제 사용 시나리오

### 시나리오 1: 파일 업로드 후 변환

```python
# FastAPI 엔드포인트
from fastapi import FastAPI, UploadFile

app = FastAPI()
adapter = FileUploadAdapter()

@app.post("/upload")
async def upload_file(file: UploadFile):
    """파일 업로드 후 변환"""
    # 전체 파일 읽기
    audio_bytes = await file.read()
    
    # 전체 변환
    pcm_data = await adapter.process_upload(
        audio_bytes,
        file.filename,
    )
    
    # 결과 반환
    return {
        "status": "success",
        "original_size": len(audio_bytes),
        "converted_size": len(pcm_data),
    }
```

### 시나리오 2: 일괄 처리 작업

```python
async def batch_process(files: list[str]):
    """여러 파일을 일괄 처리"""
    adapter = SimpleAudioAdapter()
    results = []
    
    for filename in files:
        with open(filename, "rb") as f:
            audio_bytes = f.read()
        
        # 각 파일 변환
        pcm_data = await adapter.convert(
            audio_bytes,
            filename.split(".")[-1],
        )
        
        results.append({
            "filename": filename,
            "size": len(pcm_data),
        })
    
    return results
```

---

## 4.8 핵심 정리

### Adapter 패턴의 특징

- ✅ **형식/인터페이스 변환**이 핵심
- ✅ **배치 변환에 주로 사용** (전체 데이터 처리)
- ✅ **동기/비동기 모두 가능**
- ✅ **간단한 구현**

### 사용 시나리오

- ✅ **파일 업로드 후 변환**
- ✅ **일괄 처리 작업**
- ✅ **형식/코덱 변환**

### Spring과의 비교

- Spring의 `Converter`와 동일한 패턴
- 형식 변환이 핵심 목적
- 전체 데이터 처리에 적합

---

## 다음 단계

다음 문서인 [05_channel_pattern.md](./05_channel_pattern.md)에서 Channel 패턴의 구현과 사용법을 실습으로 학습합니다.

