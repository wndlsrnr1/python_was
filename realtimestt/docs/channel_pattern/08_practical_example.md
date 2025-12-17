# 8장: 실전 예제: 오디오 STT 파이프라인

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. 전체 오디오 STT 파이프라인을 구현할 수 있습니다
2. WebSocket → Audio → gRPC → Result → WebSocket 흐름을 이해합니다
3. 각 단계별 동작을 확인할 수 있습니다
4. 따라쳐서 실행 가능한 완전한 코드를 학습합니다

---

## 8.1 전체 파이프라인 구조

### 데이터 흐름

```
WebSocket 수신
    ↓
Audio Channel (WebM → PCM 변환)
    ↓
gRPC Channel (STT 처리)
    ↓
Result Channel (결과 버퍼링)
    ↓
WebSocket 전송
```

### 각 단계의 역할

1. **WebSocket 수신**: 클라이언트로부터 WebM 오디오 청크 수신
2. **Audio Channel**: WebM을 LINEAR16 PCM으로 실시간 변환
3. **gRPC Channel**: PCM을 STT 서버로 전송하고 결과 수신
4. **Result Channel**: STT 결과를 버퍼링
5. **WebSocket 전송**: STT 결과를 클라이언트에 전송

---

## 8.2 완전한 구현 코드

### 전체 Pipeline 코드

