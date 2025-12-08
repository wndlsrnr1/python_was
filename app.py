def application(environ, start_response):
    import os
    import time
    status = "200 OK"
    headers = [("Content-Type", "text/plain; charset=utf-8")]
    start_response(status, headers)

    # 프로세스 ID와 작업 시뮬레이션
    pid: int = os.getpid()
    _ = time.sleep(1) # 1초 대기 (동시성 테스트용)

    return [f"worker PID: {pid}\n".encode("utf-8")]

"""
이제 프로세스 모델과 워커를 이해했습니다. 다음 단계:
05_django.md Django 프로젝트에서 실전 적용
06_fastapi.md FASTAPI에서 사용하기
"""