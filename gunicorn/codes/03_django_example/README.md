# Django + Gunicorn 예제

## 프로젝트 생성 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Django 및 Gunicorn 설치
pip install django gunicorn

# 3. Django 프로젝트 생성
django-admin startproject myproject .

# 4. 앱 생성
python manage.py startapp myapp

# 5. settings.py 수정
# ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 6. urls.py에 뷰 추가 (아래 예제 참고)

# 7. Gunicorn 실행
gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
```

## myapp/views.py 예제

```python
from django.http import JsonResponse

def index(request):
    return JsonResponse({
        'message': 'Hello from Django with Gunicorn!',
        'method': request.method,
    })
```

## myproject/urls.py 예제

```python
from django.contrib import admin
from django.urls import path
from myapp.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
]
```

