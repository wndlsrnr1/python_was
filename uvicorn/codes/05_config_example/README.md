# 설정 파일 예제

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

### 3. Gunicorn + Uvicorn으로 실행

```bash
gunicorn main:app -c gunicorn.conf.py
```

### 4. 직접 옵션으로 실행

```bash
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

## 설정 파일 수정

`gunicorn.conf.py` 파일을 수정하여 다양한 옵션을 테스트해보세요:

- 워커 수 변경: `workers = 8`
- 포트 변경: `bind = "0.0.0.0:8080"`
- 로그 레벨 변경: `loglevel = "debug"`

## 프로세스 확인

```bash
ps aux | grep gunicorn
```

여러 워커 프로세스가 실행되는 것을 확인할 수 있습니다.

