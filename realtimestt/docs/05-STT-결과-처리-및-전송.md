# STT 결과 처리 및 전송

## 학습 목표

이 장을 통해 다음을 학습할 수 있습니다:

1. STT 결과 파이프라인(STTPipeline)의 구조를 이해합니다
2. STT 결과 메시지 포맷을 파악합니다
3. WebSocket을 통한 결과 전송 방법을 학습합니다
4. 에러 처리 및 예외 상황 대응을 이해합니다

## STT 결과 파이프라인

### 파이프라인 구조

STT 결과는 다음 단계를 거쳐 처리됩니다:

```
gRPC 응답 → 결과 파싱 → 메시지 포맷 변환 → WebSocket 전송 → 클라이언트
```

### STTHandler.process_stream

`STTHandler.process_stream` 메서드가 STT 스트림을 처리합니다:

```python
async def process_stream(
    self,
    audio_queue: asyncio.Queue[bytes],
    session_id: UUID,
    language_code: str,
    interim_results: bool,
    input_format: str,
    send_func: Callable[[str], Awaitable[None]],
    send_error_func: Callable[[str], Awaitable[None]],
    get_sequence_number: Callable[[], int],
) -> None:
    """STT 스트림을 처리하고 결과를 WebSocket으로 전송합니다

    Args:
        audio_queue: 오디오 청크를 담는 큐
        session_id: 세션 ID
        language_code: 언어 코드
        interim_results: 임시 결과 반환 여부
        input_format: 입력 오디오 형식
        send_func: WebSocket 전송 함수
        send_error_func: 에러 전송 함수
        get_sequence_number: 시퀀스 번호 조회 함수 (SessionContext에서)
    """
    # 1. STT 설정 조회
    stt_config = await sync_to_async(RealtimeSTTConfigService.get_active)()
    if not stt_config:
        await send_error_func("활성 STT 설정을 찾을 수 없습니다")
        return

    # 2. API 키 복호화
    api_token = await sync_to_async(
        RealtimeSTTConfigService.get_decrypted_api_key
    )(stt_config)

    # 3. 오디오 청크 제너레이터 생성
    audio_handler = AudioHandler()
    audio_chunks = audio_handler.generate_chunks(audio_queue)

    # 4. STT 스트림 처리
    async for result in RealtimeSTTService.STTPipeline.process_stream(
        audio_chunks,
        session_id,
        stt_config=stt_config,
        api_token=api_token,
        language_code=language_code,
        interim_results=interim_results,
        input_format=input_format,
    ):
        # 5. 결과 처리 및 전송
        transcription_data = {
            "type": "transcription",
            "data": {
                "transcript": result.get("transcript", ""),
                "is_final": result.get("is_final", False),
                "language_code": result.get("language_code", ""),
                "total_duration": result.get("total_duration", 0.0),
            },
            "sequence": get_sequence_number(),  # SessionContext에서 조회
        }
        await send_func(json.dumps(transcription_data, ensure_ascii=False))
```

### Context 전달 패턴

STT 처리 시 필요한 정보는 함수 파라미터로 명시적으로 전달합니다:

```python
# ✅ 좋은 예: 필요한 정보를 파라미터로 전달
async def process_stream(
    self,
    audio_queue: asyncio.Queue[bytes],
    session_id: UUID,
    language_code: str,  # SessionContext에서 추출
    interim_results: bool,  # SessionContext에서 추출
    input_format: str,  # SessionContext에서 추출
    get_sequence_number: Callable[[], int],  # SessionContext에서 조회
):
    # ...
```

이 패턴의 장점:
- **명시적 의존성**: 함수가 어떤 정보를 필요로 하는지 명확
- **테스트 용이성**: 각 파라미터를 독립적으로 모킹 가능
- **재사용성**: SessionContext 없이도 함수 호출 가능

## STT 결과 메시지 포맷

### gRPC 응답 구조

gRPC 서버로부터 받은 응답은 다음과 같은 구조를 가집니다:

