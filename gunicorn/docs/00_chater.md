# Gunicorn 교과서: Python 웹 서버 완전 정복

> **대상 독자**: Spring/Tomcat 경험자  
> **학습 목표**: Django/FastAPI에서 gunicorn을 사용하는 방법과 동작 원리를 완전히 이해하기  
> **학습 방식**: 이론 → 실습 → 심화 순서로 따라하며 학습

---

## 📚 목차 및 학습 로드맵

### 전체 구조

```
1. 개요 및 왜 필요한가
   └─→ 2. WSGI/ASGI 프로토콜 이해
         └─→ 3. 기본 설치 및 실행
               └─→ 4. 프로세스 모델 및 워커 이해
                     ├─→ 5. Django에서 사용하기
                     │     └─→ 6. FastAPI에서 사용하기
                     │           └─→ 7. 설정 파일 및 고급 옵션
                     │                 └─→ 8. Spring/Tomcat과의 비교 정리
```

### 각 챕터 학습 목표

- **1장**: gunicorn이 무엇인지, 왜 필요한지 직관적 이해
- **2장**: WSGI/ASGI 프로토콜을 통한 애플리케이션-서버 통신 방식 이해
- **3장**: 실제로 설치하고 실행해보며 기본 사용법 습득
- **4장**: 프로세스 모델과 워커를 통한 내부 동작 원리 이해
- **5장**: Django 프로젝트에서 실전 적용
- **6장**: FastAPI에서 ASGI 서버(uvicorn) 사용법 이해
- **7장**: 프로덕션 환경을 위한 고급 설정 방법 습득
- **8장**: Spring/Tomcat과의 비교를 통한 통합적 이해

---

# 1장: 개요 및 왜 필요한가

## 1.1 Gunicorn이란?

**Gunicorn**(Green Unicorn)은 Python 웹 애플리케이션을 실행하기 위한 **WSGI HTTP 서버**입니다.

### Spring/Tomcat과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring/Tomcat | Python/Gunicorn |
|--------------|-----------------|
| Tomcat (서블릿 컨테이너) | Gunicorn (WSGI 서버) |
| WAR 파일 배포 | Python 모듈/패키지 배포 |
| `server.xml` 설정 | `gunicorn.conf.py` 설정 |
| 스레드 풀 모델 | 프로세스 기반 워커 모델 |

**핵심 차이점**: Tomcat은 Java 서블릿을 실행하는 컨테이너이고, Gunicorn은 Python WSGI 애플리케이션을 실행하는 서버입니다.

## 1.2 왜 필요한가?

### 개발 서버의 한계

Django나 FastAPI를 개발할 때 다음과 같이 실행해봤을 것입니다:

```bash
# Django
python manage.py runserver

# FastAPI
uvicorn main:app --reload
```

이 명령어들은 **개발용 서버**입니다. 개발 서버의 문제점:

1. **단일 스레드**: 한 번에 하나의 요청만 처리
2. **성능 부족**: 동시 접속자 수가 많으면 응답 지연
3. **안정성 부족**: 프로덕션 환경에서 충돌 시 복구 불가
4. **보안 취약**: 개발 편의 기능이 포함되어 있어 보안 위험

### 프로덕션 환경의 요구사항

실제 서비스를 운영하려면:

- **동시성 처리**: 여러 요청을 동시에 처리
- **안정성**: 프로세스가 죽어도 자동 재시작
- **성능**: 최적화된 요청 처리
- **모니터링**: 로그, 메트릭 수집

이러한 요구사항을 만족하는 것이 **Gunicorn**입니다.

## 1.3 Gunicorn의 역할

Gunicorn은 다음과 같은 역할을 합니다:

1. **HTTP 요청 수신**: 클라이언트로부터 HTTP 요청을 받음
2. **WSGI 애플리케이션 호출**: Python 애플리케이션의 WSGI 인터페이스를 호출
3. **응답 전송**: 애플리케이션의 응답을 클라이언트에 전송
4. **프로세스 관리**: 여러 워커 프로세스를 관리하여 동시성 확보

### 아키텍처 개요

```
클라이언트 요청
    ↓
Gunicorn (마스터 프로세스)
    ↓
워커 프로세스들 (Worker 1, 2, 3, ...)
    ↓
Django/FastAPI 애플리케이션
    ↓
응답 반환
```

