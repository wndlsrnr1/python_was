# 3장: 기본 설치 및 사용

## 3.1 설치

### 가상환경 설정 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### Watchdog 설치

```bash
pip install watchdog
```

설치 확인:

```bash
python -c "import watchdog; print(watchdog.__version__)"
```

## 3.2 최소한의 파일 모니터링 예제

`watchdog/codes/01_basic_setup/watch.py` 파일을 생성합니다:

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"파일이 수정되었습니다: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory:
            print(f"파일이 생성되었습니다: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"파일이 삭제되었습니다: {event.src_path}")

if __name__ == "__main__":
    # 모니터링할 디렉토리
    watch_directory = "."

    # 이벤트 핸들러 생성
    event_handler = MyHandler()

    # 옵저버 생성
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=False)

    # 모니터링 시작
    observer.start()
    print(f"모니터링 시작: {watch_directory}")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n모니터링 종료")

    observer.join()
```

## 3.3 실행

### 기본 실행

```bash
cd watchdog/codes/01_basic_setup
python watch.py
```

출력 예시:

```
모니터링 시작: .
종료하려면 Ctrl+C를 누르세요.
```

### 파일 변경 테스트

다른 터미널에서:

```bash
# 파일 생성
touch test.txt

# 파일 수정
echo "content" >> test.txt

# 파일 삭제
rm test.txt
```

실행 중인 터미널에서 다음과 같은 출력이 나타납니다:

```
파일이 생성되었습니다: ./test.txt
파일이 수정되었습니다: ./test.txt
파일이 삭제되었습니다: ./test.txt
```

## 3.4 재귀적 모니터링

하위 디렉토리까지 모니터링하려면 `recursive=True`를 사용합니다:

```python
observer.schedule(event_handler, watch_directory, recursive=True)
```

### 예제

```python
# 현재 디렉토리와 모든 하위 디렉토리 모니터링
observer.schedule(event_handler, ".", recursive=True)
```

## 3.5 다양한 이벤트 처리

### 모든 이벤트 처리

```python
class MyHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        """모든 이벤트를 처리"""
        print(f"이벤트 발생: {event.event_type} - {event.src_path}")

    def on_modified(self, event):
        """파일 수정 이벤트"""
        if not event.is_directory:
            print(f"수정: {event.src_path}")

    def on_created(self, event):
        """파일 생성 이벤트"""
        if not event.is_directory:
            print(f"생성: {event.src_path}")

    def on_deleted(self, event):
        """파일 삭제 이벤트"""
        if not event.is_directory:
            print(f"삭제: {event.src_path}")

    def on_moved(self, event):
        """파일 이동 이벤트"""
        print(f"이동: {event.src_path} -> {event.dest_path}")
```

## 3.6 파일 이동 이벤트

파일 이동이나 이름 변경을 감지하려면 `on_moved` 메서드를 사용합니다:

```python
class MyHandler(FileSystemEventHandler):
    def on_moved(self, event):
        print(f"파일 이동: {event.src_path} -> {event.dest_path}")
```

### 테스트

```bash
# 파일 이름 변경
mv old_name.txt new_name.txt

# 파일 이동
mv file.txt subdirectory/file.txt
```

## 3.7 실전 예제

`watchdog/codes/01_basic_setup/` 디렉토리에 다음 파일들이 있습니다:

- `watch.py`: 기본 파일 모니터링 예제
- `watch_recursive.py`: 재귀적 모니터링 예제
- `README.md`: 실행 방법 안내

각 파일을 실행해보며 차이점을 확인해보세요.

## 3.8 주의사항

### 디렉토리 이벤트 필터링

디렉토리 이벤트를 무시하려면:

```python
def on_modified(self, event):
    if event.is_directory:
        return  # 디렉토리 이벤트 무시
    print(f"파일 수정: {event.src_path}")
```

### 이벤트 중복

파일 저장 시 여러 이벤트가 발생할 수 있습니다. 이는 나중에 디바운싱으로 해결합니다 (06_advanced_usage.md 참조).

### 성능 고려사항

많은 파일이 있는 디렉토리를 모니터링할 때는 성능에 주의해야 합니다.

## 3.9 다음 단계

이제 watchdog을 설치하고 기본 사용법을 배웠습니다. 다음 단계:

1. **04_observer_pattern.md**: 옵저버 패턴과 핸들러의 동작 원리 이해

---

**이전: [02_file_events.md](02_file_events.md) | 다음: [04_observer_pattern.md](04_observer_pattern.md) →**

