# 6장: 고급 사용법

## 6.1 파일 필터링

### 특정 확장자만 감시

특정 확장자의 파일만 감시하려면 핸들러에서 필터링합니다:

```python
from watchdog.events import FileSystemEventHandler

class PythonFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.py'):
            return  # Python 파일만 처리
        print(f"Python 파일 수정: {event.src_path}")
```

### 패턴 매칭

더 복잡한 필터링이 필요하면 정규식을 사용합니다:

```python
import re
from watchdog.events import FileSystemEventHandler

class PatternHandler(FileSystemEventHandler):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if self.pattern.match(event.src_path):
            print(f"매칭 파일 수정: {event.src_path}")
```

## 6.2 디바운싱 (Debouncing)

### 문제 상황

파일을 저장할 때 여러 이벤트가 빠르게 연속으로 발생할 수 있습니다:

1. 임시 파일 생성
2. 원본 파일 삭제
3. 새 파일 생성
4. 파일 수정

이로 인해 같은 파일에 대해 여러 번 핸들러가 호출됩니다.

### 해결 방법: 디바운싱

디바운싱은 연속된 이벤트를 일정 시간 동안 모아서 한 번만 처리하는 기법입니다:

```python
import time
from watchdog.events import FileSystemEventHandler
from collections import defaultdict

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, delay=1.0):
        self.delay = delay
        self.pending_events = defaultdict(float)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        # 마지막 이벤트 시간 기록
        self.pending_events[event.src_path] = time.time()
        # 일정 시간 후 처리
        time.sleep(self.delay)
        # 아직 대기 중인 이벤트인지 확인
        if self.pending_events.get(event.src_path) == time.time() - self.delay:
            print(f"파일 수정: {event.src_path}")
            del self.pending_events[event.src_path]
```

### 더 나은 디바운싱 구현

스레드를 사용한 더 정교한 디바운싱:

```python
import threading
import time
from watchdog.events import FileSystemEventHandler
from collections import defaultdict

class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, delay=1.0):
        self.delay = delay
        self.pending_events = defaultdict(list)
        self.lock = threading.Lock()
    
    def _process_event(self, file_path):
        """지연 후 이벤트 처리"""
        time.sleep(self.delay)
        with self.lock:
            if file_path in self.pending_events:
                print(f"파일 수정: {file_path}")
                del self.pending_events[file_path]
    
    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        with self.lock:
            if file_path not in self.pending_events:
                thread = threading.Thread(target=self._process_event, args=(file_path,))
                thread.daemon = True
                thread.start()
            self.pending_events[file_path].append(time.time())
```

## 6.3 다중 디렉토리 모니터링

여러 디렉토리를 동시에 모니터링할 수 있습니다:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"수정: {event.src_path}")

handler = MyHandler()
observer = Observer()

# 여러 디렉토리 등록
observer.schedule(handler, "/path/to/dir1", recursive=False)
observer.schedule(handler, "/path/to/dir2", recursive=False)
observer.schedule(handler, "/path/to/dir3", recursive=False)

observer.start()
```

## 6.4 이벤트 큐 사용

대량의 이벤트를 처리할 때는 큐를 사용하는 것이 좋습니다:

```python
import queue
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class QueueHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        self.event_queue = event_queue
    
    def on_modified(self, event):
        if not event.is_directory:
            self.event_queue.put(event)

def process_events(event_queue):
    """이벤트 처리 스레드"""
    while True:
        try:
            event = event_queue.get(timeout=1)
            print(f"처리: {event.src_path}")
            event_queue.task_done()
        except queue.Empty:
            continue

# 이벤트 큐 생성
event_queue = queue.Queue()

# 처리 스레드 시작
processor = threading.Thread(target=process_events, args=(event_queue,))
processor.daemon = True
processor.start()

# 핸들러와 옵저버 설정
handler = QueueHandler(event_queue)
observer = Observer()
observer.schedule(handler, ".", recursive=False)
observer.start()
```

## 6.5 실전 예제

`watchdog/codes/05_advanced_example/` 디렉토리에 고급 예제가 있습니다:

- `filtered_handler.py`: 파일 필터링 예제
- `debounced_handler.py`: 디바운싱 예제
- `multi_directory.py`: 다중 디렉토리 모니터링 예제

각 예제를 실행해보며 차이점을 확인해보세요.

## 6.6 성능 최적화

### 불필요한 이벤트 무시

```python
class OptimizedHandler(FileSystemEventHandler):
    def __init__(self):
        self.ignored_patterns = ['.pyc', '__pycache__', '.git']
    
    def should_ignore(self, path):
        """무시할 경로인지 확인"""
        for pattern in self.ignored_patterns:
            if pattern in path:
                return True
        return False
    
    def on_modified(self, event):
        if event.is_directory or self.should_ignore(event.src_path):
            return
        print(f"수정: {event.src_path}")
```

### 비동기 처리

많은 파일을 처리할 때는 비동기 처리를 고려합니다:

```python
import asyncio
from watchdog.events import FileSystemEventHandler

class AsyncHandler(FileSystemEventHandler):
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    async def process_file(self, file_path):
        """비동기 파일 처리"""
        # 파일 처리 로직
        await asyncio.sleep(0.1)
        print(f"처리 완료: {file_path}")
    
    def on_modified(self, event):
        if not event.is_directory:
            self.loop.run_until_complete(
                self.process_file(event.src_path)
            )
```

## 6.7 다음 단계

이제 watchdog의 고급 사용법을 배웠습니다. 다음 단계:

1. **07_comparison.md**: 다른 도구와의 비교를 통한 통합적 이해

---

**이전: [05_auto_reload.md](05_auto_reload.md) | 다음: [07_comparison.md](07_comparison.md) →**

