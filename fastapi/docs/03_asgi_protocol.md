# 3장: ASGI 프로토콜 이해

## 3.1 ASGI란?

**ASGI**(Asynchronous Server Gateway Interface)는 Python 웹 애플리케이션과 웹 서버 간의 **비동기 표준 인터페이스**입니다.

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

- **서블릿 스펙**: Java 웹 애플리케이션과 서버 간의 표준 인터페이스
- **WSGI**: Python 웹 애플리케이션과 서버 간의 동기 표준 인터페이스
- **ASGI**: Python 웹 애플리케이션과 서버 간의 **비동기** 표준 인터페이스

### WSGI vs ASGI

| 특성 | WSGI | ASGI |
|------|------|------|
| **동기/비동기** | 동기만 지원 | 비동기 지원 |
| **WebSocket** | 지원 안 함 | 지원 |
| **HTTP/2** | 제한적 | 완전 지원 |
| **백그라운드 작업** | 지원 안 함 | 지원 |
| **사용 프레임워크** | Django (기본), Flask | FastAPI, Django Channels |

### FastAPI와 ASGI

FastAPI는 **ASGI 애플리케이션**입니다. 즉, FastAPI 애플리케이션은 ASGI 프로토콜을 따르는 callable 객체입니다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello"}
```

이 `app` 객체는 ASGI callable입니다. Uvicorn은 이 객체를 호출하여 요청을 처리합니다.

## 3.2 ASGI Callable 규약

ASGI 애플리케이션은 다음 규약을 따라야 합니다:

1. **Callable 객체**: 함수 또는 `__call__` 메서드를 가진 클래스 인스턴스
2. **인자**: `scope` (연결 정보), `receive` (메시지 수신 함수), `send` (메시지 전송 함수)
3. **비동기**: `async def` 또는 `async __call__` 사용

### 최소한의 ASGI 애플리케이션 예제

FastAPI 없이 순수 ASGI 애플리케이션을 만들어보겠습니다:

```python
async def simple_app(scope, receive, send):
    """가장 간단한 ASGI 애플리케이션"""
    if scope['type'] == 'http':
        # HTTP 요청 처리
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello, ASGI!\n',
        })
```

이 애플리케이션을 uvicorn으로 실행하면:

```bash
uvicorn simple_app:simple_app
```

### FastAPI의 ASGI 애플리케이션

FastAPI는 내부적으로 ASGI 애플리케이션을 생성합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

이 `app` 객체는 ASGI callable입니다. Uvicorn은 다음과 같이 호출합니다:

```python
# Uvicorn 내부 (의사 코드)
await app(scope, receive, send)
```

## 3.3 ASGI 프로토콜의 구조

### Scope (연결 정보)

`scope`는 연결에 대한 정보를 담은 딕셔너리입니다:

```python
{
    'type': 'http',  # 또는 'websocket', 'lifespan'
    'method': 'GET',
    'path': '/',
    'headers': [(b'host', b'localhost:8000')],
    'query_string': b'',
    'client': ('127.0.0.1', 12345),
    'server': ('127.0.0.1', 8000),
    # ... 기타 정보
}
```

FastAPI는 이 `scope` 정보를 사용하여 라우팅을 수행합니다.

### Receive (메시지 수신)

`receive`는 클라이언트로부터 메시지를 받는 비동기 함수입니다:

```python
message = await receive()
# 예: {'type': 'http.request', 'body': b'...', 'more_body': False}
```

FastAPI는 이 함수를 사용하여 요청 본문을 읽습니다.

### Send (메시지 전송)

`send`는 클라이언트로 메시지를 보내는 비동기 함수입니다:

```python
await send({
    'type': 'http.response.start',
    'status': 200,
    'headers': [[b'content-type', b'text/html']],
})
```

FastAPI는 이 함수를 사용하여 응답을 전송합니다.

## 3.4 HTTP 요청 처리 흐름

### 순수 ASGI 애플리케이션 예제

```python
async def http_app(scope, receive, send):
    """HTTP 요청을 처리하는 ASGI 애플리케이션"""
    if scope['type'] != 'http':
        return
    
    # 요청 본문 읽기
    body = b''
    while True:
        message = await receive()
        if message['type'] == 'http.request':
            body += message.get('body', b'')
            if not message.get('more_body', False):
                break
    
    # 응답 전송
    response_body = f"Received: {body.decode()}".encode()
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': response_body,
    })
```

### FastAPI의 처리 흐름

FastAPI는 내부적으로 다음과 같이 처리합니다:

1. **Uvicorn이 요청 수신**: 클라이언트로부터 HTTP 요청을 받음
2. **ASGI 호출**: `await app(scope, receive, send)` 호출
3. **FastAPI 라우팅**: `scope`의 `path`와 `method`를 사용하여 적절한 엔드포인트 찾기
4. **요청 본문 읽기**: `receive()`를 사용하여 요청 본문 읽기
5. **엔드포인트 함수 실행**: 찾은 엔드포인트 함수 실행
6. **응답 생성**: 함수 반환값을 JSON으로 변환
7. **응답 전송**: `send()`를 사용하여 응답 전송

이 과정은 Spring의 DispatcherServlet과 유사합니다:

```
Spring:
요청 → DispatcherServlet → HandlerMapping → Controller → 응답

FastAPI:
요청 → Uvicorn → ASGI 호출 → FastAPI 라우팅 → 엔드포인트 함수 → 응답
```

## 3.5 요청 정보 활용 예제

순수 ASGI로 요청 정보를 반환하는 예제:

```python
async def info_app(scope, receive, send):
    """요청 정보를 반환하는 ASGI 애플리케이션"""
    if scope['type'] != 'http':
        return
    
    method = scope.get('method', 'GET')
    path = scope.get('path', '/')
    query_string = scope.get('query_string', b'').decode()
    
    info = f"""
    Method: {method}
    Path: {path}
    Query String: {query_string}
    """.strip()
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain; charset=utf-8']],
    })
    await send({
        'type': 'http.response.body',
        'body': info.encode('utf-8'),
    })
```

FastAPI에서는 이 정보를 자동으로 추출하여 엔드포인트 함수에 전달합니다:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, request: Request):
    # request 객체를 통해 scope 정보 접근 가능
    return {
        "item_id": item_id,
        "path": request.url.path,
        "method": request.method,
    }
```

## 3.6 WebSocket 지원

ASGI는 WebSocket도 지원합니다. FastAPI에서 WebSocket을 사용하는 예제:

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")
```

이것이 가능한 이유는 ASGI가 WebSocket을 지원하기 때문입니다.

## 3.7 서블릿 스펙과의 비교

### 서블릿 스펙 (Spring)

```java
@WebServlet("/hello")
public class HelloServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        resp.getWriter().println("Hello");
    }
}
```

### ASGI (FastAPI)

```python
async def hello_app(scope, receive, send):
    if scope['type'] == 'http' and scope['method'] == 'GET':
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello',
        })
```

**차이점**:
- **서블릿**: 동기 처리, 스레드 기반
- **ASGI**: 비동기 처리, 이벤트 루프 기반

## 3.8 다음 단계

이제 ASGI 프로토콜이 어떻게 동작하는지 이해했습니다. 다음 단계:

1. **04_architecture.md**: FastAPI 내부 구조와 요청 처리 흐름 이해
2. **05_routing.md**: 실제 API 엔드포인트 작성 방법 학습

---

**이전: [02_basic_setup.md](02_basic_setup.md) | 다음: [04_architecture.md](04_architecture.md) →**

