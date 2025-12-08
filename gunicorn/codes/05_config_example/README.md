# 설정 파일 예제

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Gunicorn 설치
pip install gunicorn

# 3. 설정 파일로 실행
gunicorn app:application -c gunicorn.conf.py

# 4. 브라우저에서 확인
# http://127.0.0.1:8000 접속
```

## 설정 파일 수정

`gunicorn.conf.py` 파일을 수정하여 다양한 옵션을 테스트해보세요:

- 워커 수 변경: `workers = 8`
- 포트 변경: `bind = "0.0.0.0:8080"`
- 워커 타입 변경: `worker_class = "gevent"` (gevent 설치 필요)

## 환경변수 사용 (선택)

```bash
# python-dotenv 설치
pip install python-dotenv

# .env 파일 생성 (예시)
echo "GUNICORN_BIND=0.0.0.0:8000" > .env
echo "GUNICORN_WORKERS=4" >> .env

# gunicorn.conf.py에서 환경변수 로드하도록 수정 필요
```