```python
{
    "transcript": "안녕하세요",
    "is_final": True,
    "language_code": "ko-KR",
    "total_duration": 2.5
}
```

### WebSocket 메시지 포맷

클라이언트로 전송하는 메시지는 다음과 같은 구조를 가집니다:

```json
{
  "type": "transcription",
  "data": {
    "transcript": "안녕하세요",
    "is_final": true,
    "language_code": "ko-KR",
    "total_duration": 2.5
  },
  "sequence": 1
}
```

### 메시지 변환 및 전송

gRPC 응답을 WebSocket 메시지로 변환하고 전송합니다:

```python
# STTHandler.process_stream 내부
async for result in RealtimeSTTService.STTPipeline.process_stream(...):
    result_count += 1
    transcript = result.get("transcript", "")

    # WebSocket으로 전송할 메시지 구성
    transcription_data = {
        "type": "transcription",
        "data": {
            "transcript": transcript,
            "is_final": result.get("is_final", False),
            "language_code": result.get("language_code", ""),
            "total_duration": result.get("total_duration", 0.0),
        },
        "sequence": get_sequence_number(),  # SessionContext에서 조회
    }
    transcription_json = json.dumps(transcription_data, ensure_ascii=False)

    # WebSocket으로 전송
    try:
        await send_func(transcription_json)
    except Exception as send_error:
        logger.error(
            f"WebSocket 전송 중 오류: session_id={session_id}, "
            f"error={str(send_error)}",
            exc_info=True,
        )
        # WebSocket 전송 실패해도 계속 진행
```

### SessionContext에서 정보 조회

시퀀스 번호는 `get_sequence_number` 함수를 통해 SessionContext에서 조회합니다:

```python
# Consumer에서 STTHandler 호출 시
self.stt_processing_task = asyncio.create_task(
    self.stt_handler.process_stream(
        self.message_handler.audio_queue,
        self.session_context.session_id,
        self.session_context.language_code,
        self.session_context.interim_results,
        self.session_context.input_format,
        send_func,
        send_error_func,
        lambda: (
            self.session_context.sequence_number
            if self.session_context
            else 0
        ),  # SessionContext에서 시퀀스 번호 조회
    )
)
```

이 패턴의 장점:
- **최신 상태 보장**: 함수 호출 시점의 SessionContext 상태를 반영
- **느슨한 결합**: STTHandler가 SessionContext에 직접 의존하지 않음
- **유연성**: 시퀀스 번호 조회 로직을 람다로 전달하여 커스터마이징 가능

## 임시 결과 vs 최종 결과

### 임시 결과 (Interim Results)

임시 결과는 발화 도중의 부분적인 인식 결과입니다:

- **특징**:
  - `is_final: false`
  - 변경될 수 있음
  - 빠른 피드백 제공
- **용도**: 실시간 자막, 진행 상황 표시

### 최종 결과 (Final Results)

최종 결과는 완성된 발화 부분에 대한 인식 결과입니다:

- **특징**:
  - `is_final: true`
  - 변경되지 않음
  - 정확도 높음
- **용도**: 최종 전사본 저장, 분석

### 결과 처리 예시

```python
async for result in stt_stream:
    if result.get("is_final", False):
        # 최종 결과 처리
        print(f"[최종] {result['transcript']}")
        # 최종 전사본 저장
        await save_final_transcript(result)
    else:
        # 임시 결과 처리
        print(f"[임시] {result['transcript']}")
        # 실시간 자막 업데이트
        await update_subtitle(result)
```

## ResponseHandler

### 응답 전송 Handler

`ResponseHandler`는 클라이언트로 응답을 전송하는 Handler입니다:

```python
class ResponseHandler:
    """WebSocket 응답 전송 Handler"""

    async def send_ack(
        self,
        message: str,
        sequence_number: int,
        send_func: Callable[[str], Awaitable[None]],
    ) -> None:
        """확인 메시지 전송

        Args:
            message: ACK 메시지
            sequence_number: 시퀀스 번호
            send_func: WebSocket 전송 함수
        """
        ack_data = {
            "type": "ack",
            "message": message,
            "sequence": sequence_number,
        }
        ack_json = json.dumps(ack_data, ensure_ascii=False)
        await send_func(ack_json)

    async def send_error(
        self,
        error_message: str,
        send_func: Callable[[str], Awaitable[None]],
    ) -> None:
        """에러 메시지 전송

        Args:
            error_message: 에러 메시지
            send_func: WebSocket 전송 함수
        """
        error_data = {
            "type": "error",
            "data": error_message,
        }
        error_json = json.dumps(error_data, ensure_ascii=False)
        await send_func(error_json)
```

### Handler 패턴의 장점

ResponseHandler는 Consumer에 직접 의존하지 않고 `send_func`를 파라미터로 받습니다:

```python
# ✅ 좋은 예: send_func를 파라미터로 받음
async def send_ack(
    self,
    message: str,
    sequence_number: int,
    send_func: Callable[[str], Awaitable[None]],
) -> None:
    await send_func(ack_json)

# ❌ 나쁜 예: Consumer에 직접 의존
async def send_ack(self, message: str):
    await self.consumer.send(text_data=ack_json)  # 강한 결합
```

이 패턴의 장점:
- **느슨한 결합**: Handler가 Consumer에 직접 의존하지 않음
- **테스트 용이성**: send_func를 모킹하여 테스트 가능
- **재사용성**: 다른 Consumer에서도 사용 가능

### 메시지 타입

**ACK 메시지:**

```json
{
  "type": "ack",
  "message": "Session started successfully",
  "sequence": 0
}
```

**에러 메시지:**

```json
{
  "type": "error",
  "data": "세션을 찾을 수 없습니다"
}
```

**전사 결과 메시지:**

```json
{
  "type": "transcription",
  "data": {
    "transcript": "안녕하세요",
    "is_final": true,
    "language_code": "ko-KR",
    "total_duration": 2.5
  },
  "sequence": 1
}
```

## 에러 처리

### STT 처리 에러

STT 처리 중 발생하는 에러를 처리합니다:

```python
try:
    async for result in RealtimeSTTService.STTPipeline.process_stream(...):
        await self._process_and_send_result(result)
except Exception as stream_error:
    logger.error(f"STT 스트림 처리 중 예외 발생: {str(stream_error)}")
    await self.consumer.ResponsePipeline(self.consumer).send_error(
        f"STT stream processing failed: {str(stream_error)}"
    )
    return
```

### WebSocket 전송 에러

WebSocket 전송 실패는 로깅만 하고 계속 진행합니다:

```python
try:
    await self.consumer.send(text_data=transcription_json)
except Exception as send_error:
    logger.error(f"WebSocket 전송 중 오류: {str(send_error)}")
    # WebSocket 전송 실패해도 계속 진행
    # (다음 결과는 정상적으로 전송될 수 있음)
```

### 설정 조회 에러

STT 설정 조회 실패 시 에러를 전송하고 종료합니다:

```python
try:
    stt_config = await sync_to_async(
        RealtimeSTTConfigRepository.get_active
    )()
except Exception as db_error:
    logger.error(f"STT 설정 조회 중 예외 발생: {str(db_error)}")
    await self.consumer.ResponsePipeline(self.consumer).send_error(
        f"Failed to retrieve STT configuration: {str(db_error)}"
    )
    return

if not stt_config:
    await self.consumer.ResponsePipeline(self.consumer).send_error(
        "활성 STT 설정을 찾을 수 없습니다"
    )
    return
```

### API 키 복호화 에러

API 키 복호화 실패 시 에러를 전송하고 종료합니다:

```python
try:
    api_token = await sync_to_async(
        RealtimeSTTConfigService.get_decrypted_api_key
    )(stt_config)
except Exception as decrypt_error:
    logger.error(f"API 키 복호화 중 예외 발생: {str(decrypt_error)}")
    await self.consumer.ResponsePipeline(self.consumer).send_error(
        f"Failed to decrypt API key: {str(decrypt_error)}"
    )
    return

if not api_token:
    await self.consumer.ResponsePipeline(self.consumer).send_error(
        "API 키를 찾을 수 없습니다"
    )
    return
```