```python
"""
실시간 STT Pipeline 구현

여러 Channel을 연결하여 비동기로 데이터를 흘려보내는 Pipeline입니다.
WebSocket → Audio → gRPC → Result → WebSocket 순서로 데이터를 처리합니다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from transcription.channels.audio_channels import AudioChannel
from transcription.channels.grpc_channels import gRPCChannel
from transcription.channels.result_channels import ResultChannel
from transcription.channels.websocket_channels import WebSocketChannel

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from channels.generic.websocket import AsyncWebsocketConsumer


class RealtimeSTTPipeline:
    """
    실시간 STT 전체 파이프라인
    
    여러 Channel을 연결하여 비동기로 데이터를 흘려보냅니다.
    WebSocket → Audio → gRPC → Result → WebSocket 순서로 처리합니다.
    """
    
    def __init__(
        self,
        websocket: "AsyncWebsocketConsumer",
        api_token: str,
        input_format: str = "webm",
        language_code: str = "ko-KR",
        interim_results: bool = True,
        server_address: str = "apis.daglo.ai:443",
        timeout: float = 1.0,
    ) -> None:
        """
        Args:
            websocket: Django Channels AsyncWebsocketConsumer 인스턴스
            api_token: gRPC API 인증 토큰 (필수)
            input_format: 입력 오디오 형식 ("webm", "mp4", "wav", "mp3")
            language_code: 언어 코드 ("ko-KR", "en-US", "mixed")
            interim_results: 임시 결과 반환 여부 (기본값: True)
            server_address: gRPC 서버 주소 (기본값: "apis.daglo.ai:443")
            timeout: 큐에서 데이터를 가져올 때의 타임아웃 (초, 기본값: 1.0)
        """
        if not api_token:
            raise ValueError("api_token은 필수입니다")
        
        # 각 단계별 Channel 생성
        self.websocket_channel = WebSocketChannel(websocket, timeout=timeout)
        self.audio_channel = AudioChannel(input_format=input_format, timeout=timeout)
        self.grpc_channel = gRPCChannel(
            api_token=api_token,
            server_address=server_address,
            language_code=language_code,
            interim_results=interim_results,
            timeout=10800,
        )
        self.result_channel = ResultChannel(timeout=timeout)
        
        self._running = False
        self._tasks: list[asyncio.Task[None]] = []
    
    async def start(self) -> None:
        """
        전체 파이프라인 시작
        
        모든 Channel 연결 함수를 병렬로 실행합니다.
        """
        if self._running:
            logger.warning("[RealtimeSTTPipeline] Pipeline이 이미 실행 중입니다")
            return
        
        self._running = True
        logger.info("[RealtimeSTTPipeline] Pipeline 시작")
        
        try:
            # 모든 연결 함수를 병렬로 실행
            self._tasks = [
                asyncio.create_task(self._websocket_to_audio()),
                asyncio.create_task(self._audio_to_grpc()),
                asyncio.create_task(self._grpc_to_result()),
                asyncio.create_task(self._result_to_websocket()),
            ]
            
            # 모든 태스크 완료 대기
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
            logger.info("[RealtimeSTTPipeline] Pipeline 완료")
        
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Pipeline 실행 중 오류: {str(e)}",
                exc_info=True,
            )
            raise
    
    async def _websocket_to_audio(self) -> None:
        """
        WebSocket → Audio Channel
        
        WebSocket에서 WebM 오디오 청크를 수신하여 Audio Channel로 전송합니다.
        """
        try:
            async for message in self.websocket_channel.receive():
                if isinstance(message, bytes):
                    await self.audio_channel.send(message)
                    logger.debug(
                        f"[RealtimeSTTPipeline] WebSocket → Audio: "
                        f"size={len(message)} bytes"
                    )
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] WebSocket → Audio 오류: {str(e)}",
                exc_info=True,
            )
        finally:
            await self.audio_channel.close()
            logger.debug("[RealtimeSTTPipeline] Audio Channel 종료")
    
    async def _audio_to_grpc(self) -> None:
        """
        Audio → gRPC Channel
        
        Audio Channel에서 PCM 청크를 수신하여 gRPC Channel로 전송합니다.
        """
        try:
            async for pcm_chunk in self.audio_channel.receive():
                await self.grpc_channel.send(pcm_chunk)
                logger.debug(
                    f"[RealtimeSTTPipeline] Audio → gRPC: "
                    f"size={len(pcm_chunk)} bytes"
                )
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Audio → gRPC 오류: {str(e)}",
                exc_info=True,
            )
        finally:
            await self.grpc_channel.close()
            logger.debug("[RealtimeSTTPipeline] gRPC Channel 종료")
    
    async def _grpc_to_result(self) -> None:
        """
        gRPC → Result Channel
        
        gRPC Channel에서 STT 결과를 수신하여 Result Channel로 전송합니다.
        """
        try:
            async for stt_result in self.grpc_channel.receive():
                await self.result_channel.send(stt_result)
                logger.debug(
                    f"[RealtimeSTTPipeline] gRPC → Result: "
                    f"text={stt_result.get('text', '')}"
                )
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] gRPC → Result 오류: {str(e)}",
                exc_info=True,
            )
        finally:
            await self.result_channel.close()
            logger.debug("[RealtimeSTTPipeline] Result Channel 종료")
    
    async def _result_to_websocket(self) -> None:
        """
        Result → WebSocket
        
        Result Channel에서 STT 결과를 수신하여 WebSocket으로 전송합니다.
        """
        try:
            async for result in self.result_channel.receive():
                await self.websocket_channel.send(data=result)
                logger.debug(
                    f"[RealtimeSTTPipeline] Result → WebSocket: "
                    f"text={result.get('text', '')}"
                )
        except Exception as e:
            logger.error(
                f"[RealtimeSTTPipeline] Result → WebSocket 오류: {str(e)}",
                exc_info=True,
            )
        finally:
            await self.websocket_channel.close()
            logger.debug("[RealtimeSTTPipeline] WebSocket Channel 종료")
    
    async def close_all(self) -> None:
        """모든 Channel 종료"""
        logger.info("[RealtimeSTTPipeline] 모든 Channel 종료 시작")
        
        await self.websocket_channel.close()
        await self.audio_channel.close()
        await self.grpc_channel.close()
        await self.result_channel.close()
        
        # 실행 중인 태스크 취소
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # 태스크 완료 대기
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._running = False
        logger.info("[RealtimeSTTPipeline] 모든 Channel 종료 완료")
```

---

## 8.3 Django Consumer에서 사용

### Consumer 구현

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import json

from transcription.services.realtime_stt_pipeline import RealtimeSTTPipeline


