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

## 7.6 다음 단계

이제 프로덕션 환경을 위한 고급 설정 방법을 배웠습니다. 다음 단계:

1. **08_comparison.md**: Spring/Tomcat과의 비교를 통한 통합적 이해

---

**이전: [06_fastapi.md](06_fastapi.md) | 다음: [08_comparison.md](08_comparison.md) →**

