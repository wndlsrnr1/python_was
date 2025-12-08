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

# 프로세스 이름
proc_name = "myapp"
