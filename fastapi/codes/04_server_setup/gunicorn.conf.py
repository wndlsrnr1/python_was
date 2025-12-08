# Gunicorn 설정 파일

# 바인딩 주소와 포트
bind = "0.0.0.0:8000"

# 워커 수 (CPU 코어 수 × 2 + 1)
workers = 4

# 워커 클래스 (Uvicorn 워커 사용)
worker_class = "uvicorn.workers.UvicornWorker"

# 타임아웃 (초)
timeout = 120

# Keep-Alive 시간 (초)
keepalive = 5

# 로그 레벨
loglevel = "info"

# 액세스 로그 파일
accesslog = "access.log"

# 에러 로그 파일
errorlog = "error.log"

