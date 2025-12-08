# 비동기 동작 시각화 예제

## 실행 방법

### 1. 서버 실행

```bash
# 가상환경 활성화 (선택사항)
source venv/bin/activate

# 패키지 설치
pip install fastapi uvicorn[standard] aiohttp

# 서버 실행
uvicorn app:app
```

### 2. 동시성 테스트

다른 터미널에서:

```bash
# 동시 요청 테스트
python concurrent_test.py
```

**예상 결과**: 10개 요청이 약 1초 내에 처리됩니다 (순차 처리라면 10초).

### 3. 수동 테스트

브라우저나 curl로 테스트:

```bash
# 동기 엔드포인트 (블로킹)
curl http://127.0.0.1:8000/sync

# 비동기 엔드포인트 (논블로킹)
curl http://127.0.0.1:8000/async

# 지연 엔드포인트
curl http://127.0.0.1:8000/delay/2
```

## 학습 포인트

- **동기 vs 비동기**: `time.sleep()` vs `asyncio.sleep()`의 차이
- **동시성**: 여러 요청이 동시에 처리되는 방식
- **이벤트 루프**: I/O 대기 중에도 다른 작업 처리 가능

