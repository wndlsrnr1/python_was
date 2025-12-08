# 워커 동작 확인 예제

## 실행 방법

```bash
# 1. Gunicorn 설치
pip install gunicorn

# 2. 4개의 워커로 실행
gunicorn app:application --workers 4

# 3. 다른 터미널에서 동시에 여러 요청 보내기
curl http://127.0.0.1:8000
curl http://127.0.0.1:8000
curl http://127.0.0.1:8000
curl http://127.0.0.1:8000
```

## 프로세스 확인

```bash
# 다른 터미널에서 실행
ps aux | grep gunicorn
```

각 요청이 다른 PID를 반환하면 워커가 제대로 분산되고 있음을 확인할 수 있습니다.

