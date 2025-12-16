import time
import os

def application(environ, start_response):
    """워커 동작 확인용 애플리케이션"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    
    # 프로세스 ID와 작업 시뮬레이션
    pid = os.getpid()
    time.sleep(1)  # 1초 대기 (동시성 테스트용)
    
    return [f'Worker PID: {pid}\n'.encode('utf-8')]

