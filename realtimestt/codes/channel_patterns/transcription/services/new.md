문서를 확인해 WebSocketChannel과 Pipeline의 관계를 정리 중입니다.


[2 tools called]


맞습니다. 구조는 다음과 같습니다:

## 구조 관계

### Pipeline이 WebSocketChannel을 포함

```python
class RealtimeSTTPipeline:
    """실시간 STT 전체 파이프라인"""
    
    def __init__(self, websocket) -> None:
        # Pipeline이 WebSocketChannel을 포함
        self.websocket_channel = WebSocketChannel(websocket)  # ← 포함
        self.audio_channel = AudioChannel(input_format="webm")
        self.grpc_channel = gRPCChannel()
        self.result_channel = ResultChannel()
    
    async def start(self) -> None:
        """Pipeline이 모든 Channel을 연결"""
        await asyncio.gather(
            self._websocket_to_audio(),    # WebSocketChannel 사용
            self._audio_to_grpc(),
            self._grpc_to_result(),
            self._result_to_websocket(),   # WebSocketChannel 사용
        )
```

### Django Consumer에서 Pipeline 사용

현재 구조에서는 Consumer가 Pipeline을 생성하고 시작합니다:

```python
class RealtimeSTTConsumer(AsyncWebsocketConsumer):
    async def connect(self) -> None:
        await self.accept()
        
        # Pipeline 생성 (WebSocket 전달)
        self.pipeline = RealtimeSTTPipeline(websocket=self)
        
        # Pipeline 시작
        self.pipeline_task = asyncio.create_task(self.pipeline.start())
    
    async def receive(self, text_data=None, bytes_data=None):
        """WebSocket 메시지 수신"""
        if bytes_data:
            # Pipeline의 WebSocketChannel로 전달
            await self.pipeline.websocket_channel.send(bytes_data)
    
    async def disconnect(self, close_code):
        # Pipeline 종료
        await self.pipeline.close_all()
        if self.pipeline_task:
            self.pipeline_task.cancel()
```

## 전체 구조 다이어그램

```
┌─────────────────────────┐
│ RealtimeSTTConsumer     │
│ (Django Channels)       │
└───────────┬─────────────┘
            │ 생성 및 시작
            ▼
┌─────────────────────────┐
│ RealtimeSTTPipeline     │ ← Pipeline이 모든 Channel 관리
│                         │
│  ┌───────────────────┐  │
│  │ WebSocketChannel  │  │ ← Pipeline이 포함
│  └─────────┬─────────┘  │
│            │             │
│  ┌─────────▼─────────┐  │
│  │  AudioChannel     │  │ ← Pipeline이 포함
│  └─────────┬─────────┘  │
│            │             │
│  ┌─────────▼─────────┐  │
│  │  gRPCChannel      │  │ ← Pipeline이 포함
│  └─────────┬─────────┘  │
│            │             │
│  ┌─────────▼─────────┐  │
│  │ ResultChannel     │  │ ← Pipeline이 포함
│  └─────────┬─────────┘  │
│            │             │
│  ┌─────────▼─────────┐  │
│  │ WebSocketChannel  │  │ ← Pipeline이 포함 (응답용)
│  └───────────────────┘  │
└─────────────────────────┘
```

## 구현 순서

1. WebSocketChannel 구현 (단독)
   - WebSocket을 Channel 패턴으로 추상화
   - 독립적으로 테스트 가능

2. Pipeline 구현 (WebSocketChannel 포함)
   - WebSocketChannel, AudioChannel 등을 포함
   - Channel 간 연결 로직 구현

3. Consumer에서 Pipeline 사용
   - Consumer가 Pipeline 생성 및 시작
   - WebSocket 이벤트를 Pipeline으로 전달

## 핵심 포인트

- WebSocketChannel이 Pipeline을 사용하는 것이 아님
- Pipeline이 WebSocketChannel을 포함하고 관리함
- Consumer는 Pipeline을 생성하고 시작만 함

따라서 WebSocketChannel은 독립적인 Channel로 구현하고, Pipeline에서 이를 포함해 사용하는 구조가 적절합니다.

Pipeline 패턴의 동작 방식을 문서에서 확인 중입니다.


[2 tools called]


맞습니다. Pipeline 패턴은 Channel 간 연결을 통해 데이터를 전달합니다.

## Pipeline 패턴의 핵심 원리

### 제공 → 제공 → 제공 (Producer 체인)

각 연결 함수가 이전 Channel을 소비하고 다음 Channel에 제공합니다:

```python
async def _websocket_to_audio(self) -> None:
    """WebSocket → Audio Channel"""
    async for message in self.websocket_channel:  # 소비 ←
        audio_data = self._parse_audio(message)
        await self.audio_channel.send(audio_data)  # 제공 →
    await self.audio_channel.close()

async def _audio_to_grpc(self) -> None:
    """Audio → gRPC Channel"""
    async for pcm_chunk in self.audio_channel:  # 소비 ←
        await self.grpc_channel.send(pcm_chunk)  # 제공 →
    await self.grpc_channel.close()
```

