# 4장: 아키텍처 및 동작 원리

## 4.1 이벤트 루프 기반 아키텍처

Uvicorn은 **이벤트 루프(Event Loop)** 기반으로 동작합니다.

### 이벤트 루프란?

이벤트 루프는 다음과 같이 동작합니다:

1. **이벤트 대기**: 네트워크 I/O, 파일 I/O 등의 이벤트를 대기
2. **이벤트 처리**: 이벤트가 발생하면 해당 핸들러 실행
3. **비동기 작업**: I/O 대기 중에도 다른 작업 처리 가능
4. **반복**: 계속 반복하여 이벤트 처리

### Spring/Tomcat과의 비교

| 특성 | Spring/Tomcat | Uvicorn |
|------|--------------|---------|
| **동시성 모델** | 스레드 풀 | 이벤트 루프 |
| **I/O 처리** | 블로킹 I/O | 비동기 I/O |
| **컨텍스트 스위칭** | OS 스레드 스위칭 | 사용자 공간 스위칭 |
| **메모리 사용** | 스레드당 스택 메모리 | 단일 프로세스 |

**핵심 차이**: Tomcat은 여러 스레드가 각각 요청을 처리하고, Uvicorn은 단일 이벤트 루프가 여러 요청을 비동기로 처리합니다.

## 4.2 비동기 I/O 처리

### 동기 I/O의 문제

전통적인 동기 I/O 방식:

```python
# 동기 방식 (블로킹)
def handle_request():
    data = db.query()  # 1초 대기 (블로킹)
    result = api.call()  # 2초 대기 (블로킹)
    return result  # 총 3초 소요
```

**문제점**: I/O 대기 중에는 CPU가 놀고 있습니다.

### 비동기 I/O의 해결

비동기 I/O 방식:

```python
# 비동기 방식 (논블로킹)
async def handle_request():
    data = await db.query()  # 1초 대기 (다른 작업 가능)
    result = await api.call()  # 2초 대기 (다른 작업 가능)
    return result  # 총 3초지만 동시에 여러 요청 처리
```

**장점**: I/O 대기 중에도 다른 요청을 처리할 수 있습니다.

### 실제 동작 예제

`uvicorn/codes/02_async_demo/app.py`:

```python
import asyncio
import time
from fastapi import FastAPI

app = FastAPI()

@app.get("/sync")
def sync_endpoint():
    """동기 엔드포인트 (시뮬레이션)"""
    time.sleep(1)  # 1초 대기 (블로킹)
    return {"message": "Sync response"}

@app.get("/async")
async def async_endpoint():
    """비동기 엔드포인트"""
    await asyncio.sleep(1)  # 1초 대기 (논블로킹)
    return {"message": "Async response"}
```

**차이점**:
- `sync_endpoint`: `time.sleep()`은 스레드를 블로킹합니다
- `async_endpoint`: `asyncio.sleep()`은 이벤트 루프를 블로킹하지 않습니다

## 4.3 Uvicorn의 내부 구조

### 프로세스 구조

Uvicorn은 기본적으로 **단일 프로세스**로 실행됩니다:

```
Uvicorn 프로세스
    ├─→ 이벤트 루프 (메인 스레드)
    │     ├─→ HTTP 연결 1 처리
    │     ├─→ HTTP 연결 2 처리
    │     ├─→ HTTP 연결 3 처리
    │     └─→ ...
    └─→ 워커 스레드 (선택적)
```

### Gunicorn과의 비교

| 특성 | Gunicorn | Uvicorn |
|------|----------|---------|
| **프로세스 모델** | 마스터-워커 (멀티 프로세스) | 단일 프로세스 |
| **동시성** | 워커 수에 비례 | 이벤트 루프 기반 (높은 동시성) |
| **메모리 사용** | 프로세스당 독립 메모리 | 단일 프로세스 공유 메모리 |
| **CPU 활용** | 멀티 코어 활용 가능 | 단일 코어 (GIL 제약) |

### Gunicorn + Uvicorn 조합

프로덕션 환경에서는 Gunicorn이 여러 Uvicorn 워커를 관리하는 것이 권장됩니다:

```
Gunicorn (마스터 프로세스)
    ├─→ Uvicorn Worker 1 (이벤트 루프)
    ├─→ Uvicorn Worker 2 (이벤트 루프)
    ├─→ Uvicorn Worker 3 (이벤트 루프)
    └─→ Uvicorn Worker 4 (이벤트 루프)
```

