# gRPC 스트리밍 STT

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. gRPC의 기본 개념과 특징을 이해합니다
2. 양방향 스트리밍의 원리와 구현 방법을 학습합니다
3. Protocol Buffer 메시지 구조를 이해합니다
4. gRPC 클라이언트 구현을 실습합니다

## gRPC 기본 개념

### gRPC란?

gRPC는 Google이 개발한 고성능 RPC (Remote Procedure Call) 프레임워크입니다:

- **HTTP/2 기반**: 단일 연결로 다중 요청 처리
- **Protocol Buffer**: 효율적인 바이너리 직렬화
- **양방향 스트리밍**: 클라이언트와 서버가 동시에 데이터 전송 가능
- **타입 안전성**: 강력한 타입 시스템

### REST API vs gRPC

**REST API:**
- HTTP/1.1 기반
- JSON 텍스트 형식
- 요청-응답 모델
- 브라우저에서 직접 호출 가능

**gRPC:**
- HTTP/2 기반
- Protocol Buffer 바이너리 형식
- 스트리밍 지원
- 높은 성능

### gRPC 통신 방식

gRPC는 4가지 통신 방식을 지원합니다:

1. **Unary RPC**: 단일 요청-응답
2. **Server Streaming**: 서버가 스트림으로 응답
3. **Client Streaming**: 클라이언트가 스트림으로 요청
4. **Bidirectional Streaming**: 양방향 스트리밍

실시간 STT는 **Bidirectional Streaming**을 사용합니다.

## Protocol Buffer

### Protocol Buffer란?

Protocol Buffer는 구조화된 데이터를 직렬화하는 방법입니다:

- **효율적**: JSON보다 작은 크기
- **빠름**: 파싱 속도가 빠름
- **타입 안전**: 강력한 타입 시스템
- **버전 호환**: 필드 추가/삭제 시 호환성 유지

### 메시지 정의

`.proto` 파일에 메시지 구조를 정의합니다:

```protobuf
// speech.proto
syntax = "proto3";

message RecognitionConfig {
  string language_code = 1;
  bool interim_results = 2;
}

message RecognitionResult {
  string transcript = 1;
  bool is_final = 2;
  string language_code = 3;
}

message StreamingRecognizeRequest {
  RecognitionConfig config = 1;
  bytes audio_content = 2;
}

message StreamingRecognizeResponse {
  RecognitionResult result = 1;
  float total_duration = 2;
}

service Speech {
  rpc StreamingRecognize(stream StreamingRecognizeRequest) 
      returns (stream StreamingRecognizeResponse);
}
```

### 메시지 컴파일

`.proto` 파일을 Python 코드로 컴파일합니다:

```bash
python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    --proto_path=. \
    speech.proto
```

컴파일 결과:
- `speech_pb2.py`: 메시지 클래스
- `speech_pb2_grpc.py`: 서비스 스텁 클래스

## 양방향 스트리밍

### 스트리밍의 필요성

실시간 STT에서는 다음과 같은 이유로 스트리밍이 필요합니다:

1. **낮은 지연 시간**: 오디오를 받는 즉시 처리
2. **메모리 효율**: 전체 파일을 메모리에 로드하지 않음
3. **실시간 피드백**: 중간 결과를 즉시 반환

### 양방향 스트리밍 동작

```
클라이언트                    서버
    │                          │
    │─── 설정 요청 ────────────>│
    │                          │
    │─── 오디오 청크 1 ───────>│
    │                          │─── 처리 중
    │<─── 임시 결과 ───────────│
    │                          │
    │─── 오디오 청크 2 ───────>│
    │                          │─── 처리 중
    │<─── 최종 결과 ───────────│
    │                          │
    │─── 오디오 청크 3 ───────>│
    │                          │
```

### 요청 메시지 생성

첫 번째 요청은 설정을 포함하고, 이후 요청은 오디오 데이터를 포함합니다:

