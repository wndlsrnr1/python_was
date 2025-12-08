# 기본 설치 및 실행 예제

## 실행 방법

### 1. 가상환경 생성 및 활성화 (선택사항)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Uvicorn 및 FastAPI 설치

```bash
pip install uvicorn[standard] fastapi
```

### 3. 순수 ASGI 애플리케이션 실행

```bash
uvicorn app:application
```

브라우저에서 `http://127.0.0.1:8000` 접속

### 4. FastAPI 애플리케이션 실행

```bash
uvicorn main:app
```

브라우저에서:
- `http://127.0.0.1:8000` - API 엔드포인트
- `http://127.0.0.1:8000/docs` - Swagger UI 문서
- `http://127.0.0.1:8000/redoc` - ReDoc 문서

## 다양한 실행 옵션

```bash
# 포트 변경
uvicorn main:app --port 8080

# 호스트 변경 (모든 인터페이스)
uvicorn main:app --host 0.0.0.0

# 자동 리로드 (개발 모드)
uvicorn main:app --reload

# 로그 레벨 설정
uvicorn main:app --log-level debug
```

