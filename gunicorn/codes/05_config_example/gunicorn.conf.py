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
