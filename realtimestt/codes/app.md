# Python async vs JavaSCript 비교

## 핵심 개념

세 언어 모두 비동기로 I/O 대기 중 다른 작업을 처리한다. 구현방식은 다르다.

1. 문법비교

javascript (Promise 기반)

```javascript

// 비동기로 요청을 보내고 받는 과정
async function fetchData(){
    const response awiat fetch(`/api/data`);
    const data = await response.json();
    return data;
}
```

Java (CompletableFuture)

```java

//CompletableFuture 체이닝
CompletableFuture<String> fetchData() {
    return CompletableFuture
        .supplyAysnc(()->fetch("/api/data"))
        .thenApply(response -> parseJson(response));
}

```

```python


async def fetch_data():
    response = await fetch("/api/data")
    data = await response.json()
    return data

# 비교 Python과 Javasscript는 문법이 거의 동일합니다. Java는 chianning 방식입니다.

```

## 실행 모델 차이

Javascript

- 단일 스레드 이벤트 루프
- 비동기 작업은 백그라운드에서 처리 후 콜백 큐로 복귀'
- 병렬 처리: Web Workers 사용

Java

- 멀티 스레드 기반
- CompletableFuture는 스레드 풀에서 실행
- 실제 병렬 처리 가능

Python

- 단일 스레드 이벤트 루프 (asyncio)
- 코루틴이 협렵적으로 실행
- I/O 대기 중에만 다른 코루틴 실행

## 실제 사용 예시

현재 코드 기준:

```python
async def connect(self):
    awiat self.accept() # I/O 대기 중 다른 작업 처리 가능

```

```javascript
async function connect() {
    awiat this.accept(); // 동일한 문법
    // ... 초기화 로직
}
```

```Java

public CompletableFuture<Void> connect() {
    return accept()
        .thenRun(() -> {
            //... 초기화 로직
        });
}
```

Python async의 특징

- 장점: Javascript와 유사한 문법 I/O 대기 시 효율적
- 단점: CPU 직약 작업에는 부적합 (GIL 제약)
- 적합한 경우: Websocket, HTTP 요청, DB 쿼리 등 I/O 대기 작업

현재 웹소켓 코드 처럼 I/O 대기 시간이 긴 경우에 적합합니다.
