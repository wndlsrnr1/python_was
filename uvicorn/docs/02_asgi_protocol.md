# 2장: ASGI 프로토콜 이해

## 2.1 ASGI란?

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

## 2.2 ASGI Callable 규약

ASGI 애플리케이션은 다음 규약을 따라야 합니다:

1. **Callable 객체**: 함수 또는 `__call__` 메서드를 가진 클래스 인스턴스
2. **인자**: `scope` (연결 정보), `receive` (메시지 수신 함수), `send` (메시지 전송 함수)
3. **비동기**: `async def` 또는 `async __call__` 사용

### 최소한의 ASGI 애플리케이션 예제

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

이 `app` 객체는 ASGI callable입니다. Uvicorn은 이 객체를 호출하여 요청을 처리합니다.

## 2.3 ASGI 프로토콜의 구조

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

### Receive (메시지 수신)

`receive`는 클라이언트로부터 메시지를 받는 비동기 함수입니다:

```python
message = await receive()
# 예: {'type': 'http.request', 'body': b'...', 'more_body': False}
```

### Send (메시지 전송)

`send`는 클라이언트로 메시지를 보내는 비동기 함수입니다:

```python
await send({
    'type': 'http.response.start',
    'status': 200,
    'headers': [[b'content-type', b'text/html']],
})
```

## 2.4 HTTP 요청 처리 예제

### 기본 HTTP 애플리케이션

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

### 요청 정보 활용

```python
async def info_app(scope, receive, send):
    """요청 정보를 반환하는 ASGI 애플리케이션"""
    if scope['type'] != 'http':
        return
    
    method = scope['method']
    path = scope['path']
    headers = dict(scope['headers'])
    
    info = f"""
    Method: {method}
    Path: {path}
    Headers: {headers}
    """.encode()
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/plain']],
    })
    await send({
        'type': 'http.response.body',
        'body': info,
    })
```

## 2.5 WebSocket 지원

ASGI의 주요 장점 중 하나는 **WebSocket 지원**입니다.

### WebSocket 애플리케이션 예제

```python
async def websocket_app(scope, receive, send):
    """WebSocket 연결을 처리하는 ASGI 애플리케이션"""
    if scope['type'] != 'websocket':
        return
    
    # WebSocket 연결 수락
    await send({'type': 'websocket.accept'})
    
    # 메시지 수신 및 에코
    while True:
        message = await receive()
        if message['type'] == 'websocket.receive':
            text = message.get('text', '')
            await send({
                'type': 'websocket.send',
                'text': f"Echo: {text}",
            })
        elif message['type'] == 'websocket.disconnect':
            break
```

이것이 ASGI가 WSGI보다 강력한 이유 중 하나입니다. WSGI는 WebSocket을 지원하지 않습니다.

## 2.6 WSGI와의 차이점

### WSGI (동기)

```python
def wsgi_app(environ, start_response):
    """WSGI 애플리케이션 (동기)"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello, WSGI!\n']
```

**특징**:
- 동기 함수
- `environ` 딕셔너리로 요청 정보 전달
- `start_response` 콜백으로 응답 시작
- 바이트 이터러블로 응답 반환

### ASGI (비동기)

```python
async def asgi_app(scope, receive, send):
    """ASGI 애플리케이션 (비동기)"""
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

**특징**:
- 비동기 함수 (`async def`)
- `scope`로 연결 정보 전달
- `receive`/`send`로 메시지 기반 통신
- WebSocket, HTTP/2 등 지원

## 2.7 Django의 ASGI 설정

Django는 기본적으로 WSGI를 사용하지만, ASGI 모드도 지원합니다.

### asgi.py 파일

Django 프로젝트를 생성하면 `myproject/asgi.py` 파일이 자동 생성됩니다:

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_asgi_application()
```

이 `application` 객체가 ASGI callable입니다. Uvicorn은 이 객체를 호출하여 요청을 처리합니다.

### 실행

```bash
uvicorn myproject.asgi:application
```

## 2.8 FastAPI의 ASGI 애플리케이션

FastAPI는 기본적으로 ASGI를 사용합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

이 `app` 객체는 ASGI callable입니다. 내부적으로 Starlette 프레임워크를 사용하여 ASGI 프로토콜을 구현합니다.

### 실행

```bash
uvicorn main:app
```

## 2.9 다음 단계

이제 ASGI 프로토콜이 어떻게 동작하는지 이해했습니다. 다음 단계:

1. **03_basic_setup.md**: 실제로 uvicorn을 설치하고 실행해보기

---

**이전: [01_overview.md](01_overview.md) | 다음: [03_basic_setup.md](03_basic_setup.md) →**