```python
@staticmethod
async def create_request_messages(
    audio_chunks: AsyncIterator[bytes],
    language_code: str,
    interim_results: bool,
) -> AsyncIterator[speech_pb2.StreamingRecognizeRequest]:
    """gRPC 요청 메시지를 생성하는 제너레이터"""
    
    # 첫 번째 요청: 설정 전송
    config = speech_pb2.RecognitionConfig(
        language_code=language_code,
        interim_results=interim_results,
    )
    first_request = speech_pb2.StreamingRecognizeRequest(config=config)
    yield first_request
    
    # 이후 요청: 오디오 데이터 전송
    async for audio_chunk in audio_chunks:
        if audio_chunk and len(audio_chunk) > 0:
            request = speech_pb2.StreamingRecognizeRequest(
                audio_content=audio_chunk
            )
            yield request
```

## DagloRealtimeSTTClient 구현

### 클래스 구조

```python
class DagloRealtimeSTTClient:
    def __init__(self, timeout: int = 10800):
        self.channel = None
        self.stub = None
        self.server_address = None
        self.api_token = None
        self.timeout = timeout
```

### gRPC 연결

SSL/TLS 보안 채널을 생성하고 서버에 연결합니다:

```python
async def connect(self, server_address: str, api_token: str):
    """gRPC 서버에 연결"""
    if not api_token:
        raise ValueError("api_token은 필수입니다")
    
    self.server_address = server_address
    self.api_token = api_token
    
    # SSL/TLS 보안 채널 생성
    credentials = grpc.ssl_channel_credentials()
    self.channel = grpc.aio.secure_channel(
        server_address,
        credentials,
    )
    
    # gRPC 스텁 생성
    self.stub = speech_pb2_grpc.SpeechStub(self.channel)
    
    logger.info(f"gRPC 연결 성공: server_address={server_address}")
```

### 양방향 스트리밍 수행

`stream_recognize` 메서드가 양방향 스트리밍을 수행합니다:

```python
async def stream_recognize(
    self,
    audio_chunks: AsyncIterator[bytes],
    language_code: str = "ko-KR",
    interim_results: bool = True,
) -> AsyncIterator[dict[str, str | bool | float]]:
    """실시간 STT 스트리밍을 수행합니다"""
    
    if self.stub is None or self.channel is None:
        raise RuntimeError("gRPC 연결이 설정되지 않았습니다")
    
    if language_code not in SUPPORTED_LANGUAGE_CODES:
        raise ValueError(f"지원하지 않는 언어 코드: {language_code}")
    
    # API 인증 메타데이터
    metadata = (("authorization", f"Bearer {self.api_token}"),)
    
    # 요청 제너레이터 생성
    request_iterator = self.Private.create_request_messages(
        audio_chunks,
        language_code,
        interim_results,
    )
    
    # 양방향 스트리밍 호출
    response_stream = self.stub.StreamingRecognize(
        request_iterator,
        metadata=metadata,
        timeout=self.timeout,
    )
    
    # 응답 스트림 처리
    async for response in response_stream:
        if response.result:
            result_dict = {
                "transcript": response.result.transcript,
                "is_final": response.result.is_final,
                "language_code": response.result.language_code,
                "total_duration": response.total_duration,
            }
            yield result_dict
```

### 연결 종료

리소스를 정리하고 연결을 종료합니다:

```python
async def close(self):
    """gRPC 연결을 종료하고 리소스를 정리합니다"""
    if self.channel:
        try:
            await self.channel.close()
            logger.info("gRPC 연결 종료 완료")
        except Exception as e:
            logger.error(f"gRPC 연결 종료 중 오류: {str(e)}")
        finally:
            self.channel = None
            self.stub = None
            self.server_address = None
            self.api_token = None
```

## 서버 주소 정규화

### 주소 형식 변환

다양한 형식의 API URL을 gRPC 서버 주소로 변환합니다:

