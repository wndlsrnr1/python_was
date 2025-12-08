# 4장: 프로세스 모델 및 워커 이해

## 4.1 프로세스 구조

Gunicorn은 **마스터-워커 모델**을 사용합니다.

### 마스터 프로세스 (Master Process)

- **역할**: 워커 프로세스들을 관리
- **책임**:
  - 워커 프로세스 생성/종료
  - 요청을 워커에 분배
  - 워커가 죽으면 자동 재시작
  - 시그널 처리 (SIGTERM, SIGHUP 등)

### 워커 프로세스 (Worker Process)

- **역할**: 실제 HTTP 요청을 처리
- **책임**:
  - WSGI 애플리케이션 호출
  - 요청/응답 처리
  - 마스터와 통신

### 프로세스 확인 실습

Gunicorn을 실행한 상태에서 다른 터미널에서:

```bash
ps aux | grep gunicorn
```

출력 예시:

```
user  12345  0.1  0.5  마스터 프로세스
user  12346  0.2  0.8  워커 프로세스 1
user  12347  0.2  0.8  워커 프로세스 2
user  12348  0.2  0.8  워커 프로세스 3
user  12349  0.2  0.8  워커 프로세스 4
```

워커 수는 `--workers` 옵션으로 지정한 수만큼 생성됩니다.

## 4.2 워커 타입

Gunicorn은 여러 워커 타입을 지원합니다.

### sync (기본값)

- **특징**: 동기 방식, 한 번에 하나의 요청 처리
- **사용 시나리오**: CPU 집약적 작업, 간단한 애플리케이션
- **장점**: 안정적, 디버깅 쉬움
- **단점**: 동시성 낮음

```bash
gunicorn app:application --worker-class sync --workers 4
```

### gevent

- **특징**: 비동기 I/O, 코루틴 기반
- **사용 시나리오**: I/O 집약적 작업 (DB 쿼리, 외부 API 호출)
- **장점**: 높은 동시성, 적은 메모리 사용
- **단점**: CPU 집약적 작업에는 부적합

```bash
pip install gevent
gunicorn app:application --worker-class gevent --workers 4
```

### gthread

- **특징**: 스레드 기반
- **사용 시나리오**: I/O 집약적 작업, C 확장 모듈 사용 시
- **장점**: 스레드 안전한 라이브러리와 호환
- **단점**: GIL(Global Interpreter Lock) 제약

```bash
gunicorn app:application --worker-class gthread --threads 4 --workers 2
```

### Spring/Tomcat과의 비교

| Spring/Tomcat | Gunicorn |
|--------------|----------|
| 스레드 풀 (Thread Pool) | 워커 프로세스 풀 (Worker Process Pool) |
| `maxThreads` 설정 | `--workers` 설정 |
| 스레드당 하나의 요청 | 프로세스당 하나의 요청 (sync) |
| 공유 메모리 | 프로세스 간 메모리 분리 |

**핵심 차이**: Tomcat은 스레드를 사용하고, Gunicorn은 프로세스를 사용합니다. 프로세스는 메모리를 공유하지 않으므로 더 안정적이지만, 메모리 사용량이 더 큽니다.

## 4.3 워커 수 결정

### 권장 공식

```
워커 수 = (2 × CPU 코어 수) + 1
```

예: 4코어 CPU → `(2 × 4) + 1 = 9` 워커

### 실습: 워커 수에 따른 동시성 테스트

`gunicorn/codes/02_worker_demo/app.py`:

```python
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
```

실행:

```bash
gunicorn app:application --workers 4
```

여러 터미널에서 동시에 요청:

```bash
# 터미널 1
curl http://127.0.0.1:8000

# 터미널 2
curl http://127.0.0.1:8000

# 터미널 3
curl http://127.0.0.1:8000

# 터미널 4
curl http://127.0.0.1:8000
```

각 요청이 다른 PID를 반환하면 워커가 제대로 분산되고 있음을 확인할 수 있습니다.

## 4.4 다음 단계

이제 프로세스 모델과 워커를 이해했습니다. 다음 단계:

1. **05_django.md**: Django 프로젝트에서 실전 적용
2. **06_fastapi.md**: FastAPI에서 사용하기

---

**이전: [03_basic_setup.md](03_basic_setup.md) | 다음: [05_django.md](05_django.md) →**

