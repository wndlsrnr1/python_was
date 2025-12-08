# 4장: 옵저버 패턴 및 핸들러 이해

## 4.1 옵저버 패턴이란?

옵저버 패턴은 객체의 상태 변화를 관찰하는 관찰자들의 목록을 객체에 등록하여, 상태 변화가 있을 때마다 메서드 등을 통해 객체가 직접 목록의 각 관찰자에게 통지하도록 하는 디자인 패턴입니다.

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring | Watchdog |
|--------|----------|
| `ApplicationListener` | `FileSystemEventHandler` |
| `@EventListener` | `on_modified`, `on_created` 등 |
| 이벤트 발행 | 파일 시스템 이벤트 발생 |

**공통점**: 둘 다 이벤트 기반 프로그래밍 패턴을 사용합니다.

## 4.2 Watchdog의 옵저버 패턴

### 구성 요소

1. **Observer (옵저버)**: 파일 시스템을 감시하는 객체
2. **EventHandler (핸들러)**: 이벤트를 처리하는 객체
3. **FileSystemEvent (이벤트)**: 파일 시스템 변경 사항

### 구조

```
Observer (감시자)
    ↓
파일 시스템 모니터링
    ↓
이벤트 발생
    ↓
EventHandler (처리자)
    ↓
사용자 정의 동작 실행
```

## 4.3 FileSystemEventHandler

`FileSystemEventHandler`는 모든 파일 시스템 이벤트 핸들러의 기본 클래스입니다.

### 기본 구조

```python
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        pass

    def on_created(self, event):
        """파일 생성 이벤트 처리"""
        pass

    def on_deleted(self, event):
        """파일 삭제 이벤트 처리"""
        pass

    def on_moved(self, event):
        """파일 이동 이벤트 처리"""
        pass

    def on_any_event(self, event):
        """모든 이벤트 처리"""
        pass
```

### 메서드 오버라이딩

필요한 이벤트만 처리하도록 메서드를 오버라이딩합니다:

```python
class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"파일 수정: {event.src_path}")
```

## 4.4 커스텀 핸들러 작성

### 기본 예제

`watchdog/codes/02_handler_example/custom_handler.py`:

```python
from watchdog.events import FileSystemEventHandler
import os

class LoggingHandler(FileSystemEventHandler):
    """파일 변경을 로그로 기록하는 핸들러"""
    
    def __init__(self, log_file="file_changes.log"):
        self.log_file = log_file
    
    def _log(self, message):
        """로그 파일에 기록"""
        with open(self.log_file, "a") as f:
            f.write(f"{message}\n")
        print(message)
    
    def on_created(self, event):
        if not event.is_directory:
            self._log(f"생성: {event.src_path}")
    
    def on_modified(self, event):
        if not event.is_directory:
            self._log(f"수정: {event.src_path}")
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._log(f"삭제: {event.src_path}")
```

### 사용 예제

```python
from watchdog.observers import Observer
from custom_handler import LoggingHandler

handler = LoggingHandler()
observer = Observer()
observer.schedule(handler, ".", recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

## 4.5 여러 핸들러 사용

하나의 옵저버에 여러 핸들러를 등록할 수 있습니다:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler1(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"핸들러1: {event.src_path}")

class Handler2(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"핸들러2: {event.src_path}")

observer = Observer()
observer.schedule(Handler1(), ".", recursive=False)
observer.schedule(Handler2(), ".", recursive=False)
observer.start()
```

## 4.6 Spring의 리스너 패턴과 비교

### Spring 이벤트 리스너

```java
@Component
public class MyEventListener implements ApplicationListener<MyEvent> {
    @Override
    public void onApplicationEvent(MyEvent event) {
        System.out.println("이벤트 발생: " + event.getMessage());
    }
}
```

### Watchdog 핸들러

```python
class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"이벤트 발생: {event.src_path}")
```

**공통점**: 
- 이벤트 기반 프로그래밍
- 관찰자 패턴 사용
- 이벤트 발생 시 자동 호출

**차이점**:
- **Spring**: 애플리케이션 레벨 이벤트
- **Watchdog**: 파일 시스템 레벨 이벤트

## 4.7 실전 예제

`watchdog/codes/02_handler_example/` 디렉토리에 다음 예제들이 있습니다:

- `custom_handler.py`: 커스텀 핸들러 예제
- `multiple_handlers.py`: 여러 핸들러 사용 예제
- `filtered_handler.py`: 필터링 핸들러 예제

각 예제를 실행해보며 차이점을 확인해보세요.

## 4.8 핸들러 작성 팁

### 이벤트 타입 확인

```python
def on_any_event(self, event):
    if event.event_type == 'modified':
        print("수정 이벤트")
    elif event.event_type == 'created':
        print("생성 이벤트")
```

### 디렉토리 필터링

```python
def on_modified(self, event):
    if event.is_directory:
        return  # 디렉토리 이벤트 무시
    # 파일 이벤트만 처리
    print(f"파일 수정: {event.src_path}")
```

### 에러 처리

```python
def on_modified(self, event):
    try:
        # 파일 처리 로직
        process_file(event.src_path)
    except Exception as e:
        print(f"에러 발생: {e}")
```

## 4.9 다음 단계

이제 옵저버 패턴과 핸들러의 동작 원리를 이해했습니다. 다음 단계:

1. **05_auto_reload.md**: Django/FastAPI에서 자동 리로드가 어떻게 동작하는지

---

**이전: [03_basic_setup.md](03_basic_setup.md) | 다음: [05_auto_reload.md](05_auto_reload.md) →**