```python
@staticmethod
def normalize_grpc_server_address(api_url: str | None) -> str:
    """gRPC 서버 주소를 정규화합니다"""
    if not api_url:
        return "apis.daglo.ai:443"
    
    # 스킴 제거 (http://, https://)
    address = api_url.strip()
    if address.startswith("https://"):
        address = address[8:]  # len("https://") = 8
    elif address.startswith("http://"):
        address = address[7:]  # len("http://") = 7
    
    # 포트가 없으면 443 추가
    if ":" not in address:
        address = f"{address}:443"
    
    return address
```

**변환 예시:**
- `https://apis.daglo.ai` → `apis.daglo.ai:443`
- `apis.daglo.ai` → `apis.daglo.ai:443`
- `apis.daglo.ai:443` → `apis.daglo.ai:443`

## STT 스트림 처리

### STTPipeline.process_stream

서비스 레이어에서 STT 스트림을 처리합니다:

```python
@staticmethod
async def process_stream(
    audio_chunks: AsyncIterator[bytes],
    session_id: UUID,
    stt_config: RealtimeSTTConfig,
    api_token: str,
    language_code: str = "ko-KR",
    interim_results: bool = True,
    input_format: str = "webm",
    timeout: int = 3600,
) -> AsyncIterator[dict[str, Any]]:
    """실시간 STT 스트림을 처리합니다"""
    
    # 파라미터 검증
    if not stt_config:
        raise ServiceError("STT 설정이 제공되지 않았습니다", status_code=400)
    
    if not api_token:
        raise ServiceError("API 토큰이 제공되지 않았습니다", status_code=400)
    
    # DAGLO provider만 지원
    if stt_config.provider != "DAGLO":
        raise ServiceError(
            f"실시간 STT는 DAGLO만 지원합니다. 현재 provider: {stt_config.provider}",
            status_code=400,
        )
    
    # 서버 주소 정규화
    original_url = stt_config.api_url or "apis.daglo.ai:443"
    server_address = RealtimeSTTService.Private.normalize_grpc_server_address(
        original_url
    )
    
    # gRPC 클라이언트 생성 및 연결
    client = DagloRealtimeSTTClient(timeout=timeout)
    try:
        await client.connect(
            server_address=server_address,
            api_token=api_token,
        )
        
        # 오디오 변환 제너레이터 생성
        converted_chunks = RealtimeSTTService.Private.convert_audio_chunks(
            audio_chunks,
            input_format,
        )
        
        # STT 스트리밍 수행
        async for result in client.stream_recognize(
            converted_chunks,
            language_code=language_code,
            interim_results=interim_results,
        ):
            yield result
    
    except Exception as e:
        logger.error(f"STT 스트림 처리 중 오류: {str(e)}")
        raise
    finally:
        await client.close()
```

## 실습: gRPC 클라이언트 구현

### 1. 간단한 gRPC 클라이언트

```python
# simple_grpc_client.py
import grpc.aio
from speech_pb2_grpc import SpeechStub
from speech_pb2 import StreamingRecognizeRequest, RecognitionConfig

class SimpleGRPCClient:
    def __init__(self):
        self.channel = None
        self.stub = None
    
    async def connect(self, server_address: str, api_token: str):
        """gRPC 서버에 연결"""
        credentials = grpc.ssl_channel_credentials()
        self.channel = grpc.aio.secure_channel(
            server_address,
            credentials,
        )
        self.stub = SpeechStub(self.channel)
    
    async def stream_recognize(self, audio_chunks, language_code: str):
        """STT 스트리밍 수행"""
        # 요청 제너레이터
        async def request_generator():
            # 첫 요청: 설정
            config = RecognitionConfig(
                language_code=language_code,
                interim_results=True,
            )
            yield StreamingRecognizeRequest(config=config)
            
            # 이후 요청: 오디오 데이터
            async for chunk in audio_chunks:
                yield StreamingRecognizeRequest(audio_content=chunk)
        
        # 메타데이터
        metadata = (("authorization", f"Bearer {api_token}"),)
        
        # 스트리밍 호출
        response_stream = self.stub.StreamingRecognize(
            request_generator(),
            metadata=metadata,
        )
        
        # 응답 처리
        async for response in response_stream:
            if response.result:
                yield {
                    "transcript": response.result.transcript,
                    "is_final": response.result.is_final,
                }
    
    async def close(self):
        """연결 종료"""
        if self.channel:
            await self.channel.close()
```