이렇게 하면:
- 멀티 코어 활용 가능
- 프로세스 격리로 안정성 향상
- 높은 동시성 처리

자세한 내용은 07_config.md에서 다룹니다.

## 4.4 이벤트 루프 구현체

Uvicorn은 여러 이벤트 루프 구현체를 지원합니다:

### asyncio (기본)

Python 표준 라이브러리의 이벤트 루프:

```bash
uvicorn main:app  # asyncio 사용
```

### uvloop (권장, Linux/Mac)

C로 작성된 고성능 이벤트 루프:

```bash
pip install uvloop
uvicorn main:app  # 자동으로 uvloop 사용 (설치 시)
```

**성능**: asyncio보다 약 2-4배 빠릅니다.

### 선택 방법

`uvicorn[standard]`를 설치하면 자동으로 최적의 이벤트 루프를 선택합니다.

## 4.5 동시성 처리 실습

### 동시 요청 처리 확인

`uvicorn/codes/02_async_demo/concurrent_test.py`:

```python
import asyncio
import aiohttp
import time

async def fetch(session, url):
    """비동기 HTTP 요청"""
    async with session.get(url) as response:
        return await response.json()

async def main():
    """동시 요청 테스트"""
    url = "http://127.0.0.1:8000/async"
    
    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for _ in range(10)]
        results = await asyncio.gather(*tasks)
    end = time.time()
    
    print(f"10개 요청 처리 시간: {end - start:.2f}초")
    print(f"결과: {results}")

if __name__ == "__main__":
    asyncio.run(main())
```

**실행 방법**:

1. 서버 실행:
```bash
uvicorn app:app
```

2. 다른 터미널에서 테스트:
```bash
python concurrent_test.py
```

**예상 결과**: 10개 요청이 약 1초 내에 처리됩니다 (순차 처리라면 10초).

## 4.6 Spring의 비동기 처리와 비교

### Spring WebFlux (리액티브)

Spring의 비동기 프레임워크:

```java
@GetMapping("/async")
public Mono<String> async() {
    return webClient.get()
        .uri("/api/data")
        .retrieve()
        .bodyToMono(String.class);
}
```

**특징**: 리액티브 스트림 기반, 논블로킹 I/O

### FastAPI (비동기)

FastAPI의 비동기 처리:

```python
@app.get("/async")
async def async_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api/data")
        return response.json()
```

**특징**: async/await 기반, 이벤트 루프

**공통점**: 둘 다 비동기 I/O를 사용하지만, Spring은 리액티브 스트림을, FastAPI는 async/await를 사용합니다.

## 4.7 성능 특성

### I/O 집약적 작업

| 작업 유형 | 동기 처리 | 비동기 처리 |
|----------|----------|-----------|
| **DB 쿼리** | 블로킹 | 논블로킹 |
| **API 호출** | 블로킹 | 논블로킹 |
| **파일 I/O** | 블로킹 | 논블로킹 |

**결론**: I/O 집약적 작업에서는 비동기가 훨씬 효율적입니다.

### CPU 집약적 작업

| 작업 유형 | 동기 처리 | 비동기 처리 |
|----------|----------|-----------|
| **계산 작업** | 효율적 | GIL 제약 |
| **이미지 처리** | 효율적 | GIL 제약 |

**결론**: CPU 집약적 작업에서는 동기 처리가 더 효율적일 수 있습니다.

### 하이브리드 접근

실제 애플리케이션에서는:

- **I/O 작업**: 비동기 처리
- **CPU 작업**: 별도 스레드 풀에서 처리

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def cpu_intensive_task():
    """CPU 집약적 작업을 스레드 풀에서 실행"""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        heavy_computation  # CPU 집약적 함수
    )
    return result
```

## 4.8 다음 단계

이제 uvicorn의 아키텍처와 비동기 처리 원리를 이해했습니다. 다음 단계:

1. **05_fastapi.md**: FastAPI에서 실제로 사용하기
2. **06_django.md**: Django에서 ASGI 모드로 사용하기

---

**이전: [03_basic_setup.md](03_basic_setup.md) | 다음: [05_fastapi.md](05_fastapi.md) →**