## 로깅

### 결과 로깅

STT 결과는 상세하게 로깅됩니다:

```python
# STT 결과 강조 로깅 (DEBUG)
separator = "=" * 50
logger.debug(f"[STT-RESULT-WEBSOCKET] {separator}")
logger.debug("[STT-RESULT-WEBSOCKET] === STT 결과 (WebSocket 전송) ===")
logger.debug(f"[STT-RESULT-WEBSOCKET] 타입: [{result_type}]")
logger.debug(f"[STT-RESULT-WEBSOCKET] Session ID: {self.consumer.session_id}")
logger.debug(f"[STT-RESULT-WEBSOCKET] 전송 메시지: {json.dumps(transcription_data, ensure_ascii=False, indent=2)}")
logger.debug(f'[STT-RESULT-WEBSOCKET] Transcript: "{transcript}"')
logger.debug(f"[STT-RESULT-WEBSOCKET] Count: {result_count}")
logger.debug(f"[STT-RESULT-WEBSOCKET] {separator}")
```

### 정보 로깅

중요한 이벤트는 INFO 레벨로 로깅됩니다:

```python
logger.info(
    f"[RealtimeSTT] STT 결과 수신 ({result_type}): "
    f'transcript="{transcript}", count={result_count}'
)
```

## 실습: 결과 처리 구현

### 1. 간단한 결과 처리기

```python
# simple_result_processor.py
import json
import asyncio
from collections.abc import AsyncIterator

class SimpleResultProcessor:
    def __init__(self, websocket):
        self.websocket = websocket
        self.sequence_number = 0

    async def process_results(
        self,
        stt_results: AsyncIterator[dict[str, Any]]
    ):
        """STT 결과를 처리하고 WebSocket으로 전송"""
        result_count = 0

        async for result in stt_results:
            result_count += 1
            result_type = "최종" if result.get("is_final", False) else "임시"
            transcript = result.get("transcript", "")

            print(f"[{result_type}] {transcript}")

            # WebSocket 메시지 구성
            message = {
                "type": "transcription",
                "data": {
                    "transcript": transcript,
                    "is_final": result.get("is_final", False),
                    "language_code": result.get("language_code", ""),
                    "total_duration": result.get("total_duration", 0.0),
                },
                "sequence": self.sequence_number,
            }

            # WebSocket으로 전송
            try:
                await self.websocket.send(json.dumps(message))
                self.sequence_number += 1
            except Exception as e:
                print(f"전송 실패: {str(e)}")

        print(f"총 {result_count}개의 결과 처리 완료")
```

### 2. 에러 처리 포함 결과 처리기

```python
# result_processor_with_error_handling.py
import json
import asyncio
from collections.abc import AsyncIterator

class ResultProcessorWithErrorHandling:
    def __init__(self, websocket):
        self.websocket = websocket
        self.sequence_number = 0

    async def send_error(self, error_message: str):
        """에러 메시지 전송"""
        error_data = {
            "type": "error",
            "data": error_message,
        }
        try:
            await self.websocket.send(json.dumps(error_data))
        except Exception as e:
            print(f"에러 메시지 전송 실패: {str(e)}")

    async def process_results(
        self,
        stt_results: AsyncIterator[dict[str, Any]]
    ):
        """STT 결과를 처리하고 WebSocket으로 전송 (에러 처리 포함)"""
        try:
            result_count = 0

            async for result in stt_results:
                result_count += 1

                # 결과 검증
                if not result.get("transcript"):
                    continue

                # 메시지 구성
                message = {
                    "type": "transcription",
                    "data": {
                        "transcript": result.get("transcript", ""),
                        "is_final": result.get("is_final", False),
                        "language_code": result.get("language_code", ""),
                        "total_duration": result.get("total_duration", 0.0),
                    },
                    "sequence": self.sequence_number,
                }

                # 전송
                try:
                    await self.websocket.send(json.dumps(message))
                    self.sequence_number += 1
                except Exception as send_error:
                    # 전송 실패는 로깅만 하고 계속 진행
                    print(f"전송 실패 (계속 진행): {str(send_error)}")

            print(f"총 {result_count}개의 결과 처리 완료")

        except Exception as e:
            # 스트림 처리 중 예외 발생
            print(f"스트림 처리 중 오류: {str(e)}")
            await self.send_error(f"STT stream processing failed: {str(e)}")
```

