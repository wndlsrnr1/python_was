# Gunicorn 프로덕션 설정

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
proc_name = "fastapi_production"

