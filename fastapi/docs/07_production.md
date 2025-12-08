# 7장: 프로덕션 배포 기본

## 7.1 프로덕션 환경 준비

프로덕션 환경에서는 개발 환경과 다른 설정이 필요합니다.

### 개발 vs 프로덕션

| 항목 | 개발 환경 | 프로덕션 환경 |
|------|---------|------------|
| **서버** | Uvicorn 단독 | Gunicorn + Uvicorn |
| **자동 리로드** | `--reload` 사용 | 사용 안 함 |
| **로그 레벨** | `debug` | `info` 또는 `warning` |
| **환경 변수** | 하드코딩 또는 `.env` | 시스템 환경 변수 |
| **HTTPS** | 선택적 | 필수 |

## 7.2 Gunicorn 설정 파일

프로덕션 환경에서는 설정 파일을 사용하는 것이 좋습니다.

### 기본 설정 파일

`gunicorn.conf.py`:

```python
# 바인딩 주소와 포트
bind = "0.0.0.0:8000"

# 워커 수
workers = 4

# 워커 클래스
worker_class = "uvicorn.workers.UvicornWorker"

# 타임아웃
timeout = 120
keepalive = 5

# 로그
loglevel = "info"
accesslog = "logs/access.log"
errorlog = "logs/error.log"

# 프로세스 이름
proc_name = "fastapi_app"
```

### 실행

```bash
gunicorn main:app -c gunicorn.conf.py
```

## 7.3 환경 변수 관리

프로덕션 환경에서는 환경 변수를 사용하여 설정을 관리합니다.

### 환경 변수 설정

```bash
export DATABASE_URL="postgresql://user:pass@localhost/db"
export SECRET_KEY="your-secret-key"
export DEBUG="False"
```

### FastAPI에서 사용

```python
import os
from fastapi import FastAPI

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

### .env 파일 (개발 환경만)

개발 환경에서는 `.env` 파일을 사용할 수 있습니다:

```env
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=dev-secret-key
DEBUG=True
```

```python
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드
```

**주의**: `.env` 파일은 프로덕션 환경에서 사용하지 마세요. 시스템 환경 변수를 사용하세요.

### Spring Boot와 비교

**Spring Boot**:
```properties
# application.properties
database.url=jdbc:postgresql://localhost/db
secret.key=your-secret-key
```

**FastAPI**:
```python
# 환경 변수 사용
DATABASE_URL = os.getenv("DATABASE_URL")
```

## 7.4 로깅 설정

프로덕션 환경에서는 체계적인 로깅이 필요합니다.

### 기본 로깅

```python
import logging
from fastapi import FastAPI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello"}
```

### 로그 레벨

- **DEBUG**: 개발 중 상세 정보
- **INFO**: 일반 정보 (프로덕션 기본)
- **WARNING**: 경고 메시지
- **ERROR**: 에러 메시지
- **CRITICAL**: 심각한 에러

### Spring Boot와 비교

**Spring Boot**:
```properties
# application.properties
logging.level.root=INFO
logging.file.name=logs/app.log
```

**FastAPI**:
```python
logging.basicConfig(level=logging.INFO)
```

## 7.5 성능 튜닝

### 워커 수 조정

```python
# gunicorn.conf.py
workers = 4  # CPU 코어 수에 따라 조정
```

### 타임아웃 설정

```python
# gunicorn.conf.py
timeout = 120  # 초 단위
```

### Keep-Alive 설정

```python
# gunicorn.conf.py
keepalive = 5  # 초 단위
```

## 7.6 시스템 서비스로 등록

프로덕션 환경에서는 systemd를 사용하여 서비스를 등록합니다.

### systemd 서비스 파일

`/etc/systemd/system/fastapi.service`:

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/fastapi
Environment="PATH=/var/www/fastapi/venv/bin"
ExecStart=/var/www/fastapi/venv/bin/gunicorn main:app -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 서비스 관리

```bash
# 서비스 시작
sudo systemctl start fastapi

# 서비스 중지
sudo systemctl stop fastapi

# 서비스 재시작
sudo systemctl restart fastapi

# 서비스 상태 확인
sudo systemctl status fastapi

# 부팅 시 자동 시작
sudo systemctl enable fastapi
```

### Spring Boot와 비교

**Spring Boot**:
```ini
[Unit]
Description=Spring Boot Application
After=network.target

[Service]
ExecStart=/usr/bin/java -jar /var/www/springboot/app.jar
Restart=always
```

**FastAPI**:
```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
ExecStart=/var/www/fastapi/venv/bin/gunicorn main:app -c gunicorn.conf.py
Restart=always
```

## 7.7 실습 예제

`fastapi/codes/05_production_example/` 디렉토리에 프로덕션 설정 예제가 있습니다.

### 예제 구조

```
05_production_example/
├── main.py              # FastAPI 애플리케이션
├── gunicorn.conf.py     # Gunicorn 설정
├── .env.example         # 환경 변수 예제
└── README.md            # 실행 방법
```

## 7.8 보안 고려사항

### HTTPS 사용

프로덕션 환경에서는 HTTPS를 사용해야 합니다. Nginx나 다른 리버스 프록시를 사용하세요.

### 시크릿 키 관리

시크릿 키는 환경 변수로 관리하고, 절대 코드에 하드코딩하지 마세요.

### CORS 설정

필요한 경우 CORS를 적절히 설정하세요:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 7.9 다음 단계

이제 프로덕션 환경에서 FastAPI를 배포하는 기본 방법을 배웠습니다. 다음 단계:

1. **08_comparison.md**: Spring과의 종합 비교 정리

---

**이전: [06_uvicorn_gunicorn.md](06_uvicorn_gunicorn.md) | 다음: [08_comparison.md](08_comparison.md) →**

