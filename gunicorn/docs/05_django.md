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

### Timeout 설정 상세 설명

#### Timeout이란?

**Timeout(타임아웃)**은 요청 처리가 완료되기를 기다리는 최대 시간입니다. 이 시간을 초과하면 요청이 강제로 종료됩니다.

**왜 필요한가?**

1. **무한 대기 방지**: 응답이 오지 않는 요청이 워커를 영원히 점유하는 것을 방지
2. **리소스 보호**: 응답하지 않는 요청으로 인한 메모리 누수 방지
3. **시스템 안정성**: 문제가 있는 요청이 전체 시스템을 마비시키는 것을 방지

**동작 원리**:

```
요청 시작
    ↓
워커가 요청 처리 시작
    ↓
[30초 경과] ← timeout 설정값
    ↓
응답이 아직 오지 않으면?
    ↓
워커 프로세스 강제 종료
    ↓
마스터 프로세스가 새 워커 생성
```

#### 여러 컴포넌트의 Timeout 비교

프로덕션 환경에서는 보통 **Nginx → Gunicorn → Django** 순서로 요청이 전달됩니다. 각 컴포넌트마다 timeout 설정이 있습니다.

| 컴포넌트     | Timeout 설정         | 기본값  | 역할                                   |
| ------------ | -------------------- | ------- | -------------------------------------- |
| **Nginx**    | `proxy_read_timeout` | 60초    | Gunicorn으로부터 응답을 기다리는 시간  |
| **Gunicorn** | `--timeout`          | 30초    | 워커가 요청을 처리하는 최대 시간       |
| **Django**   | 없음                 | -       | Django 자체는 timeout 설정 없음        |
| **Vite**     | `server.hmr.timeout` | 30000ms | 개발 서버의 HMR(핫 모듈 교체) 타임아웃 |

**Nginx 설정 예시**:

```nginx
server {
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 60s;  # Gunicorn 응답 대기 시간
        proxy_connect_timeout 10s;  # 연결 시간
    }
}
```

**Gunicorn 설정**:

```bash
gunicorn myproject.wsgi:application --timeout 30
```

#### "하한만 따지는가?" - Timeout의 우선순위

**답변: 네, 가장 짧은 timeout이 실제로 적용됩니다.**

**동작 원리**:

```
클라이언트 요청
    ↓
Nginx (proxy_read_timeout: 60초)
    ↓
Gunicorn (--timeout: 30초)
    ↓
Django 애플리케이션
```

**시나리오 1: Gunicorn timeout이 더 짧은 경우**

- Nginx: 60초 대기
- Gunicorn: 30초 대기
- **실제 적용**: 30초 (Gunicorn이 먼저 타임아웃)

**시나리오 2: Nginx timeout이 더 짧은 경우**

- Nginx: 30초 대기
- Gunicorn: 60초 대기
- **실제 적용**: 30초 (Nginx가 먼저 타임아웃)

**핵심 원리**:

각 컴포넌트는 **독립적으로** 자신의 timeout을 체크합니다. 가장 먼저 timeout이 발생하는 컴포넌트가 연결을 끊고, 그 시점에 전체 요청이 종료됩니다.

**권장 설정**:

```nginx
# Nginx: Gunicorn보다 약간 길게 설정
proxy_read_timeout 60s;
```

```bash
# Gunicorn: 기본값 또는 애플리케이션 특성에 맞게
gunicorn myproject.wsgi:application --timeout 30
```

**이유**: Gunicorn이 먼저 타임아웃되어 워커가 재시작되면, Nginx는 여전히 대기 중이므로 새 워커가 요청을 처리할 수 있습니다. 반대로 Nginx가 먼저 타임아웃되면 클라이언트는 에러를 받게 됩니다.

#### Timeout 설정 가이드

**짧은 timeout (10-30초)**:

- 빠른 응답이 필요한 API
- 사용자 인터랙션이 많은 웹 애플리케이션
- 실시간성이 중요한 서비스

**긴 timeout (60-120초)**:

- 파일 업로드/다운로드
- 대용량 데이터 처리
- 배치 작업 API

**예시**:

```bash
# 빠른 응답이 필요한 경우
gunicorn myproject.wsgi:application --timeout 20

# 파일 처리 등 긴 작업이 있는 경우
gunicorn myproject.wsgi:application --timeout 120
```

### 로그 파일 설정 상세 설명

#### Access Log와 Error Log의 차이

**Access Log (접근 로그)**:

- **내용**: 모든 HTTP 요청 기록
- **포함 정보**: IP 주소, 요청 시간, HTTP 메서드, URL, 상태 코드, 응답 크기 등
- **용도**: 트래픽 분석, 사용자 행동 분석, 성능 모니터링

**Error Log (에러 로그)**:

- **내용**: 에러와 경고만 기록
- **포함 정보**: 예외 스택 트레이스, 에러 메시지, 경고 등
- **용도**: 문제 진단, 디버깅, 시스템 모니터링

#### 로그 파일 경로 설정

**파일로 저장**:

```bash
gunicorn myproject.wsgi:application \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log
```

**표준 출력으로 출력** (`-` 사용):

```bash
gunicorn myproject.wsgi:application \
    --access-logfile - \
    --error-logfile -
```

**표준 출력을 사용하는 경우**:

- Docker 컨테이너에서 실행 시 (로그 수집 도구가 표준 출력을 캡처)
- 개발 환경에서 즉시 확인
- systemd 등 프로세스 관리자가 로그를 자동으로 수집

#### 프로덕션 환경 권장 설정

