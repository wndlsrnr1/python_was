# 5장: Django/FastAPI 자동 리로드 활용

## 5.1 Django의 자동 리로드

### 기본 사용법

```bash
python manage.py runserver
```

이 명령어를 실행하면 Django는 자동으로 파일 변경을 감지하고 서버를 재시작합니다.

### 내부 동작 원리

Django는 내부적으로 watchdog을 사용하여 다음을 모니터링합니다:

- Python 파일 (`.py`)
- 템플릿 파일 (`.html`, `.txt` 등)
- 설정 파일

파일이 변경되면:
1. Watchdog이 이벤트 감지
2. Django가 변경된 파일 확인
3. 서버 자동 재시작
4. 변경 사항 반영

### 수동으로 확인하기

Django의 자동 리로드가 어떻게 동작하는지 확인하려면:

```bash
python manage.py runserver --verbosity 2
```

이렇게 하면 파일 변경 감지 로그를 볼 수 있습니다.

## 5.2 FastAPI/Uvicorn의 자동 리로드

### 기본 사용법

```bash
uvicorn main:app --reload
```

이 명령어를 실행하면 Uvicorn은 자동으로 파일 변경을 감지하고 서버를 재시작합니다.

### 내부 동작 원리

Uvicorn은 내부적으로 watchdog을 사용하여 다음을 모니터링합니다:

- Python 파일 (`.py`)
- 설정 파일

파일이 변경되면:
1. Watchdog이 이벤트 감지
2. Uvicorn이 변경된 파일 확인
3. 서버 자동 재시작
4. 변경 사항 반영

### 수동으로 확인하기

```bash
uvicorn main:app --reload --log-level debug
```

이렇게 하면 파일 변경 감지 로그를 볼 수 있습니다.

## 5.3 직접 자동 리로드 구현하기

### 간단한 자동 리로드 서버

`watchdog/codes/03_django_reload/simple_reload.py`:

```python
import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.start_process()
    
    def start_process(self):
        """프로세스 시작"""
        if self.process:
            self.process.terminate()
        print("서버 시작...")
        self.process = subprocess.Popen([sys.executable, self.script_path])
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"파일 변경 감지: {event.src_path}")
            print("서버 재시작...")
            self.start_process()

if __name__ == "__main__":
    # 모니터링할 스크립트
    script_to_run = "app.py"
    
    handler = ReloadHandler(script_to_run)
    observer = Observer()
    observer.schedule(handler, ".", recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.terminate()
    observer.join()
```

## 5.4 Django 자동 리로드 예제

`watchdog/codes/03_django_reload/` 디렉토리에 Django 자동 리로드 예제가 있습니다.

### 실행 방법

```bash
# Django 프로젝트가 있다고 가정
python manage.py runserver
```

파일을 수정하면 자동으로 서버가 재시작됩니다.

## 5.5 FastAPI 자동 리로드 예제

`watchdog/codes/04_fastapi_reload/` 디렉토리에 FastAPI 자동 리로드 예제가 있습니다.

### 실행 방법

```bash
# FastAPI 애플리케이션이 있다고 가정
uvicorn main:app --reload
```

파일을 수정하면 자동으로 서버가 재시작됩니다.

## 5.6 Spring Boot DevTools와 비교

### Spring Boot DevTools

```java
// application.properties
spring.devtools.restart.enabled=true
spring.devtools.livereload.enabled=true
```

**특징**:
- 클래스패스 변경 감지
- 자동 재시작
- LiveReload 지원

### Django/FastAPI 자동 리로드

```bash
# Django
python manage.py runserver

# FastAPI
uvicorn main:app --reload
```

**특징**:
- Python 파일 변경 감지
- 자동 재시작
- 간단한 사용법

**공통점**: 둘 다 파일 변경을 감지하여 자동으로 재시작합니다.

## 5.7 자동 리로드의 제한사항

### 감지되지 않는 변경

- 데이터베이스 변경
- 환경 변수 변경
- 외부 설정 파일 변경

### 성능 고려사항

많은 파일이 있는 프로젝트에서는 자동 리로드가 느릴 수 있습니다.

### 프로덕션 환경

**주의**: 프로덕션 환경에서는 자동 리로드를 사용하지 마세요!

```bash
# 프로덕션 (자동 리로드 없음)
uvicorn main:app --host 0.0.0.0 --port 8000

# 개발 (자동 리로드)
uvicorn main:app --reload
```

## 5.8 다음 단계

이제 Django/FastAPI에서 자동 리로드가 어떻게 동작하는지 이해했습니다. 다음 단계:

1. **06_advanced_usage.md**: 고급 사용법 학습

---

**이전: [04_observer_pattern.md](04_observer_pattern.md) | 다음: [06_advanced_usage.md](06_advanced_usage.md) →**

