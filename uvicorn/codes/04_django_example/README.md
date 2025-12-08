# Django + Uvicorn 예제

## 프로젝트 생성 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Django 및 Uvicorn 설치
pip install django uvicorn[standard]

# 3. Django 프로젝트 생성
django-admin startproject myproject .

# 4. 앱 생성
python manage.py startapp myapp

# 5. 마이그레이션 실행
python manage.py migrate

# 6. Uvicorn으로 실행
uvicorn myproject.asgi:application
```

## ASGI 모드 실행

```bash
# 기본 실행
uvicorn myproject.asgi:application

# 포트 변경
uvicorn myproject.asgi:application --port 8080

# 호스트 변경
uvicorn myproject.asgi:application --host 0.0.0.0

# 자동 리로드 (개발 모드)
uvicorn myproject.asgi:application --reload
```

## WSGI 모드와 비교

### WSGI 모드 (Gunicorn)

```bash
pip install gunicorn
gunicorn myproject.wsgi:application
```

### ASGI 모드 (Uvicorn)

```bash
uvicorn myproject.asgi:application
```

## 비동기 뷰 예제

`myapp/views.py`:

```python
from django.http import JsonResponse
import asyncio

async def async_view(request):
    await asyncio.sleep(1)  # 비동기 작업
    return JsonResponse({"message": "Async view"})
```

`myproject/urls.py`:

```python
from django.urls import path
from myapp.views import async_view

urlpatterns = [
    path('async/', async_view),
]
```

## 프로덕션 실행 (Gunicorn + Uvicorn)

```bash
pip install gunicorn

gunicorn myproject.asgi:application \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

