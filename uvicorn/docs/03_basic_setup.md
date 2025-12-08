# 3장: 기본 설치 및 실행

## 3.1 설치

### 가상환경 설정 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### Uvicorn 설치

```bash
pip install uvicorn
```

또는 표준 라이브러리 포함 설치 (권장):

```bash
pip install "uvicorn[standard]"
```

`[standard]` 옵션은 다음을 포함합니다:
- `httptools`: 빠른 HTTP 파싱
- `uvloop`: 빠른 이벤트 루프 (Linux/Mac)
- `websockets`: WebSocket 지원
- `watchfiles`: 자동 리로드

설치 확인:

```bash
uvicorn --version
```

## 3.2 최소한의 ASGI 애플리케이션 만들기

`uvicorn/codes/01_basic_setup/app.py` 파일을 생성합니다:

```python
async def application(scope, receive, send):
    """최소한의 ASGI 애플리케이션"""
    if scope['type'] != 'http':
        return
    
    # 요청 정보 추출
    method = scope.get('method', 'GET')
    path = scope.get('path', '/')
    
    # 응답 생성
    body = f"""
    <html>
    <head><title>Uvicorn 테스트</title></head>
    <body>
        <h1>Uvicorn이 정상 작동합니다!</h1>
        <p>요청 메서드: {method}</p>
        <p>요청 경로: {path}</p>
    </body>
    </html>
    """.encode('utf-8')
    
    # 응답 전송
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/html; charset=utf-8']],
    })
    await send({
        'type': 'http.response.body',
        'body': body,
    })
```

## 3.3 실행

### 기본 실행

```bash
cd uvicorn/codes/01_basic_setup
uvicorn app:application
```

출력 예시:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 브라우저에서 확인

브라우저에서 `http://127.0.0.1:8000` 접속하면 HTML 페이지가 표시됩니다.

### 포트 변경

```bash
uvicorn app:application --port 8080
```

### 호스트 변경

```bash
uvicorn app:application --host 0.0.0.0
```

모든 네트워크 인터페이스에서 접근 가능합니다.

## 3.4 FastAPI 예제 실행

FastAPI를 사용하는 것이 더 일반적입니다.

### FastAPI 설치

```bash
pip install fastapi
```

### FastAPI 애플리케이션

`uvicorn/codes/01_basic_setup/main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI with Uvicorn!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

### 실행

```bash
uvicorn main:app
```

여기서 `main:app`은:
- `main`: `main.py` 모듈
- `app`: 해당 모듈의 `app` 변수 (FastAPI 인스턴스)

### 자동 API 문서 확인

FastAPI는 자동으로 API 문서를 생성합니다:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 3.5 자동 리로드 (개발 모드)

개발 중에는 코드 변경 시 자동으로 서버를 재시작하는 것이 편리합니다:

```bash
uvicorn main:app --reload
```

**주의**: 프로덕션 환경에서는 `--reload` 옵션을 사용하지 마세요.

## 3.6 다양한 실행 옵션

### 로그 레벨 설정

```bash
uvicorn main:app --log-level debug
```

로그 레벨: `critical`, `error`, `warning`, `info`, `debug`, `trace`

### 워커 수 지정

```bash
uvicorn main:app --workers 4
```

**주의**: Uvicorn은 기본적으로 단일 프로세스로 실행됩니다. 여러 워커를 사용하려면 Gunicorn과 함께 사용하는 것이 권장됩니다 (07_config.md 참조).

### 타임아웃 설정

```bash
uvicorn main:app --timeout-keep-alive 5
```

Keep-Alive 연결 유지 시간을 5초로 설정합니다.

## 3.7 Django 예제 실행

Django 프로젝트가 있다면:

```bash
uvicorn myproject.asgi:application
```

여기서 `myproject.asgi:application`은:
- `myproject.asgi`: `myproject/asgi.py` 모듈
- `application`: 해당 모듈의 `application` 변수 (ASGI callable)

Django ASGI 설정은 06_django.md에서 자세히 다룹니다.

## 3.8 종료

터미널에서 `Ctrl+C`를 누르면 uvicorn이 종료됩니다.

## 3.9 실습 예제

`uvicorn/codes/01_basic_setup/` 디렉토리에 다음 파일들이 있습니다:

- `app.py`: 순수 ASGI 애플리케이션
- `main.py`: FastAPI 애플리케이션
- `README.md`: 실행 방법 안내

각 파일을 실행해보며 차이점을 확인해보세요.

## 3.10 다음 단계

이제 uvicorn을 설치하고 실행하는 방법을 배웠습니다. 다음 단계:

1. **04_architecture.md**: uvicorn의 내부 구조와 비동기 처리 원리 이해

---

**이전: [02_asgi_protocol.md](02_asgi_protocol.md) | 다음: [04_architecture.md](04_architecture.md) →**

