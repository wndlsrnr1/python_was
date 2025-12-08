# 5장: FastAPI에서 사용하기

## 5.1 FastAPI와 Uvicorn

FastAPI는 기본적으로 **ASGI 애플리케이션**입니다. 따라서 ASGI 서버인 Uvicorn이 필요합니다.

### FastAPI의 구조

```python
from fastapi import FastAPI

app = FastAPI()  # ASGI 애플리케이션
```

이 `app` 객체는 내부적으로 Starlette 프레임워크를 사용하여 ASGI 프로토콜을 구현합니다.

## 5.2 기본 FastAPI 프로젝트

### 프로젝트 구조

```
myproject/
├── main.py
├── requirements.txt
└── README.md
```

### main.py

`uvicorn/codes/03_fastapi_example/main.py`:

```python
from fastapi import FastAPI
from typing import Optional

app = FastAPI(title="My FastAPI App", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI with Uvicorn!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
def create_item(item: dict):
    return {"item": item}
```

### requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

### 실행

```bash
uvicorn main:app
```

## 5.3 자동 API 문서

FastAPI는 자동으로 OpenAPI 스펙을 생성하고 Swagger UI를 제공합니다.

### Swagger UI

브라우저에서 `http://127.0.0.1:8000/docs` 접속:

- 모든 엔드포인트 목록
- 각 엔드포인트의 파라미터와 응답 스키마
- 직접 API 테스트 가능

### ReDoc

브라우저에서 `http://127.0.0.1:8000/redoc` 접속:

- 더 읽기 쉬운 API 문서
- 스키마 상세 정보

### OpenAPI JSON

브라우저에서 `http://127.0.0.1:8000/openapi.json` 접속:

- OpenAPI 스펙 JSON
- 다른 도구에서 사용 가능

## 5.4 비동기 엔드포인트

FastAPI는 비동기 엔드포인트를 지원합니다.

### 동기 vs 비동기

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

# 동기 엔드포인트
@app.get("/sync")
def sync_endpoint():
    # 블로킹 작업
    response = httpx.get("http://api.example.com/data")
    return response.json()

# 비동기 엔드포인트
@app.get("/async")
async def async_endpoint():
    # 논블로킹 작업
    async with httpx.AsyncClient() as client:
        response = await client.get("http://api.example.com/data")
        return response.json()
```

**차이점**:
- 동기: `def` 사용, 블로킹 I/O
- 비동기: `async def` 사용, 논블로킹 I/O

### 비동기 데이터베이스 접근

```python
from fastapi import FastAPI
import asyncpg

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    conn = await asyncpg.connect("postgresql://...")
    user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    await conn.close()
    return dict(user)
```

## 5.5 의존성 주입

FastAPI는 강력한 의존성 주입 시스템을 제공합니다.

### 기본 예제

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_db():
    """데이터베이스 연결 의존성"""
    db = connect_db()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
def read_items(db = Depends(get_db)):
    return db.query("SELECT * FROM items")
```

### 공통 의존성

```python
from fastapi import FastAPI, Depends, Header

app = FastAPI()

async def verify_token(authorization: str = Header(...)):
    """토큰 검증 의존성"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    return authorization[7:]

@app.get("/protected")
def protected_route(token: str = Depends(verify_token)):
    return {"message": "Access granted"}
```

## 5.6 미들웨어

FastAPI는 Starlette의 미들웨어 시스템을 사용합니다.

### CORS 미들웨어

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 커스텀 미들웨어

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 5.7 WebSocket 지원

FastAPI는 WebSocket을 지원합니다 (ASGI의 장점).

### WebSocket 엔드포인트

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

### WebSocket 테스트

브라우저 콘솔에서:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (event) => console.log(event.data);
ws.send("Hello, WebSocket!");
```

## 5.8 프로덕션 실행

### 개발 모드

```bash
uvicorn main:app --reload
```

### 프로덕션 모드

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Gunicorn + Uvicorn (권장)

프로덕션 환경에서는 Gunicorn이 여러 Uvicorn 워커를 관리하는 것이 좋습니다:

```bash
pip install gunicorn

gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

자세한 내용은 07_config.md에서 다룹니다.

## 5.9 실전 예제

`uvicorn/codes/03_fastapi_example/` 디렉토리에 완전한 예제가 있습니다:

- `main.py`: 기본 FastAPI 애플리케이션
- `requirements.txt`: 의존성 목록
- `README.md`: 실행 방법

### 실행

```bash
cd uvicorn/codes/03_fastapi_example
pip install -r requirements.txt
uvicorn main:app --reload
```

브라우저에서:
- `http://127.0.0.1:8000` - API 엔드포인트
- `http://127.0.0.1:8000/docs` - Swagger UI
- `http://127.0.0.1:8000/redoc` - ReDoc

## 5.10 다음 단계

이제 FastAPI에서 uvicorn을 사용하는 방법을 배웠습니다. 다음 단계:

1. **06_django.md**: Django에서 ASGI 모드로 사용하기
2. **07_config.md**: 프로덕션 환경 설정

---

**이전: [04_architecture.md](04_architecture.md) | 다음: [06_django.md](06_django.md) →**