**로그 디렉토리 생성**:

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
```

**Gunicorn 실행**:

```bash
gunicorn myproject.wsgi:application \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info
```

**로그 로테이션 설정** (선택):

`/etc/logrotate.d/gunicorn`:

```
/var/log/gunicorn/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn || true
    endscript
}
```

이 설정은 로그 파일을 매일 회전시키고, 14일치를 보관하며, 압축합니다.

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

#### Gunicorn이 정적 파일을 서빙하지 않는 이유

**Gunicorn의 역할**:

- Gunicorn은 **WSGI 애플리케이션 서버**입니다
- 동적 요청(Django 뷰)만 처리하는 것이 목적입니다
- 정적 파일(CSS, JavaScript, 이미지 등)은 웹 서버의 역할입니다

**비유**:

- **Gunicorn**: 요리사 (동적 요청 처리)
- **Nginx/WhiteNoise**: 서빙 직원 (정적 파일 제공)

#### WhiteNoise란?

**WhiteNoise**는 Django 미들웨어로, 정적 파일을 효율적으로 서빙할 수 있게 해주는 라이브러리입니다.

**동작 원리**:

```
HTTP 요청
    ↓
Django 미들웨어 체인
    ↓
WhiteNoiseMiddleware
    ↓
정적 파일 요청인가?
    ├─ Yes → 정적 파일 직접 서빙 (Django 뷰 호출 안 함)
    └─ No → 다음 미들웨어로 전달
```

**특징**:

- **미들웨어 기반**: Django의 미들웨어 시스템을 활용
- **메모리 효율**: 정적 파일을 메모리에 캐싱
- **CDN 없이 사용 가능**: 작은 규모 애플리케이션에 적합

#### WhiteNoise vs Nginx

| 항목               | WhiteNoise                          | Nginx                        |
| ------------------ | ----------------------------------- | ---------------------------- |
| **설정 복잡도**    | 간단 (Django 설정만)                | 복잡 (별도 서버 설정)        |
| **성능**           | 좋음 (미들웨어 레벨)                | 매우 좋음 (웹 서버 레벨)     |
| **적용 시나리오**  | 소규모 애플리케이션, Heroku 등 PaaS | 프로덕션 환경, 대규모 트래픽 |
| **정적 파일 캐싱** | 메모리 캐싱                         | 디스크 + 메모리 캐싱         |
| **CDN 연동**       | 제한적                              | 완벽 지원                    |

**언제 WhiteNoise를 사용할까?**

- Heroku, Railway 등 PaaS 환경
- 소규모 애플리케이션
- Nginx 설정이 복잡한 경우
- 개발/스테이징 환경

**언제 Nginx를 사용할까?**

- 프로덕션 환경
- 대규모 트래픽
- CDN 연동이 필요한 경우
- 정적 파일 최적화가 중요한 경우

#### WhiteNoise 설정 방법

**1. 설치**:

```bash
pip install whitenoise
```

**2. settings.py 설정**:

```python
# MIDDLEWARE에 추가 (SecurityMiddleware 다음에)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 여기 추가
    'django.middleware.common.CommonMiddleware',
    # ... 나머지 미들웨어
]

# 정적 파일 루트 디렉토리 설정
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise 추가 설정 (선택)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**설명**:

- `STATIC_ROOT`: `collectstatic` 명령어로 수집된 정적 파일이 저장될 경로
- `STATICFILES_STORAGE`: WhiteNoise의 압축 및 캐싱 기능 사용

**3. 정적 파일 수집**:

```bash
python manage.py collectstatic
```

이 명령어는:

- `STATICFILES_DIRS`에 있는 정적 파일들을 수집
- 각 앱의 `static/` 디렉토리에서 정적 파일을 수집
- `STATIC_ROOT` 디렉토리에 모든 정적 파일을 복사

**4. 실행 확인**:

```bash
gunicorn myproject.wsgi:application
```

이제 정적 파일 요청(`/static/css/style.css` 등)이 WhiteNoise를 통해 서빙됩니다.

#### WhiteNoise 동작 예시

**요청 흐름**:

```
1. 클라이언트: GET /static/css/style.css
   ↓
2. Gunicorn: 요청 수신
   ↓
3. Django: 미들웨어 체인 시작
   ↓
4. WhiteNoiseMiddleware: /static/ 경로 감지
   ↓
5. WhiteNoise: staticfiles/css/style.css 파일 찾기
   ↓
6. WhiteNoise: 파일을 직접 응답 (Django 뷰 호출 안 함)
   ↓
7. 클라이언트: CSS 파일 수신
```

**장점**:

- Django 뷰를 거치지 않아 빠름
- 메모리에 캐싱되어 반복 요청 시 더 빠름
- 별도 웹 서버 없이 정적 파일 서빙 가능

#### 프로덕션 환경 권장 사항

**소규모 애플리케이션**:

- WhiteNoise만 사용해도 충분

**대규모 애플리케이션**:

- Nginx를 리버스 프록시로 사용
- Nginx가 정적 파일 직접 서빙
- WhiteNoise는 비활성화

**Nginx + Gunicorn 구성 예시**:

```nginx
server {
    # 정적 파일은 Nginx가 직접 서빙
    location /static/ {
        alias /path/to/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 동적 요청은 Gunicorn으로 전달
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

이 경우 `settings.py`에서 WhiteNoise 미들웨어를 제거하거나, Nginx가 정적 파일을 먼저 처리하므로 WhiteNoise는 동작하지 않습니다.

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