이 구조는 Spring의 Tomcat이 여러 스레드로 요청을 처리하는 것과 유사하지만, **프로세스 기반**이라는 차이가 있습니다.

---

# 2장: WSGI/ASGI 프로토콜 이해

## 2.1 WSGI란?

**WSGI**(Web Server Gateway Interface)는 Python 웹 애플리케이션과 웹 서버 간의 **표준 인터페이스**입니다.

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

- **서블릿 스펙**: Java 웹 애플리케이션과 서버 간의 표준 인터페이스
- **WSGI**: Python 웹 애플리케이션과 서버 간의 표준 인터페이스

둘 다 **표준화된 인터페이스**를 통해 애플리케이션과 서버를 분리합니다.

## 2.2 WSGI Callable 규약

WSGI 애플리케이션은 다음 규약을 따라야 합니다:

1. **Callable 객체**: 함수 또는 `__call__` 메서드를 가진 클래스 인스턴스
2. **인자**: `environ` (환경 변수 딕셔너리), `start_response` (응답 시작 함수)
3. **반환값**: 응답 바이트의 이터러블 (리스트, 제너레이터 등)

### 최소한의 WSGI 애플리케이션 예제

```python
def simple_app(environ, start_response):
    """가장 간단한 WSGI 애플리케이션"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    return [b'Hello, WSGI!\n']
```

이 애플리케이션을 gunicorn으로 실행하면:

```bash
gunicorn simple_app:simple_app
```

### Django의 WSGI 애플리케이션

Django 프로젝트를 생성하면 `myproject/wsgi.py` 파일이 자동 생성됩니다:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_wsgi_application()
```

이 `application` 객체가 WSGI callable입니다. Gunicorn은 이 객체를 호출하여 요청을 처리합니다.

## 2.3 ASGI란?

**ASGI**(Asynchronous Server Gateway Interface)는 WSGI의 비동기 버전입니다.

### WSGI vs ASGI

| 특성 | WSGI | ASGI |
|------|------|------|
| 동기/비동기 | 동기만 지원 | 비동기 지원 |
| WebSocket | 지원 안 함 | 지원 |
| HTTP/2 | 제한적 | 완전 지원 |
| 사용 프레임워크 | Django (기본), Flask | FastAPI, Django (Channels) |

### FastAPI와 ASGI

FastAPI는 ASGI를 사용합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

이 `app` 객체는 ASGI 애플리케이션입니다. ASGI 서버(예: uvicorn)가 이를 실행합니다.

## 2.4 Gunicorn과 WSGI/ASGI

- **Gunicorn**: 주로 **WSGI 서버**로 사용 (Django 등)
- **Uvicorn**: **ASGI 서버** (FastAPI 등)
- **Gunicorn + Uvicorn 워커**: Gunicorn이 uvicorn 워커를 사용하여 ASGI 애플리케이션 실행 가능

이 조합은 나중에 6장에서 자세히 다룹니다.

---

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

---

# 4장: 프로세스 모델 및 워커 이해

## 4.1 프로세스 구조

Gunicorn은 **마스터-워커 모델**을 사용합니다.

### 마스터 프로세스 (Master Process)

- **역할**: 워커 프로세스들을 관리
- **책임**:
  - 워커 프로세스 생성/종료
  - 요청을 워커에 분배
  - 워커가 죽으면 자동 재시작
  - 시그널 처리 (SIGTERM, SIGHUP 등)

### 워커 프로세스 (Worker Process)

- **역할**: 실제 HTTP 요청을 처리
- **책임**:
  - WSGI 애플리케이션 호출
  - 요청/응답 처리
  - 마스터와 통신

### 프로세스 확인 실습

Gunicorn을 실행한 상태에서 다른 터미널에서:

```bash
ps aux | grep gunicorn
```

출력 예시:

```
user  12345  0.1  0.5  마스터 프로세스
user  12346  0.2  0.8  워커 프로세스 1
user  12347  0.2  0.8  워커 프로세스 2
user  12348  0.2  0.8  워커 프로세스 3
user  12349  0.2  0.8  워커 프로세스 4
```

워커 수는 `--workers` 옵션으로 지정한 수만큼 생성됩니다.

## 4.2 워커 타입

Gunicorn은 여러 워커 타입을 지원합니다.

### sync (기본값)

- **특징**: 동기 방식, 한 번에 하나의 요청 처리
- **사용 시나리오**: CPU 집약적 작업, 간단한 애플리케이션
- **장점**: 안정적, 디버깅 쉬움
- **단점**: 동시성 낮음

```bash
gunicorn app:application --worker-class sync --workers 4
```

### gevent

- **특징**: 비동기 I/O, 코루틴 기반
- **사용 시나리오**: I/O 집약적 작업 (DB 쿼리, 외부 API 호출)
- **장점**: 높은 동시성, 적은 메모리 사용
- **단점**: CPU 집약적 작업에는 부적합

```bash
pip install gevent
gunicorn app:application --worker-class gevent --workers 4
```

### gthread

- **특징**: 스레드 기반
- **사용 시나리오**: I/O 집약적 작업, C 확장 모듈 사용 시
- **장점**: 스레드 안전한 라이브러리와 호환
- **단점**: GIL(Global Interpreter Lock) 제약

```bash
gunicorn app:application --worker-class gthread --threads 4 --workers 2
```

### Spring/Tomcat과의 비교

| Spring/Tomcat | Gunicorn |
|--------------|----------|
| 스레드 풀 (Thread Pool) | 워커 프로세스 풀 (Worker Process Pool) |
| `maxThreads` 설정 | `--workers` 설정 |
| 스레드당 하나의 요청 | 프로세스당 하나의 요청 (sync) |
| 공유 메모리 | 프로세스 간 메모리 분리 |

**핵심 차이**: Tomcat은 스레드를 사용하고, Gunicorn은 프로세스를 사용합니다. 프로세스는 메모리를 공유하지 않으므로 더 안정적이지만, 메모리 사용량이 더 큽니다.

## 4.3 워커 수 결정

### 권장 공식

```
워커 수 = (2 × CPU 코어 수) + 1
```

예: 4코어 CPU → `(2 × 4) + 1 = 9` 워커

### 실습: 워커 수에 따른 동시성 테스트

`gunicorn/codes/02_worker_demo/app.py`:

```python
import time
import os

