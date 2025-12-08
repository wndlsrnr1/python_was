# FastAPI + Uvicorn 예제

## 실행 방법

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn main:app --reload

# 프로덕션 모드
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. API 테스트

브라우저에서:
- `http://127.0.0.1:8000` - 루트 엔드포인트
- `http://127.0.0.1:8000/docs` - Swagger UI (자동 API 문서)
- `http://127.0.0.1:8000/redoc` - ReDoc (대체 문서)
- `http://127.0.0.1:8000/openapi.json` - OpenAPI 스펙

### 5. curl로 테스트

```bash
# GET 요청
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/items/123?q=test

# POST 요청
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "item1", "price": 100}'
```

## 프로덕션 실행 (Gunicorn + Uvicorn)

```bash
pip install gunicorn

gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

