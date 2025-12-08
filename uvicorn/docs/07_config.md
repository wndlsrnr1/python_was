# 7장: 설정 파일 및 고급 옵션

## 7.1 명령줄 옵션

Uvicorn은 다양한 명령줄 옵션을 제공합니다.

### 기본 옵션

```bash
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
```

### 주요 옵션 설명

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--host` | 바인딩할 호스트 | `127.0.0.1` |
| `--port` | 바인딩할 포트 | `8000` |
| `--workers` | 워커 수 (단일 프로세스) | `1` |
| `--log-level` | 로그 레벨 | `info` |
| `--reload` | 자동 리로드 (개발 모드) | `False` |
| `--reload-dir` | 리로드 감시 디렉토리 | 현재 디렉토리 |
| `--timeout-keep-alive` | Keep-Alive 타임아웃 | `5` |

## 7.2 환경변수를 통한 설정

환경변수로도 설정할 수 있습니다:

```bash
export UVICORN_HOST=0.0.0.0
export UVICORN_PORT=8000
export UVICORN_WORKERS=4
uvicorn main:app
```

### .env 파일 사용

```bash
pip install python-dotenv
```

`.env` 파일:

```env
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8000
UVICORN_WORKERS=4
UVICORN_LOG_LEVEL=info
```

Python 코드에서:

```python
from dotenv import load_dotenv
import os

load_dotenv()

host = os.getenv("UVICORN_HOST", "127.0.0.1")
port = int(os.getenv("UVICORN_PORT", "8000"))
```

## 7.3 로깅 설정

### 로그 레벨

```bash
uvicorn main:app --log-level debug
```

로그 레벨: `critical`, `error`, `warning`, `info`, `debug`, `trace`

### 커스텀 로깅

```python
import logging
from uvicorn import Config, Server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

config = Config(
    app="main:app",
    host="0.0.0.0",
    port=8000,
    log_level="info"
)

server = Server(config)
server.run()
```

## 7.4 Gunicorn + Uvicorn 워커

프로덕션 환경에서는 Gunicorn이 여러 Uvicorn 워커를 관리하는 것이 권장됩니다.

### 설치

```bash
pip install gunicorn uvicorn[standard]
```

### 기본 실행

```bash
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
```

### 설정 파일 사용

`gunicorn.conf.py`:

```python
# 워커 설정
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

# 로깅
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 프로세스 관리
daemon = False
pidfile = "/tmp/gunicorn.pid"

# 타임아웃
timeout = 30
keepalive = 2
```

실행:

```bash
gunicorn main:app -c gunicorn.conf.py
```

### 워커 수 결정

```
워커 수 = (2 × CPU 코어 수) + 1
```

예: 4코어 CPU → `(2 × 4) + 1 = 9` 워커

## 7.5 프로덕션 배포 예제

### Systemd 서비스 등록 (선택)

`/etc/systemd/system/myapp.service`:

```ini
[Unit]
Description=Uvicorn instance for myapp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/myapp
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn \
    --config /path/to/gunicorn.conf.py \
    main:app

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
        
        # WebSocket 지원
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }
}
```

이렇게 하면:
- Nginx가 80 포트에서 요청 수신
- 정적 파일은 Nginx가 직접 서빙
- 동적 요청은 Uvicorn으로 전달
- WebSocket 지원

## 7.6 성능 최적화

### uvloop 사용 (Linux/Mac)

```bash
pip install uvloop
```

`uvicorn[standard]`를 설치하면 자동으로 사용됩니다.

### HTTP/2 지원

```bash
uvicorn main:app --http httptools
```

### 워커 수 조정

```bash
# 단일 프로세스 (기본)
uvicorn main:app

# Gunicorn + Uvicorn 워커 (권장)
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4
```

## 7.7 보안 설정

### HTTPS 설정

Nginx에서 SSL/TLS를 처리하는 것이 일반적입니다.

### 접근 제한

```bash
# 특정 호스트만 허용
uvicorn main:app --host 127.0.0.1
```

### 헤더 설정

FastAPI에서:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```

## 7.8 모니터링

### 헬스 체크 엔드포인트

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### 메트릭 수집

Prometheus, Grafana 등을 사용하여 메트릭을 수집할 수 있습니다.

## 7.9 실전 예제

`uvicorn/codes/05_config_example/` 디렉토리에 설정 예제가 있습니다:

- `gunicorn.conf.py`: Gunicorn 설정 파일
- `main.py`: FastAPI 애플리케이션
- `README.md`: 실행 방법

### 실행

```bash
cd uvicorn/codes/05_config_example
pip install -r requirements.txt
gunicorn main:app -c gunicorn.conf.py
```

## 7.10 다음 단계

이제 프로덕션 환경에서 uvicorn을 설정하는 방법을 배웠습니다. 다음 단계:

1. **08_comparison.md**: Gunicorn/Spring과의 비교를 통한 통합적 이해

---

**이전: [06_django.md](06_django.md) | 다음: [08_comparison.md](08_comparison.md) →**

