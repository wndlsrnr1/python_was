# 서버 설정 예제

## Uvicorn 단독 실행 (개발 환경)

```bash
uvicorn main:app --reload
```

## Gunicorn + Uvicorn 실행 (프로덕션 환경)

### 명령줄 옵션 사용

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 설정 파일 사용

```bash
gunicorn main:app -c gunicorn.conf.py
```

## 테스트

```bash
# 기본 엔드포인트
curl http://127.0.0.1:8000/

# 헬스 체크
curl http://127.0.0.1:8000/health
```

## 워커 수 조정

워커 수는 시스템 리소스에 맞게 조정하세요:

- **개발 환경**: 1-2 워커
- **소규모 프로덕션**: 2-4 워커
- **대규모 프로덕션**: 4-8 워커 (CPU 코어 수에 따라)

## 로그 확인

설정 파일에서 지정한 로그 파일을 확인하세요:

```bash
tail -f access.log
tail -f error.log
```

