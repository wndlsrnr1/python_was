# FastAPI + Uvicorn 예제

## 실행 방법

### 방법 1: Uvicorn 직접 사용

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. Uvicorn으로 실행
uvicorn main:app --host 0.0.0.0 --port 8000

# 4. 브라우저에서 확인
# http://127.0.0.1:8000 접속
# http://127.0.0.1:8000/docs 접속 (자동 API 문서)
```

### 방법 2: Gunicorn + Uvicorn 워커

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. Gunicorn으로 실행 (Uvicorn 워커 사용)
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4

# 3. 브라우저에서 확인
# http://127.0.0.1:8000 접속
# http://127.0.0.1:8000/docs 접속 (자동 API 문서)
```

## API 테스트

```bash
# 루트 엔드포인트
curl http://127.0.0.1:8000/

# 아이템 조회
curl http://127.0.0.1:8000/items/123?q=test
```