### 2. 사용 예시

```python
# test_grpc_client.py
import asyncio
from simple_grpc_client import SimpleGRPCClient

async def generate_audio_chunks():
    """오디오 청크 생성기 (테스트용)"""
    for i in range(10):
        yield b"audio_chunk_" + str(i).encode()

async def test_grpc_client():
    client = SimpleGRPCClient()
    
    try:
        await client.connect("apis.daglo.ai:443", "your_api_token")
        
        async for result in client.stream_recognize(
            generate_audio_chunks(),
            language_code="ko-KR"
        ):
            print(f"전사 결과: {result['transcript']}")
            print(f"최종 여부: {result['is_final']}")
    
    finally:
        await client.close()

# 실행
asyncio.run(test_grpc_client())
```

### 3. 에러 처리

```python
# grpc_client_with_error_handling.py
import grpc
from simple_grpc_client import SimpleGRPCClient

async def test_with_error_handling():
    client = SimpleGRPCClient()
    
    try:
        await client.connect("apis.daglo.ai:443", "your_api_token")
        
        async for result in client.stream_recognize(
            generate_audio_chunks(),
            language_code="ko-KR"
        ):
            print(f"전사 결과: {result['transcript']}")
    
    except grpc.RpcError as e:
        print(f"gRPC 오류 발생: code={e.code()}, details={e.details()}")
    
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")
    
    finally:
        await client.close()
```

## 성능 최적화

### 타임아웃 설정

긴 스트리밍 세션을 위해 충분한 타임아웃을 설정합니다:

```python
client = DagloRealtimeSTTClient(timeout=3600)  # 1시간
```

### gRPC 재연결 시나리오

gRPC 연결이 끊기고 재시도할 때는 다음을 수행해야 합니다:

1. **기존 Queue 종료**: 종료 신호 전송
2. **새 Queue 생성**: 재사용 불가능하므로 새로 생성
3. **ffmpeg 프로세스 재시작**: 새로운 stdout 파이프 생성
4. **새 STT 태스크 시작**: 새 Queue와 새 ffmpeg로 시작

```python
# gRPC 재연결 시나리오
async def handle_grpc_reconnect(self):
    """gRPC 재연결 처리"""
    # 1. 기존 STT 태스크 종료
    if self.stt_processing_task:
        self.stt_processing_task.cancel()
        try:
            await self.stt_processing_task
        except asyncio.CancelledError:
            pass
    
    # 2. 기존 Queue 종료 (None 전송)
    await self.message_handler.close_queue()
    
    # 3. 새 Queue 생성 (재사용 불가능)
    self.message_handler.audio_queue = asyncio.Queue()
    
    # 4. 새 STT 태스크 시작
    self.stt_processing_task = asyncio.create_task(
        self.stt_handler.process_stream(
            self.message_handler.audio_queue,  # 새 Queue
            self.session_context.session_id,
            self.session_context.language_code,
            self.session_context.interim_results,
            self.session_context.input_format,
            send_func,
            send_error_func,
            lambda: self.session_context.sequence_number,
        )
    )
```

**재연결 흐름:**

