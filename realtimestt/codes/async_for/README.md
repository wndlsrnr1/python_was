# async for 및 AsyncIterator 튜토리얼

## 개요

이 튜토리얼은 Python의 `async for` 문법과 `AsyncIterator`의 기본 개념과 사용 방법을 학습하고 테스트할 수 있도록 구성되었습니다. 실시간 STT 시스템에서 사용되는 패턴을 기반으로 실용적인 예제를 포함합니다.

## 학습 목표

이 튜토리얼을 통해 다음을 학습할 수 있습니다:

1. `async for`를 왜 사용하는가 (동기 for와의 차이)
2. `async for` 문법의 기본 사용법
3. `AsyncIterator` 인터페이스 이해
4. 비동기 제너레이터 작성 방법
5. 실무에서 자주 사용되는 패턴 (Queue 기반 비동기 제너레이터)

## 왜 async for를 사용하는가?

### 동기 for의 한계

동기 `for`는 `await`를 사용할 수 없으므로 비동기 제너레이터를 직접 사용할 수 없습니다:

```python
# ❌ 불가능: 동기 for에서 await 사용 불가
def sync_example():
    for item in async_generator():  # 에러!
        print(item)
```

### async for의 장점

`async for`는 I/O 대기 중에도 다른 코루틴을 실행할 수 있습니다:

```python
# ✅ 가능: async for는 await를 내부적으로 처리
async def async_example():
    async for item in async_generator():  # 정상 동작
        print(item)
    # I/O 대기 중에도 다른 작업 처리 가능
```

**실제 차이**:
- 동기 for: 각 항목을 기다리는 동안 블로킹됨
- async for: I/O 대기 중에도 다른 코루틴 실행 가능

자세한 비교는 `00-why-async-for.py` 예제를 실행해보세요.

## 기본 개념

### async for

`async for`는 비동기 이터레이터를 순회하는 문법입니다. 각 항목을 가져오는 동안 다른 코루틴이 실행될 수 있습니다.

```python
async for item in async_iterator:
    # item 처리
```

### AsyncIterator

`AsyncIterator`는 비동기적으로 데이터를 순회할 수 있는 객체입니다. `__aiter__()`와 `__anext__()` 메서드를 구현합니다.

### 비동기 제너레이터

`async def` 함수에서 `yield`를 사용하면 비동기 제너레이터가 됩니다. 이는 `AsyncIterator`를 반환합니다.

```python
async def async_generator():
    for i in range(5):
        await asyncio.sleep(0.1)
        yield i
```

## 파일 구조

1. **00-why-async-for.py**: async for를 왜 사용하는가? (비교 예제)
2. **01-basic-async-for.py**: 기본 async for 사용법
3. **02-async-iterator.py**: AsyncIterator 직접 구현 예제
4. **03-practical-example.py**: 실시간 STT 시스템 패턴 기반 예제 (Queue 기반)
5. **test_all.py**: 모든 예제를 실행하는 테스트 스크립트

## 실행 방법

### 개별 예제 실행

```bash
# 왜 async for를 사용하는가? (비교 예제)
python 00-why-async-for.py

# 기본 예제
python 01-basic-async-for.py

# AsyncIterator 구현 예제
python 02-async-iterator.py

# 실용적 예제
python 03-practical-example.py
```

### 모든 예제 일괄 실행

```bash
python test_all.py
```

## 예제 설명

### 00-why-async-for.py

동기 for와 async for의 차이를 실제로 보여주는 비교 예제입니다. async for를 왜 사용해야 하는지 명확히 이해할 수 있습니다.

**학습 포인트**:
- 동기 for의 한계 (await 사용 불가)
- async for의 장점 (I/O 대기 중 다른 작업 처리)
- 실제 성능 차이 비교
- 백그라운드 작업과의 동시 실행

**핵심 내용**:
- 동기 for는 비동기 제너레이터를 직접 사용할 수 없음
- async for는 I/O 대기 중에도 다른 코루틴 실행 가능
- 실시간 스트리밍, Queue 처리에 필수

### 01-basic-async-for.py

간단한 비동기 제너레이터를 만들고 `async for`로 순회하는 기본 예제입니다.

**학습 포인트**:
- 비동기 제너레이터 작성
- async for 문법
- 동기 for와의 차이점

### 02-async-iterator.py

`AsyncIterator`를 클래스로 직접 구현하는 예제입니다.

**학습 포인트**:
- `__aiter__()` 메서드 구현
- `__anext__()` 메서드 구현
- async for와 함께 사용

### 03-practical-example.py

실시간 STT 시스템에서 사용되는 Queue 기반 비동기 제너레이터 패턴을 구현한 예제입니다.

**학습 포인트**:
- asyncio.Queue와 비동기 제너레이터 조합
- 종료 신호 처리 (None)
- 실무에서 자주 사용되는 패턴

## 다음 단계

이 튜토리얼을 완료한 후:

1. 실시간 STT 시스템의 `AudioHandler.generate_chunks()` 구현을 확인하세요
2. `convert_stream_to_linear16()` 함수의 비동기 제너레이터 패턴을 학습하세요
3. 실제 프로젝트에서 비동기 이터레이터를 활용해보세요