class RealtimeSTTConsumer(AsyncWebsocketConsumer):
    """실시간 STT WebSocket Consumer"""
    
    async def connect(self, api_token: str) -> None:
        """WebSocket 연결"""
        await self.accept()
        
        # Pipeline 생성
        self.pipeline = RealtimeSTTPipeline(
            websocket=self,
            api_token=api_token,
            input_format="webm",
            language_code="ko-KR",
            interim_results=True,
        )
        
        # Pipeline 시작
        self.pipeline_task = asyncio.create_task(self.pipeline.start())
    
    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        """메시지 수신"""
        if text_data:
            # 제어 메시지 처리
            data = json.loads(text_data)
            if data.get("type") == "start":
                await self.send(text_data=json.dumps({
                    "type": "ack",
                    "message": "Pipeline started"
                }))
            elif data.get("type") == "end":
                await self.pipeline.close_all()
                await self.close()
        elif bytes_data:
            # 오디오 데이터를 Pipeline으로 전송
            await self.pipeline.websocket_channel.send(bytes_data=bytes_data)
    
    async def disconnect(self, close_code: int) -> None:
        """연결 종료"""
        if hasattr(self, 'pipeline'):
            await self.pipeline.close_all()
        
        if hasattr(self, 'pipeline_task'):
            self.pipeline_task.cancel()
            try:
                await self.pipeline_task
            except asyncio.CancelledError:
                pass
```

---

## 8.4 단계별 실행 결과 확인

### 단계 1: WebSocket 수신

```python
# WebSocket에서 WebM 청크 수신
async for message in self.websocket_channel.receive():
    if isinstance(message, bytes):
        # WebM 청크를 Audio Channel로 전송
        await self.audio_channel.send(message)
```

**실행 결과:**
```
[RealtimeSTTPipeline] WebSocket → Audio: size=8192 bytes
[RealtimeSTTPipeline] WebSocket → Audio: size=8192 bytes
...
```

### 단계 2: 오디오 변환

```python
# Audio Channel에서 PCM 청크 수신
async for pcm_chunk in self.audio_channel.receive():
    # PCM 청크를 gRPC Channel로 전송
    await self.grpc_channel.send(pcm_chunk)
```

**실행 결과:**
```
[RealtimeSTTPipeline] Audio → gRPC: size=16384 bytes
[RealtimeSTTPipeline] Audio → gRPC: size=16384 bytes
...
```

### 단계 3: STT 처리

```python
# gRPC Channel에서 STT 결과 수신
async for stt_result in self.grpc_channel.receive():
    # STT 결과를 Result Channel로 전송
    await self.result_channel.send(stt_result)
```

**실행 결과:**
```
[RealtimeSTTPipeline] gRPC → Result: text=안녕하세요
[RealtimeSTTPipeline] gRPC → Result: text=안녕하세요 반갑습니다
...
```

### 단계 4: 결과 전송

```python
# Result Channel에서 STT 결과 수신
async for result in self.result_channel.receive():
    # STT 결과를 WebSocket으로 전송
    await self.websocket_channel.send(data=result)
```

**실행 결과:**
```
[RealtimeSTTPipeline] Result → WebSocket: text=안녕하세요
[RealtimeSTTPipeline] Result → WebSocket: text=안녕하세요 반갑습니다
...
```

---

## 8.5 따라쳐서 실행하기

### 1. 필요한 파일 생성

```bash
# 프로젝트 디렉토리 구조
realtimestt/
├── codes/
│   └── channel_patterns/
│       └── transcription/
│           ├── channels/
│           │   ├── audio_channels.py
│           │   ├── grpc_channels.py
│           │   ├── result_channels.py
│           │   └── websocket_channels.py
│           └── services/
│               └── realtime_stt_pipeline.py
└── docs/
    └── channel_pattern/
        └── 08_practical_example.md
