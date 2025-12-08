# 6장: FastAPI에서 사용하기 (uvicorn 포함)

## 6.1 FastAPI와 ASGI

FastAPI는 **ASGI 애플리케이션**입니다. 따라서 ASGI 서버가 필요합니다.

### Uvicorn이란?

**Uvicorn**은 ASGI 서버입니다. Gunicorn과의 관계:

- **Gunicorn**: WSGI 서버 (Django 등)
- **Uvicorn**: ASGI 서버 (FastAPI 등)
- **Gunicorn + Uvicorn 워커**: Gunicorn이 uvicorn 워커를 사용하여 ASGI 애플리케이션 실행

## 6.2 Uvicorn 직접 사용

### 설치

```bash
pip install uvicorn fastapi
```

### FastAPI 애플리케이션

`gunicorn/codes/04_fastapi_example/main.py`:

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

### Uvicorn 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

또는 리로드 모드:

```bash
uvicorn main:app --reload
```

## 6.3 Gunicorn + Uvicorn 워커

프로덕션 환경에서는 Gunicorn이 여러 uvicorn 워커를 관리하는 것이 좋습니다.

### 설치

```bash
pip install gunicorn uvicorn[standard] fastapi
```

### 실행

```bash
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4
```

### 구조 이해

```
Gunicorn (마스터 프로세스)
    ├─→ Uvicorn Worker 1 → FastAPI app
    ├─→ Uvicorn Worker 2 → FastAPI app
    ├─→ Uvicorn Worker 3 → FastAPI app
    └─→ Uvicorn Worker 4 → FastAPI app
```

각 워커는 독립적인 uvicorn 서버 인스턴스입니다.

## 6.4 WSGI vs ASGI 비교

| 특성 | WSGI | ASGI |
|------|------|------|
| **프로토콜** | 동기 | 비동기 |
| **WebSocket** | ❌ | ✅ |
| **HTTP/2** | 제한적 | ✅ |
| **사용 프레임워크** | Django (기본), Flask | FastAPI, Django Channels |
| **서버** | Gunicorn | Uvicorn (또는 Gunicorn + Uvicorn) |

### 언제 무엇을 사용할까?

- **WSGI (Gunicorn)**: Django, Flask 등 전통적인 동기 프레임워크
- **ASGI (Uvicorn)**: FastAPI, Django Channels 등 비동기 프레임워크

## 6.5 실전 예제

`gunicorn/codes/04_fastapi_example/` 디렉토리 구조:

```
04_fastapi_example/
├── main.py
└── requirements.txt
```

`requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
```

실행:

```bash
cd gunicorn/codes/04_fastapi_example
pip install -r requirements.txt
gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4
```

브라우저에서 `http://127.0.0.1:8000/docs` 접속하여 FastAPI 자동 문서를 확인할 수 있습니다.

## 6.6 다음 단계

이제 FastAPI에서 Gunicorn + Uvicorn을 사용하는 방법을 배웠습니다. 다음 단계:

1. **07_config.md**: 프로덕션 환경을 위한 고급 설정 방법 습득

---

**이전: [05_django.md](05_django.md) | 다음: [07_config.md](07_config.md) →**

