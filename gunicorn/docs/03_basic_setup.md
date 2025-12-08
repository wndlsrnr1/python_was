# 3장: 기본 설치 및 실행

## 3.1 설치

### 가상환경 설정 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### Gunicorn 설치

```bash
pip install gunicorn
```

설치 확인:

```bash
gunicorn --version
```

## 3.2 최소한의 WSGI 애플리케이션 만들기

`gunicorn/codes/01_basic_setup/app.py` 파일을 생성합니다:

```python
def application(environ, start_response):
    """최소한의 WSGI 애플리케이션"""
    status = '200 OK'
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
    ]
    start_response(status, headers)
    
    # 요청 정보 출력
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    
    body = f"""
    <html>
    <head><title>Gunicorn 테스트</title></head>
    <body>
        <h1>Gunicorn이 정상 작동합니다!</h1>
        <p>요청 메서드: {method}</p>
        <p>요청 경로: {path}</p>
    </body>
    </html>
    """.encode('utf-8')
    
    return [body]
```

## 3.3 실행

### 기본 실행

```bash
cd gunicorn/codes/01_basic_setup
gunicorn app:application
```

출력 예시:

```
[2024-01-01 10:00:00 +0900] [12345] [INFO] Starting gunicorn 21.2.0
[2024-01-01 10:00:00 +0900] [12345] [INFO] Listening at: http://127.0.0.1:8000 (12345)
[2024-01-01 10:00:00 +0900] [12345] [INFO] Using worker: sync
[2024-01-01 10:00:00 +0900] [12346] [INFO] Booting worker with pid: 12346
```

### 브라우저에서 확인

브라우저에서 `http://127.0.0.1:8000` 접속하면 HTML 페이지가 표시됩니다.

### 포트 변경

```bash
gunicorn app:application --bind 0.0.0.0:8080
```

### 워커 수 지정

```bash
gunicorn app:application --workers 4
```

## 3.4 Django 예제 실행

Django 프로젝트가 있다면:

```bash
gunicorn myproject.wsgi:application
```

여기서 `myproject.wsgi:application`은:
- `myproject.wsgi`: `myproject/wsgi.py` 모듈
- `application`: 해당 모듈의 `application` 변수 (WSGI callable)

## 3.5 종료

터미널에서 `Ctrl+C`를 누르면 gunicorn이 종료됩니다.

## 3.6 실습 예제

`gunicorn/codes/01_basic_setup/` 디렉토리에 다음 파일들이 있습니다:

- `app.py`: 순수 WSGI 애플리케이션
- `README.md`: 실행 방법 안내

각 파일을 실행해보며 차이점을 확인해보세요.

## 3.7 다음 단계

이제 gunicorn을 설치하고 실행하는 방법을 배웠습니다. 다음 단계:

1. **04_worker_model.md**: 프로세스 모델과 워커를 통한 내부 동작 원리 이해

---

**이전: [02_wsgi_asgi_protocol.md](02_wsgi_asgi_protocol.md) | 다음: [04_worker_model.md](04_worker_model.md) →**