```

### 2. Pipeline 코드 작성

위의 `RealtimeSTTPipeline` 코드를 `realtime_stt_pipeline.py`에 작성합니다.

### 3. Consumer 코드 작성

위의 `RealtimeSTTConsumer` 코드를 `consumers.py`에 작성합니다.

### 4. 실행 및 테스트

```python
# Django 설정
# settings.py
ASGI_APPLICATION = 'myproject.asgi.application'

# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/realtime-stt/(?P<api_token>\w+)/$', consumers.RealtimeSTTConsumer.as_asgi()),
]
```

### 5. 클라이언트 테스트

```javascript
// WebSocket 클라이언트
const ws = new WebSocket('ws://localhost:8000/ws/realtime-stt/YOUR_API_TOKEN/');

ws.onopen = () => {
    // 시작 신호
    ws.send(JSON.stringify({ type: 'start' }));
    
    // 오디오 데이터 전송 (시뮬레이션)
    const audioChunks = [/* WebM 오디오 청크 */];
    audioChunks.forEach(chunk => {
        ws.send(chunk);
    });
};

ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
        const data = JSON.parse(event.data);
        console.log('STT 결과:', data.text);
    }
};

ws.onclose = () => {
    console.log('연결 종료');
};
```

---

## 8.6 문제 해결 가이드

### 문제 1: Pipeline이 시작되지 않음

**증상**: `Pipeline이 이미 실행 중입니다` 경고

**해결책**:
```python
# Pipeline이 이미 실행 중인지 확인
if self._running:
    await self.close_all()  # 기존 Pipeline 종료
    self._running = False

# 새로 시작
await self.pipeline.start()
```

### 문제 2: Channel이 종료되지 않음

**증상**: 데이터가 계속 대기 중

**해결책**:
```python
# 모든 Channel 명시적으로 종료
await self.pipeline.close_all()
```

### 문제 3: 메모리 사용량 증가

**증상**: 메모리 사용량이 계속 증가

**해결책**:
```python
# 타임아웃 설정으로 무한 대기 방지
self.audio_channel = AudioChannel(timeout=1.0)
self.grpc_channel = gRPCChannel(timeout=10800)
```

---

## 8.7 핵심 정리

### Pipeline 구조

- **WebSocket → Audio → gRPC → Result → WebSocket**
- 각 단계가 독립적인 Channel
- 모든 단계를 병렬로 실행

### 구현 포인트

- ✅ **비동기로 계속 제공하고 소모**
- ✅ **asyncio.gather()로 병렬 실행**
- ✅ **명시적 종료 신호 처리**
- ✅ **에러 처리 및 로깅**

### 사용 시나리오

- ✅ **실시간 오디오 스트리밍**
- ✅ **STT 결과 실시간 전송**
- ✅ **다단계 데이터 처리**

---

## 결론

이 교과서를 통해 다음을 학습했습니다:

1. **Adapter와 Channel의 본질적 차이**
2. **배치 변환과 스트리밍 변환의 구분**
3. **블로킹과 비동기 실행 모델의 구분**
4. **Adapter 패턴과 Channel 패턴의 구현**
5. **Pipeline 패턴을 통한 여러 Channel 연결**
6. **정확한 네이밍 규칙과 용어 사용**
7. **실전 예제를 통한 통합 이해**

이제 실제 프로젝트에서 Adapter와 Channel 패턴을 올바르게 적용할 수 있습니다!

---

## 참고 자료

- [00_chapter.md](./00_chapter.md) - 목차 및 학습 가이드
- [01_overview.md](./01_overview.md) - 개요 및 핵심 개념
- [02_batch_vs_streaming.md](./02_batch_vs_streaming.md) - 배치 변환과 스트리밍 변환
- [03_blocking_vs_async.md](./03_blocking_vs_async.md) - 블로킹과 비동기 실행 모델
- [04_adapter_pattern.md](./04_adapter_pattern.md) - Adapter 패턴 상세
- [05_channel_pattern.md](./05_channel_pattern.md) - Channel 패턴 상세
- [06_pipeline_pattern.md](./06_pipeline_pattern.md) - Pipeline 패턴
- [07_naming_conventions.md](./07_naming_conventions.md) - 네이밍 규칙 및 용어 정리

