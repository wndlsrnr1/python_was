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

### STTPipeline.process_stream

Consumer의 `STTPipeline.process_stream` 메서드가 STT 스트림을 처리합니다:

```python
async def process_stream(self) -> None:
    """STT 스트림을 처리하고 결과를 WebSocket으로 전송합니다"""

    # 1. 오디오 청크 제너레이터 생성
    audio_chunks = self.consumer.AudioPipeline(
        self.consumer
    ).generate_chunks()

    # 2. STT 설정 조회
    stt_config = await sync_to_async(
        RealtimeSTTConfigRepository.get_active
    )()

    # 3. API 키 복호화
    api_token = await sync_to_async(
        RealtimeSTTConfigService.get_decrypted_api_key
    )(stt_config)

    # 4. STT 스트림 처리
    async for result in RealtimeSTTService.STTPipeline.process_stream(
        audio_chunks,
        self.consumer.session_id,
        stt_config=stt_config,
        api_token=api_token,
        language_code=self.consumer.language_code,
        interim_results=self.consumer.interim_results,
        input_format=self.consumer.input_format,
    ):
        # 5. 결과 처리 및 전송
        await self._process_and_send_result(result)
```

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

### 메시지 변환

gRPC 응답을 WebSocket 메시지로 변환합니다:

```python
async def _process_and_send_result(self, result: dict[str, Any]):
    """STT 결과를 처리하고 WebSocket으로 전송"""

    result_type = "최종" if result.get("is_final", False) else "임시"
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
        "sequence": self.consumer.sequence_number,
    }

    transcription_json = json.dumps(transcription_data, ensure_ascii=False)

    # WebSocket으로 전송
    try:
        await self.consumer.send(text_data=transcription_json)
    except Exception as send_error:
        logger.error(f"WebSocket 전송 중 오류: {str(send_error)}")
        # WebSocket 전송 실패해도 계속 진행
```

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

## ResponsePipeline

### 응답 전송 파이프라인

`ResponsePipeline`은 클라이언트로 응답을 전송하는 파이프라인입니다:

```python
class ResponsePipeline:
    def __init__(self, consumer):
        self.consumer = consumer

    async def send_ack(self, message: str = "OK"):
        """확인 메시지 전송"""
        ack_data = {
            "type": "ack",
            "message": message,
            "sequence": self.consumer.sequence_number,
        }
        ack_json = json.dumps(ack_data, ensure_ascii=False)
        await self.consumer.send(text_data=ack_json)

    async def send_error(self, error_message: str):
        """에러 메시지 전송"""
        error_data = {
            "type": "error",
            "data": error_message,
        }
        error_json = json.dumps(error_data, ensure_ascii=False)
        await self.consumer.send(text_data=error_json)
```

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

## 정리

이 장에서는 다음을 학습했습니다:

1. **STT 결과 파이프라인**: 결과 처리 흐름
2. **메시지 포맷**: gRPC 응답과 WebSocket 메시지 변환
3. **임시/최종 결과**: 두 가지 결과 타입의 차이와 처리
4. **에러 처리**: 다양한 에러 상황 대응
5. **로깅**: 결과 추적 및 디버깅

다음 장인 [06-설정-관리-및-통합-실습.md](./06-설정-관리-및-통합-실습.md)에서는 설정 관리와 전체 시스템 통합을 학습합니다.
