# 2장: 파일 시스템 이벤트 이해

## 2.1 파일 시스템 이벤트란?

파일 시스템 이벤트는 파일이나 디렉토리에 발생하는 변경 사항을 나타냅니다.

### 이벤트의 종류

Watchdog은 다음과 같은 이벤트를 감지합니다:

- **파일 생성** (`on_created`): 새 파일이 생성됨
- **파일 수정** (`on_modified`): 기존 파일이 수정됨
- **파일 삭제** (`on_deleted`): 파일이 삭제됨
- **파일 이동** (`on_moved`): 파일이 이동되거나 이름이 변경됨
- **디렉토리 생성** (`on_created`): 새 디렉토리가 생성됨
- **디렉토리 삭제** (`on_deleted`): 디렉토리가 삭제됨

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring WatchService | Watchdog |
|---------------------|----------|
| `ENTRY_CREATE` | `on_created` |
| `ENTRY_MODIFY` | `on_modified` |
| `ENTRY_DELETE` | `on_deleted` |

## 2.2 이벤트 객체 구조

### FileSystemEvent

모든 파일 시스템 이벤트는 `FileSystemEvent` 객체로 표현됩니다:

```python
class FileSystemEvent:
    src_path: str      # 이벤트가 발생한 경로
    event_type: str   # 이벤트 타입
    is_directory: bool # 디렉토리인지 여부
```

### FileModifiedEvent

파일 수정 이벤트:

```python
class FileModifiedEvent(FileSystemEvent):
    event_type = 'modified'
```

### FileCreatedEvent

파일 생성 이벤트:

```python
class FileCreatedEvent(FileSystemEvent):
    event_type = 'created'
```

### FileDeletedEvent

파일 삭제 이벤트:

```python
class FileDeletedEvent(FileSystemEvent):
    event_type = 'deleted'
```

### FileMovedEvent

파일 이동 이벤트:

```python
class FileMovedEvent(FileSystemEvent):
    src_path: str      # 원본 경로
    dest_path: str    # 목적지 경로
    event_type = 'moved'
```

## 2.3 이벤트 발생 시나리오

### 파일 생성 시나리오

1. 사용자가 새 파일 생성: `touch new_file.txt`
2. Watchdog이 이벤트 감지
3. `on_created` 핸들러 호출
4. 이벤트 객체에 파일 경로 포함

### 파일 수정 시나리오

1. 사용자가 파일 편집: `echo "content" >> file.txt`
2. Watchdog이 이벤트 감지
3. `on_modified` 핸들러 호출
4. 이벤트 객체에 수정된 파일 경로 포함

### 파일 삭제 시나리오

1. 사용자가 파일 삭제: `rm file.txt`
2. Watchdog이 이벤트 감지
3. `on_deleted` 핸들러 호출
4. 이벤트 객체에 삭제된 파일 경로 포함

### 파일 이동 시나리오

1. 사용자가 파일 이동: `mv old_name.txt new_name.txt`
2. Watchdog이 이벤트 감지
3. `on_moved` 핸들러 호출
4. 이벤트 객체에 원본 경로와 목적지 경로 포함

## 2.4 디렉토리 이벤트

### 디렉토리 모니터링

디렉토리를 모니터링하면 해당 디렉토리 내의 모든 파일 변경을 감지할 수 있습니다:

```python
observer.schedule(handler, "/path/to/directory", recursive=True)
```

- `recursive=True`: 하위 디렉토리까지 재귀적으로 모니터링
- `recursive=False`: 현재 디렉토리만 모니터링

### 디렉토리 이벤트 예제

```python
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            print(f"디렉토리 생성: {event.src_path}")
        else:
            print(f"파일 생성: {event.src_path}")
```

## 2.5 이벤트 필터링

### 디렉토리 이벤트 무시

일부 경우 디렉토리 이벤트를 무시하고 싶을 수 있습니다:

```python
class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return  # 디렉토리 이벤트 무시
        print(f"파일 수정: {event.src_path}")
```

### 특정 확장자만 감시

특정 확장자의 파일만 감시할 수도 있습니다:

```python
class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith('.py'):
            return  # .py 파일만 처리
        print(f"Python 파일 수정: {event.src_path}")
```

## 2.6 이벤트 중복 문제

### 문제 상황

파일을 저장할 때 여러 이벤트가 발생할 수 있습니다:

1. 임시 파일 생성
2. 원본 파일 삭제
3. 새 파일 생성
4. 파일 수정

이로 인해 같은 파일에 대해 여러 번 이벤트가 발생할 수 있습니다.

### 해결 방법

이 문제는 나중에 **디바운싱(Debouncing)**으로 해결합니다 (06_advanced_usage.md 참조).

## 2.7 OS별 차이점

### Linux (inotify)

- 빠른 이벤트 감지
- 많은 파일 동시 모니터링 가능
- 디렉토리 재귀 모니터링 효율적

### Mac (FSEvents)

- 파일 시스템 레벨 이벤트
- 배치 이벤트 처리
- 성능 최적화됨

### Windows (ReadDirectoryChangesW)

- Windows API 사용
- 모든 플랫폼과 호환
- 일부 제한 사항 있음

**Watchdog의 장점**: 이러한 OS별 차이를 추상화하여 동일한 API로 사용 가능

## 2.8 다음 단계

이제 파일 시스템 이벤트가 어떻게 동작하는지 이해했습니다. 다음 단계:

1. **03_basic_setup.md**: 실제로 watchdog을 설치하고 사용해보기

---

**이전: [01_overview.md](01_overview.md) | 다음: [03_basic_setup.md](03_basic_setup.md) →**