```
gRPC 연결 끊김
    ↓
기존 STT 태스크 취소
    ↓
Queue 종료 신호 전송 (put(None))
    ↓
제너레이터 종료
    ↓
새 Queue 생성 (asyncio.Queue())
    ↓
새 STT 태스크 시작
    ↓
새 ffmpeg 프로세스 시작 (새 stdout 파이프)
    ↓
새 gRPC 연결 생성
    ↓
정상 동작 재개 ✅
```

**중요 사항:**

- **Queue 재사용 불가능**: 종료된 Queue는 재사용할 수 없으므로 반드시 새로 생성
- **ffmpeg 재시작 필요**: 새로운 stdout 파이프를 위해 프로세스 재시작
- **SessionContext 유지**: 재시작 시에도 SessionContext는 유지하여 상태 보존

### 메타데이터 최적화

필요한 메타데이터만 전송하여 오버헤드를 줄입니다:

```python
metadata = (
    ("authorization", f"Bearer {api_token}"),
    # 필요한 경우 추가 메타데이터만 포함
)
```

## 스트림 종료 시나리오

### 제너레이터 종료 보장

STT 스트림 처리는 여러 단계의 제너레이터로 구성됩니다:

```
AudioHandler.generate_chunks() → 오디오 변환 → gRPC 스트림
```

각 제너레이터는 `None` 종료 신호를 받아 안전하게 종료됩니다:

```python
# AudioHandler.generate_chunks()
async def generate_chunks(
    self, audio_queue: asyncio.Queue[bytes]
) -> AsyncIterator[bytes]:
    while True:
        chunk = await audio_queue.get()
        
        # None이면 종료 신호 (제너레이터 종료 보장)
        if chunk is None:
            break  # 안전하게 종료
        
        yield chunk
```

### 종료 신호 전파

종료 신호는 다음 순서로 전파됩니다:

```
1. close_queue() 호출
   ↓
2. audio_queue.put(None) (종료 신호)
   ↓
3. AudioHandler.generate_chunks()에서 None 수신
   ↓
4. break로 제너레이터 종료
   ↓
5. 오디오 변환 제너레이터 종료
   ↓
6. gRPC 스트림 종료
   ↓
7. STT 태스크 완료
```

### 예외 상황에서의 종료 보장

예외가 발생해도 제너레이터는 안전하게 종료됩니다:

```python
async def generate_chunks(
    self, audio_queue: asyncio.Queue[bytes]
) -> AsyncIterator[bytes]:
    chunk_count = 0
    
    while True:
        try:
            chunk = await asyncio.wait_for(
                audio_queue.get(),
                timeout=1.0,
            )
            
            if chunk is None:
                break  # 정상 종료
            
            chunk_count += 1
            yield chunk
            
        except asyncio.TimeoutError:
            continue  # 타임아웃 시 계속 대기
        except Exception as e:
            logger.error(
                f"오디오 청크 생성 중 오류: chunk_count={chunk_count}, error={str(e)}",
                exc_info=True,
            )
            break  # 예외 발생 시에도 종료 보장
```

**종료 보장 메커니즘:**

- **정상 종료**: `None` 수신 시 `break`로 종료
- **예외 종료**: 예외 발생 시에도 `break`로 종료
- **타임아웃**: 타임아웃은 예외가 아니므로 계속 대기

## 정리

이 장에서는 다음을 학습했습니다:

1. **gRPC 기본 개념**: HTTP/2 기반 RPC 프레임워크
2. **Protocol Buffer**: 효율적인 바이너리 직렬화
3. **양방향 스트리밍**: 클라이언트와 서버가 동시에 데이터 전송
4. **gRPC 클라이언트 구현**: 연결, 스트리밍, 종료
5. **제너레이터 종료 보장**: None 종료 신호를 통한 안전한 종료
6. **gRPC 재연결**: Queue 재생성 및 ffmpeg 재시작

다음 장인 [05-STT-결과-처리-및-전송.md](./05-STT-결과-처리-및-전송.md)에서는 STT 결과를 처리하고 전송하는 방법을 학습합니다.

