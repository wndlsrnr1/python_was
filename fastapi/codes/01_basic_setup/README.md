# 기본 설치 및 실행 예제

## 실행 방법

1. 가상환경 활성화 (선택사항)

```bash
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

2. 필요한 패키지 설치

```bash
pip install fastapi "uvicorn[standard]"
```

3. 서버 실행

```bash
uvicorn main:app --reload
```

4. 브라우저에서 확인

- 기본 엔드포인트: http://127.0.0.1:8000
- API 문서 (Swagger): http://127.0.0.1:8000/docs
- API 문서 (ReDoc): http://127.0.0.1:8000/redoc
- 경로 파라미터 예제: http://127.0.0.1:8000/items/42
- 쿼리 파라미터 예제: http://127.0.0.1:8000/items/42?q=test

## 코드 설명

- `main.py`: 기본 FastAPI 애플리케이션
  - `/`: 루트 엔드포인트
  - `/items/{item_id}`: 경로 파라미터와 쿼리 파라미터 사용 예제

