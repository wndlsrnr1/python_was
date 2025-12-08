# 프로덕션 배포 예제

## 준비 사항

1. 로그 디렉토리 생성

```bash
mkdir -p logs
```

2. 환경 변수 설정 (프로덕션)

```bash
export DATABASE_URL="postgresql://user:pass@localhost/db"
export SECRET_KEY="your-secret-key"
export DEBUG="False"
```

## 실행

### 개발 환경 (Uvicorn 단독)

```bash
# .env 파일 사용 (개발 환경만)
pip install python-dotenv
# .env 파일 생성 후

uvicorn main:app --reload
```

### 프로덕션 환경 (Gunicorn + Uvicorn)

```bash
gunicorn main:app -c gunicorn.conf.py
```

## 테스트

```bash
# 기본 엔드포인트
curl http://127.0.0.1:8000/

# 헬스 체크
curl http://127.0.0.1:8000/health
```

## 로그 확인

```bash
# 애플리케이션 로그
tail -f logs/app.log

# 액세스 로그
tail -f logs/access.log

# 에러 로그
tail -f logs/error.log
```

## systemd 서비스 등록 (선택사항)

`/etc/systemd/system/fastapi.service` 파일 생성:

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/fastapi/codes/05_production_example
Environment="PATH=/path/to/venv/bin"
Environment="DATABASE_URL=postgresql://user:pass@localhost/db"
Environment="SECRET_KEY=your-secret-key"
Environment="DEBUG=False"
ExecStart=/path/to/venv/bin/gunicorn main:app -c gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 관리:

```bash
sudo systemctl daemon-reload
sudo systemctl start fastapi
sudo systemctl enable fastapi
```