### 소비 ← 소비 ← 소비 (Consumer 체인)

각 Channel은 이전 단계의 출력을 소비하고 다음 단계에 제공합니다:

```
WebSocketChannel (소비) → AudioChannel (소비) → gRPCChannel (소비) → ResultChannel
```

## 실시간 STT Pipeline 구조

현재 AudioChannel이 ffmpeg를 내부화했으므로, 실제 구조는 다음과 같습니다:

```python
class RealtimeSTTPipeline:
    def __init__(self, websocket) -> None:
        # 각 단계별 Channel
        self.websocket_channel = WebSocketChannel(websocket)  # WebSocket 수신/전송
        self.audio_channel = AudioChannel(input_format="webm")  # ffmpeg 내부화됨 ✅
        self.grpc_channel = gRPCChannel()  # gRPC STT 전송
        self.result_channel = ResultChannel()  # STT 결과 버퍼링
    
    async def start(self) -> None:
        """전체 파이프라인 시작"""
        await asyncio.gather(
            # 제공 → 제공 → 제공 패턴
            self._websocket_to_audio(),    # WebSocket 소비 → Audio 제공
            self._audio_to_grpc(),         # Audio 소비 → gRPC 제공
            self._grpc_to_result(),        # gRPC 소비 → Result 제공
            self._result_to_websocket(),   # Result 소비 → WebSocket 제공
        )
    
    async def _websocket_to_audio(self) -> None:
        """WebSocket → Audio Channel"""
        async for message in self.websocket_channel:  # 소비 ←
            if self._is_audio_chunk(message):
                await self.audio_channel.send(message)  # 제공 →
        await self.audio_channel.close()
    
    async def _audio_to_grpc(self) -> None:
        """Audio → gRPC Channel"""
        async for pcm_chunk in self.audio_channel:  # 소비 ← (이미 PCM으로 변환됨)
            await self.grpc_channel.send(pcm_chunk)  # 제공 →
        await self.grpc_channel.close()
    
    async def _grpc_to_result(self) -> None:
        """gRPC → Result Channel"""
        async for stt_result in self.grpc_channel:  # 소비 ←
            await self.result_channel.send(stt_result)  # 제공 →
        await self.result_channel.close()
    
    async def _result_to_websocket(self) -> None:
        """Result → WebSocket"""
        async for result in self.result_channel:  # 소비 ←
            await self.websocket_channel.send(result)  # 제공 →
```

## 데이터 흐름 다이어그램

```
┌─────────────────┐
│  WebSocket      │
│  (클라이언트)    │
└────────┬────────┘
         │ send()
         ▼
┌─────────────────┐      소비 ←      ┌─────────────────┐
│ WebSocketChannel │ ──────────────→ │  AudioChannel   │
│   (제공)         │                  │   (소비)        │
└─────────────────┘                  └────────┬────────┘
                                             │ yield (PCM)
                                             ▼
                                    ┌─────────────────┐      소비 ←
                                    │  gRPCChannel    │ ────────────
                                    │   (제공)        │
                                    └────────┬────────┘
                                             │ yield (STT 결과)
                                             ▼
                                    ┌─────────────────┐      소비 ←
                                    │ ResultChannel   │ ────────────
                                    │   (제공)        │
                                    └────────┬────────┘
                                             │ yield
                                             ▼
                                    ┌─────────────────┐
                                    │ WebSocketChannel│
                                    │   (소비)        │
                                    └────────┬────────┘
                                             │ send()
                                             ▼
                                    ┌─────────────────┐
                                    │  WebSocket      │
                                    │  (클라이언트)    │
                                    └─────────────────┘
```

## 핵심 패턴 정리

1. 각 Channel은 독립적: 내부 큐를 가지고 send/__aiter__/close 제공
2. Pipeline이 연결: 각 `_xxx_to_yyy()` 함수가 Channel 간 연결
3. 소비 → 제공 체인:
   - `async for item in channel_A` (소비)
   - `await channel_B.send(processed_item)` (제공)
4. 병렬 실행: 모든 연결 함수를 `asyncio.gather()`로 동시 실행

## AudioChannel의 특수성

AudioChannel은 ffmpeg 변환을 내부화했으므로:
- 입력: WebM 청크 (send)
- 내부: ffmpeg 변환 (자동)
- 출력: PCM 청크 (async for)

따라서 Pipeline에서는:
```python
# WebSocket → Audio (WebM 전송)
await self.audio_channel.send(webm_chunk)

# Audio → gRPC (PCM 수신)
async for pcm_chunk in self.audio_channel:
    await self.grpc_channel.send(pcm_chunk)
```

이 패턴으로 각 단계가 명확히 분리되고, Pipeline이 전체 흐름을 관리합니다.