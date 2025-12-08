# 6장: Django에서 사용하기

## 6.1 Django의 WSGI와 ASGI

Django는 기본적으로 **WSGI**를 사용하지만, **ASGI** 모드도 지원합니다.

### WSGI vs ASGI 모드

| 모드 | 사용 시나리오 | 서버 |
|------|--------------|------|
| **WSGI** | 전통적인 동기 Django 앱 | Gunicorn |
| **ASGI** | WebSocket, 비동기 뷰, Django Channels | Uvicorn |

### 언제 ASGI를 사용할까?

- ✅ **WebSocket**이 필요한 경우
- ✅ **비동기 뷰**를 사용하는 경우
- ✅ **Django Channels**를 사용하는 경우
- ✅ **HTTP/2**를 활용하고 싶은 경우

## 6.2 Django ASGI 설정

### asgi.py 파일

Django 프로젝트를 생성하면 `myproject/asgi.py` 파일이 자동 생성됩니다:

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_asgi_application()
```

이 `application` 객체가 ASGI callable입니다.

### ASGI 애플리케이션 구조

```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# 기본 Django ASGI 애플리케이션
django_asgi_app = get_asgi_application()

# 프로토콜별 라우팅 (HTTP + WebSocket)
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # WebSocket 라우팅
        ])
    ),
})
```

## 6.3 기본 실행

### Uvicorn으로 실행

```bash
uvicorn myproject.asgi:application
```

여기서 `myproject.asgi:application`은:
- `myproject.asgi`: `myproject/asgi.py` 모듈
- `application`: 해당 모듈의 `application` 변수 (ASGI callable)

### 프로덕션 설정

```bash
uvicorn myproject.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4
```

**주의**: Uvicorn의 `--workers` 옵션은 단일 프로세스 내에서 여러 워커를 생성하지 않습니다. 프로덕션에서는 Gunicorn과 함께 사용하는 것이 권장됩니다.

## 6.4 Django 비동기 뷰

Django 3.1+부터 비동기 뷰를 지원합니다.

### 동기 뷰

```python
from django.http import JsonResponse

def sync_view(request):
    return JsonResponse({"message": "Sync view"})
```

### 비동기 뷰

```python
from django.http import JsonResponse
import asyncio

async def async_view(request):
    await asyncio.sleep(1)  # 비동기 작업
    return JsonResponse({"message": "Async view"})
```

### 클래스 기반 뷰

```python
from django.views import View
from django.http import JsonResponse
import asyncio

class AsyncView(View):
    async def get(self, request):
        await asyncio.sleep(1)
        return JsonResponse({"message": "Async class-based view"})
```

## 6.5 WebSocket 지원 (Django Channels)

Django Channels를 사용하면 WebSocket을 지원할 수 있습니다.

### Django Channels 설치

```bash
pip install channels
```

### settings.py 설정

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',  # 추가
    'myapp',
]

ASGI_APPLICATION = 'myproject.asgi.application'
```

### WebSocket 소비자 (Consumer)

```python
# myapp/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        await self.send(text_data=json.dumps({
            'message': message
        }))
```

### WebSocket 라우팅

```python
# myproject/asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import myapp.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            myapp.routing.websocket_urlpatterns
        )
    ),
})
```

```python
# myapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]
```

## 6.6 WSGI vs ASGI 모드 비교

### WSGI 모드 (Gunicorn)

```bash
gunicorn myproject.wsgi:application
```

**특징**:
- ✅ 전통적인 Django 앱에 적합
- ✅ 안정적이고 검증됨
- ❌ WebSocket 미지원
- ❌ 비동기 뷰 제한적

### ASGI 모드 (Uvicorn)

```bash
uvicorn myproject.asgi:application
```

**특징**:
- ✅ WebSocket 지원
- ✅ 비동기 뷰 완전 지원
- ✅ HTTP/2 지원
- ⚠️ 일부 미들웨어 호환성 문제 가능

### 선택 가이드

| 상황 | 권장 모드 |
|------|----------|
| 전통적인 Django 앱 | WSGI (Gunicorn) |
| WebSocket 필요 | ASGI (Uvicorn) |
| 비동기 뷰 사용 | ASGI (Uvicorn) |
| Django Channels 사용 | ASGI (Uvicorn) |

## 6.7 프로덕션 배포

### Gunicorn + Uvicorn 워커

프로덕션 환경에서는 Gunicorn이 여러 Uvicorn 워커를 관리하는 것이 좋습니다:

```bash
pip install gunicorn uvicorn[standard]

gunicorn myproject.asgi:application \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

이렇게 하면:
- 멀티 코어 활용
- 프로세스 격리
- 높은 동시성

자세한 내용은 07_config.md에서 다룹니다.

## 6.8 실전 예제

`uvicorn/codes/04_django_example/` 디렉토리에 Django ASGI 예제가 있습니다.

### 프로젝트 생성

```bash
django-admin startproject myproject
cd myproject
python manage.py startapp myapp
```

### asgi.py 확인

`myproject/asgi.py` 파일이 자동 생성됩니다.

### 실행

```bash
uvicorn myproject.asgi:application
```

브라우저에서 `http://127.0.0.1:8000` 접속하여 확인합니다.

## 6.9 주의사항

### 미들웨어 호환성

일부 Django 미들웨어는 ASGI 모드에서 제대로 작동하지 않을 수 있습니다. 테스트가 필요합니다.

### 정적 파일

Uvicorn은 정적 파일을 직접 서빙하지 않습니다. Nginx나 WhiteNoise를 사용하세요.

### 데이터베이스 연결

비동기 뷰에서 데이터베이스를 사용할 때는 `async` 쿼리 메서드를 사용해야 합니다:

```python
from django.db import models

async def async_view(request):
    # 동기 ORM (작동하지만 블로킹)
    # user = User.objects.get(id=1)
    
    # 비동기 ORM (Django 4.1+)
    user = await User.objects.aget(id=1)
    return JsonResponse({"user": user.username})
```

## 6.10 다음 단계

이제 Django에서 ASGI 모드로 uvicorn을 사용하는 방법을 배웠습니다. 다음 단계:

1. **07_config.md**: 프로덕션 환경 설정 방법

---

**이전: [05_fastapi.md](05_fastapi.md) | 다음: [07_config.md](07_config.md) →**