### 3. 통합 테스트

```python
# test_result_processing.py
import asyncio
from simple_result_processor import SimpleResultProcessor

async def generate_stt_results():
    """STT 결과 생성기 (테스트용)"""
    results = [
        {"transcript": "안녕", "is_final": False, "language_code": "ko-KR", "total_duration": 0.5},
        {"transcript": "안녕하", "is_final": False, "language_code": "ko-KR", "total_duration": 1.0},
        {"transcript": "안녕하세요", "is_final": True, "language_code": "ko-KR", "total_duration": 1.5},
    ]

    for result in results:
        yield result
        await asyncio.sleep(0.1)

class MockWebSocket:
    """테스트용 WebSocket 모의 객체"""
    async def send(self, text_data):
        print(f"전송된 메시지: {text_data}")

async def test_result_processing():
    websocket = MockWebSocket()
    processor = SimpleResultProcessor(websocket)

    await processor.process_results(generate_stt_results())

# 실행
asyncio.run(test_result_processing())
```

## 성능 최적화

### 배치 전송

여러 결과를 배치로 전송하여 오버헤드를 줄입니다:

```python
batch = []
batch_size = 10

async for result in stt_results:
    batch.append(result)

    if len(batch) >= batch_size:
        # 배치 전송
        await send_batch(batch)
        batch = []

# 남은 결과 전송
if batch:
    await send_batch(batch)
```

### 결과 필터링

불필요한 결과를 필터링하여 전송량을 줄입니다:

```python
async for result in stt_results:
    # 빈 전사본은 건너뛰기
    if not result.get("transcript"):
        continue

    # 최종 결과만 전송 (임시 결과는 제외)
    if not result.get("is_final", False):
        continue

    await send_result(result)
```

## Handler 간 의존성

실시간 STT 시스템의 Handler들은 다음과 같은 관계를 가집니다:

```
RealtimeSTTConsumer
    ├─→ MessageHandler (Consumer 참조)
    │       └─→ audio_queue 생성 및 관리
    │
    ├─→ ResponseHandler (독립적)
    │       └─→ send_func를 파라미터로 받음
    │
    └─→ STTHandler (독립적)
            ├─→ AudioHandler.generate_chunks() 사용
            ├─→ send_func를 파라미터로 받음
            └─→ get_sequence_number를 파라미터로 받음
```

### Handler 책임 분리

각 Handler는 명확한 책임을 가집니다:

- **MessageHandler**: WebSocket 메시지 처리, SessionContext 생성/업데이트, 오디오 큐 관리
- **ResponseHandler**: 응답 전송 (ack, error)
- **STTHandler**: STT 스트림 처리 및 결과 전송
- **AudioHandler**: 오디오 청크 제너레이터

## 정리

이 장에서는 다음을 학습했습니다:

1. **STT 결과 처리**: STTHandler를 통한 스트림 처리
2. **Handler 패턴**: 책임 분리와 느슨한 결합
3. **Context 전달 패턴**: SessionContext에서 정보 추출 및 전달
4. **메시지 포맷**: gRPC 응답과 WebSocket 메시지 변환
5. **임시/최종 결과**: 두 가지 결과 타입의 차이와 처리
6. **에러 처리**: 다양한 에러 상황 대응
7. **로깅**: 결과 추적 및 디버깅

다음 장인 [06-설정-관리-및-통합-실습.md](./06-설정-관리-및-통합-실습.md)에서는 설정 관리와 전체 시스템 통합을 학습합니다.
