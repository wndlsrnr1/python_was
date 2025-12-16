# 기본 설치 및 실행 예제

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Gunicorn 설치
pip install gunicorn

# 3. 실행
gunicorn app:application

# 4. 브라우저에서 확인
# http://127.0.0.1:8000 접속
```

## 다양한 실행 옵션

```bash
# 포트 변경
gunicorn app:application --bind 0.0.0.0:8080

# 워커 수 지정
gunicorn app:application --workers 4

# 로그 출력
gunicorn app:application --access-logfile - --error-logfile -
```