def application(environ, start_response):
    """워커 동작 확인용 애플리케이션"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    
    # 프로세스 ID와 작업 시뮬레이션
    pid = os.getpid()
    time.sleep(1)  # 1초 대기 (동시성 테스트용)
    
    return [f'Worker PID: {pid}\n'.encode('utf-8')]
```

실행:

```bash
gunicorn app:application --workers 4
```

여러 터미널에서 동시에 요청:

```bash
# 터미널 1
curl http://127.0.0.1:8000

# 터미널 2
curl http://127.0.0.1:8000

# 터미널 3
curl http://127.0.0.1:8000

# 터미널 4
curl http://127.0.0.1:8000
```

각 요청이 다른 PID를 반환하면 워커가 제대로 분산되고 있음을 확인할 수 있습니다.

---

# 5장: Django에서 사용하기

## 5.1 Django 프로젝트 준비

### 프로젝트 생성

```bash
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
```

### 기본 뷰 추가

`myapp/views.py`:

```python
from django.http import JsonResponse

def index(request):
    return JsonResponse({
        'message': 'Hello from Django with Gunicorn!',
        'method': request.method,
    })
```

`myproject/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from myapp.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
]
```

## 5.2 Gunicorn으로 실행

### 기본 실행

```bash
gunicorn myproject.wsgi:application
```

### 프로덕션 설정

```bash
gunicorn myproject.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
```

### 설정 설명

- `--bind 0.0.0.0:8000`: 모든 네트워크 인터페이스의 8000 포트에 바인딩
- `--workers 4`: 4개의 워커 프로세스
- `--worker-class sync`: 동기 워커 사용
- `--timeout 30`: 요청 타임아웃 30초
- `--access-logfile -`: 접근 로그를 표준 출력으로
- `--error-logfile -`: 에러 로그를 표준 출력으로

## 5.3 Django 설정 주의사항

### ALLOWED_HOSTS

`myproject/settings.py`:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']
```

프로덕션에서는 실제 도메인을 추가해야 합니다.

### DEBUG 모드

```python
DEBUG = False  # 프로덕션에서는 반드시 False
```

### 정적 파일 처리

Gunicorn은 정적 파일을 직접 서빙하지 않습니다. 다음 중 하나를 사용:

1. **Nginx/Apache**: 리버스 프록시로 정적 파일 서빙
2. **WhiteNoise**: Django 미들웨어로 정적 파일 서빙

```bash
pip install whitenoise
```

`settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 추가
    # ...
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

```bash
python manage.py collectstatic
```

## 5.4 실전 예제

`gunicorn/codes/03_django_example/` 디렉토리 구조:

```
03_django_example/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── myapp/
    ├── __init__.py
    ├── views.py
    └── urls.py
```

실행:

```bash
cd gunicorn/codes/03_django_example
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
```

브라우저에서 `http://127.0.0.1:8000` 접속하여 확인합니다.

---

# 6장: FastAPI에서 사용하기 (uvicorn 포함)

## 6.1 FastAPI와 ASGI

FastAPI는 **ASGI 애플리케이션**입니다. 따라서 ASGI 서버가 필요합니다.

### Uvicorn이란?

**Uvicorn**은 ASGI 서버입니다. Gunicorn과의 관계:

- **Gunicorn**: WSGI 서버 (Django 등)
- **Uvicorn**: ASGI 서버 (FastAPI 등)
- **Gunicorn + Uvicorn 워커**: Gunicorn이 uvicorn 워커를 사용하여 ASGI 애플리케이션 실행

## 6.2 Uvicorn 직접 사용

### 설치

```bash
pip install uvicorn fastapi
```

### FastAPI 애플리케이션

`gunicorn/codes/04_fastapi_example/main.py`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI with Uvicorn!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

### Uvicorn 실행

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

또는 리로드 모드:

```bash
uvicorn main:app --reload
```

## 6.3 Gunicorn + Uvicorn 워커

프로덕션 환경에서는 Gunicorn이 여러 uvicorn 워커를 관리하는 것이 좋습니다.

### 설치

```bash
pip install gunicorn uvicorn[standard] fastapi
```

### 실행

```bash
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4
```

### 구조 이해

```
Gunicorn (마스터 프로세스)
    ├─→ Uvicorn Worker 1 → FastAPI app
    ├─→ Uvicorn Worker 2 → FastAPI app
    ├─→ Uvicorn Worker 3 → FastAPI app
    └─→ Uvicorn Worker 4 → FastAPI app
```

각 워커는 독립적인 uvicorn 서버 인스턴스입니다.

## 6.4 WSGI vs ASGI 비교

| 특성 | WSGI | ASGI |
|------|------|------|
| **프로토콜** | 동기 | 비동기 |
| **WebSocket** | ❌ | ✅ |
| **HTTP/2** | 제한적 | ✅ |
| **사용 프레임워크** | Django (기본), Flask | FastAPI, Django Channels |
| **서버** | Gunicorn | Uvicorn (또는 Gunicorn + Uvicorn) |

### 언제 무엇을 사용할까?

- **WSGI (Gunicorn)**: Django, Flask 등 전통적인 동기 프레임워크
- **ASGI (Uvicorn)**: FastAPI, Django Channels 등 비동기 프레임워크

## 6.5 실전 예제

`gunicorn/codes/04_fastapi_example/` 디렉토리 구조:

```
04_fastapi_example/
├── main.py
└── requirements.txt
```

`requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
```

실행:

```bash
cd gunicorn/codes/04_fastapi_example
pip install -r requirements.txt
gunicorn main:app --worker-class uvicorn.workers.UvicornWorker --workers 4
```

브라우저에서 `http://127.0.0.1:8000/docs` 접속하여 FastAPI 자동 문서를 확인할 수 있습니다.

---

# 7장: 설정 파일 및 고급 옵션

## 7.1 설정 파일 사용

명령줄 옵션이 많아지면 설정 파일을 사용하는 것이 편리합니다.

### gunicorn.conf.py 생성

`gunicorn/codes/05_config_example/gunicorn.conf.py`:

```python
# 바인딩 주소 및 포트
bind = "0.0.0.0:8000"

# 워커 수
workers = 4

# 워커 타입
worker_class = "sync"

# 타임아웃 (초)
timeout = 30

# 접근 로그
accesslog = "-"  # 표준 출력

# 에러 로그
errorlog = "-"  # 표준 출력

# 로그 레벨
loglevel = "info"

# 프로세스 이름
proc_name = "myapp"

# 데몬 모드 (백그라운드 실행)
daemon = False

# PID 파일
pidfile = "/tmp/gunicorn.pid"

# 사용자/그룹 (프로덕션에서 권장)
# user = "www-data"
# group = "www-data"
```

### 설정 파일로 실행

```bash
gunicorn app:application -c gunicorn.conf.py
```

## 7.2 주요 설정 옵션

### 바인딩

```python
bind = "0.0.0.0:8000"  # 모든 인터페이스
# 또는
bind = "127.0.0.1:8000"  # 로컬호스트만
```

### 워커 설정

```python
workers = 4  # 워커 프로세스 수
worker_class = "sync"  # 워커 타입
worker_connections = 1000  # gevent/gthread 사용 시
threads = 4  # gthread 사용 시 스레드 수
```

### 타임아웃

```python
timeout = 30  # 워커 타임아웃 (초)
keepalive = 2  # Keep-Alive 연결 유지 시간 (초)
```

### 로깅

```python
accesslog = "/var/log/gunicorn/access.log"  # 접근 로그 파일
errorlog = "/var/log/gunicorn/error.log"  # 에러 로그 파일
loglevel = "info"  # debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

### 프로세스 관리

```python
daemon = False  # 백그라운드 실행 여부
pidfile = "/var/run/gunicorn.pid"  # PID 파일 경로
umask = 0  # 파일 권한 마스크
```

## 7.3 환경변수를 통한 설정

환경변수로도 설정할 수 있습니다:

```bash
export GUNICORN_BIND="0.0.0.0:8000"
export GUNICORN_WORKERS=4
gunicorn app:application
```

또는 `.env` 파일 사용:

```bash
pip install python-dotenv
```

`gunicorn.conf.py`에서:

```python
import os
from dotenv import load_dotenv

load_dotenv()

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.getenv("GUNICORN_WORKERS", "4"))
```

## 7.4 프로덕션 배포 예제

### Systemd 서비스 등록 (선택)

`/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=Gunicorn instance for myapp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/myapp
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn \
    --config /path/to/gunicorn.conf.py \
    myproject.wsgi:application

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
sudo systemctl start myapp
sudo systemctl enable myapp  # 부팅 시 자동 시작
```

### Nginx 리버스 프록시 (권장)

Nginx 설정 예제:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }
}
```

이렇게 하면:
- Nginx가 80 포트에서 요청 수신
- 정적 파일은 Nginx가 직접 서빙
- 동적 요청은 Gunicorn으로 전달

## 7.5 실전 예제

`gunicorn/codes/05_config_example/` 디렉토리:

```
05_config_example/
├── app.py
├── gunicorn.conf.py
└── .env.example
```

실행:

```bash
cd gunicorn/codes/05_config_example
gunicorn app:application -c gunicorn.conf.py
```

---

# 8장: Spring/Tomcat과의 비교 정리

## 8.1 아키텍처 비교

### 프로세스 모델 vs 스레드 모델

| 특성 | Spring/Tomcat | Python/Gunicorn |
|------|--------------|-----------------|
| **실행 단위** | 스레드 (Thread) | 프로세스 (Process) |
| **메모리 공유** | 공유 힙 메모리 | 프로세스별 독립 메모리 |
| **장점** | 메모리 효율적, 컨텍스트 스위칭 빠름 | 프로세스 격리, 안정성 높음 |
| **단점** | 스레드 안전성 고려 필요 | 메모리 사용량 큼 |

### 요청 처리 흐름

**Spring/Tomcat**:
```
요청 → Tomcat 스레드 풀 → 서블릿 컨테이너 → Spring 컨트롤러
```

**Python/Gunicorn**:
```
요청 → Gunicorn 마스터 → 워커 프로세스 → WSGI 애플리케이션
```

## 8.2 설정 방식 비교

### Tomcat: server.xml

```xml
<Connector port="8080" 
           maxThreads="200" 
           connectionTimeout="20000" />
```

### Gunicorn: gunicorn.conf.py

```python
bind = "0.0.0.0:8000"
workers = 4
timeout = 30
```

**공통점**: 모두 설정 파일로 서버 동작 제어  
**차이점**: XML vs Python 설정 파일

## 8.3 배포 방식 비교

### Spring/Tomcat: WAR 파일

```bash
# 빌드
mvn clean package

# 배포
cp target/myapp.war $CATALINA_HOME/webapps/
```

### Python/Gunicorn: 패키지/모듈

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
gunicorn myproject.wsgi:application
```

**차이점**: 
- WAR는 컴파일된 바이트코드 포함
- Python은 소스코드 직접 실행

## 8.4 성능 특성 비교

### 동시성 처리

| 항목 | Spring/Tomcat | Python/Gunicorn |
|------|--------------|-----------------|
| **기본 모델** | 스레드 풀 | 프로세스 풀 |
| **동시 요청 수** | 스레드 수에 비례 | 워커 수에 비례 |
| **메모리 사용** | 상대적으로 적음 | 상대적으로 많음 |
| **컨텍스트 스위칭** | 빠름 | 느림 |

### I/O 집약적 작업

- **Tomcat**: 스레드가 블로킹되면 다른 스레드가 처리
- **Gunicorn (sync)**: 워커가 블로킹되면 다른 워커가 처리
- **Gunicorn (gevent)**: 비동기 I/O로 높은 동시성

### CPU 집약적 작업

- **Tomcat**: 멀티스레드로 CPU 코어 활용
- **Gunicorn**: 멀티프로세스로 CPU 코어 활용 (GIL 제약 있음)

## 8.5 선택 가이드

### Spring/Tomcat을 선택하는 경우

- 기존 Java 생태계 활용
- 엔터프라이즈급 기능 필요 (JTA, JMS 등)
- 높은 처리량과 낮은 메모리 사용 중요

### Python/Gunicorn을 선택하는 경우

- Python 생태계 활용 (Django, FastAPI 등)
- 빠른 개발 속도 중요
- 데이터 분석/머신러닝 통합 필요

## 8.6 핵심 정리

### 공통점

1. **웹 서버 역할**: HTTP 요청을 받아 애플리케이션에 전달
2. **동시성 처리**: 여러 요청을 동시에 처리
3. **설정 파일**: 서버 동작을 설정 파일로 제어
4. **프로덕션 배포**: 리버스 프록시(Nginx/Apache)와 함께 사용

### 차이점

1. **실행 모델**: 스레드 vs 프로세스
2. **메모리 관리**: 공유 vs 격리
3. **언어**: Java vs Python
4. **프로토콜**: 서블릿 스펙 vs WSGI/ASGI

### 학습 포인트

Spring/Tomcat 경험자가 Python/Gunicorn을 이해할 때:

1. **역할은 동일**: 둘 다 웹 애플리케이션 서버
2. **구현 방식이 다름**: 스레드 vs 프로세스
3. **프로토콜이 다름**: 서블릿 스펙 vs WSGI/ASGI
4. **설정 방식이 다름**: XML vs Python

이러한 차이점을 이해하면 Python 웹 서버를 효과적으로 사용할 수 있습니다.

---

# 마무리

이 교과서를 통해 다음을 학습했습니다:

1. ✅ Gunicorn이 무엇이고 왜 필요한지
2. ✅ WSGI/ASGI 프로토콜의 동작 원리
3. ✅ Gunicorn 설치 및 기본 사용법
4. ✅ 프로세스 모델과 워커의 동작 방식
5. ✅ Django에서 Gunicorn 사용하기
6. ✅ FastAPI에서 Uvicorn 사용하기
7. ✅ 프로덕션 환경 설정 방법
8. ✅ Spring/Tomcat과의 비교를 통한 통합적 이해

이제 Django나 FastAPI 프로젝트를 프로덕션 환경에 배포할 준비가 되었습니다!

---

## 참고 자료

- [Gunicorn 공식 문서](https://docs.gunicorn.org/)
- [WSGI 스펙 (PEP 3333)](https://peps.python.org/pep-3333/)
- [ASGI 스펙](https://asgi.readthedocs.io/)
- [Uvicorn 공식 문서](https://www.uvicorn.org/)
