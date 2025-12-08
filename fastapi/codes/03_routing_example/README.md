# 라우팅 예제

## 실행 방법

```bash
uvicorn main:app --reload
```

## 테스트

### GET: 경로 파라미터
```bash
curl http://127.0.0.1:8000/items/42
```

### GET: 쿼리 파라미터
```bash
curl "http://127.0.0.1:8000/items/?skip=20&limit=5&q=test"
```

### POST: Request Body
```bash
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "price": 9.99, "quantity": 10}'
```

### PUT: 경로 파라미터 + Request Body
```bash
curl -X PUT http://127.0.0.1:8000/items/42 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item", "price": 19.99, "quantity": 5}'
```

### DELETE: 경로 파라미터
```bash
curl -X DELETE http://127.0.0.1:8000/items/42
```

### Response 모델
```bash
curl http://127.0.0.1:8000/items/42/detail
```

## API 문서

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

