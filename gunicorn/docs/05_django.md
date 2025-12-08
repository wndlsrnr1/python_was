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

## 5.4 Spring Boot와의 비교

### 배포 방식

**Spring Boot**:
```bash
# 빌드
mvn clean package

# 실행
java -jar target/myapp.jar
```

**Django + Gunicorn**:
```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
gunicorn myproject.wsgi:application
```

**차이점**:
- Spring Boot: JAR 파일로 패키징하여 실행
- Django: 소스코드를 직접 실행

## 5.5 실전 예제

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

## 5.6 다음 단계

이제 Django에서 Gunicorn을 사용하는 방법을 배웠습니다. 다음 단계:

1. **06_fastapi.md**: FastAPI에서 ASGI 서버 사용법 이해
2. **07_config.md**: 프로덕션 환경을 위한 고급 설정 방법 습득

---

**이전: [04_worker_model.md](04_worker_model.md) | 다음: [06_fastapi.md](06_fastapi.md) →**

