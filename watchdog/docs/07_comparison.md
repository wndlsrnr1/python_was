# 7장: 다른 도구와의 비교 정리

## 7.1 OS별 네이티브 도구

### Linux: inotify

**inotify**는 Linux 커널의 파일 시스템 이벤트 모니터링 기능입니다.

```python
# inotify 직접 사용 (복잡함)
import inotify.adapters

i = inotify.adapters.Inotify()
i.add_watch('/path/to/watch')

for event in i.event_gen():
    if event is not None:
        (header, type_names, watch_path, filename) = event
        print(f"이벤트: {type_names} - {filename}")
```

**특징**:
- ✅ 매우 빠름
- ✅ 커널 레벨 이벤트
- ❌ Linux 전용
- ❌ 사용법 복잡

### Mac: FSEvents

**FSEvents**는 macOS의 파일 시스템 이벤트 API입니다.

**특징**:
- ✅ 배치 이벤트 처리
- ✅ 성능 최적화
- ❌ Mac 전용
- ❌ 사용법 복잡

### Windows: ReadDirectoryChangesW

**ReadDirectoryChangesW**는 Windows의 파일 변경 감지 API입니다.

**특징**:
- ✅ Windows 네이티브
- ❌ Windows 전용
- ❌ 사용법 복잡

### Watchdog의 장점

Watchdog은 이러한 OS별 차이를 추상화하여:

- ✅ 크로스 플랫폼 (Windows, Linux, Mac 모두 지원)
- ✅ 간단한 API
- ✅ 일관된 사용법

## 7.2 Python의 다른 파일 모니터링 라이브러리

### pyinotify (Linux 전용)

```python
import pyinotify

wm = pyinotify.WatchManager()
mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        print(f"수정: {event.pathname}")

notifier = pyinotify.Notifier(wm, EventHandler())
wm.add_watch('/path/to/watch', mask, rec=True)
notifier.loop()
```

**특징**:
- ✅ Linux에서 빠름
- ❌ Linux 전용
- ❌ 사용법 복잡

### watchdog (현재 학습 중)

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"수정: {event.src_path}")

observer = Observer()
observer.schedule(Handler(), "/path/to/watch", recursive=True)
observer.start()
```

**특징**:
- ✅ 크로스 플랫폼
- ✅ 간단한 API
- ✅ 널리 사용됨

## 7.3 Spring의 파일 감시와 비교

### Java WatchService

```java
WatchService watchService = FileSystems.getDefault().newWatchService();
Path path = Paths.get("/path/to/watch");
path.register(watchService, 
    StandardWatchEventKinds.ENTRY_MODIFY,
    StandardWatchEventKinds.ENTRY_CREATE);

WatchKey key;
while ((key = watchService.take()) != null) {
    for (WatchEvent<?> event : key.pollEvents()) {
        System.out.println("이벤트: " + event.kind() + " - " + event.context());
    }
    key.reset();
}
```

### Python Watchdog

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"이벤트: modified - {event.src_path}")

observer = Observer()
observer.schedule(Handler(), "/path/to/watch", recursive=True)
observer.start()
```

**공통점**:
- 파일 시스템 이벤트 감지
- 비동기 이벤트 처리
- 크로스 플랫폼 지원

**차이점**:
- **Java WatchService**: 저수준 API, 직접 구현 필요
- **Python Watchdog**: 고수준 API, 간단한 사용법

## 7.4 사용 시나리오별 선택 가이드

### 개발 도구 (자동 리로드)

| 도구 | 권장 상황 |
|------|----------|
| **Watchdog** | Django, FastAPI 등 Python 프로젝트 |
| **Spring Boot DevTools** | Spring Boot 프로젝트 |
| **Nodemon** | Node.js 프로젝트 |

### 운영 도구 (로그 모니터링)

| 도구 | 권장 상황 |
|------|----------|
| **Watchdog** | Python 기반 로그 모니터링 |
| **inotify-tools** | Linux 서버 로그 모니터링 |
| **Filebeat** | 대규모 로그 수집 |

### 크로스 플랫폼 필요 시

| 도구 | 플랫폼 지원 |
|------|------------|
| **Watchdog** | ✅ Windows, Linux, Mac |
| **pyinotify** | ❌ Linux만 |
| **Java WatchService** | ✅ Windows, Linux, Mac |

## 7.5 성능 비교

### 이벤트 감지 속도

| 도구 | 속도 | 메모리 사용 |
|------|------|------------|
| **inotify (Linux)** | 매우 빠름 | 낮음 |
| **FSEvents (Mac)** | 빠름 | 낮음 |
| **Watchdog** | 빠름 | 중간 |
| **Java WatchService** | 빠름 | 중간 |

### 동시 모니터링 파일 수

| 도구 | 제한 |
|------|------|
| **inotify** | 매우 많음 (수만 개) |
| **Watchdog** | 많음 (수천 개) |
| **Java WatchService** | 많음 (수천 개) |

## 7.6 핵심 정리

### Watchdog을 선택하는 경우

- ✅ Python 프로젝트
- ✅ 크로스 플랫폼 필요
- ✅ 간단한 API 선호
- ✅ Django/FastAPI 자동 리로드

### 다른 도구를 선택하는 경우

- **inotify/pyinotify**: Linux 전용, 최고 성능 필요
- **Java WatchService**: Java 프로젝트
- **Spring Boot DevTools**: Spring Boot 프로젝트

### 공통점

모든 도구는:
- 파일 시스템 이벤트 감지
- 비동기 이벤트 처리
- 개발 생산성 향상

---

**이전: [06_advanced_usage.md](06_advanced_usage.md) | [목차로 돌아가기](00_chapter.md)**

---

## 마무리

이 교과서를 통해 다음을 학습했습니다:

1. ✅ Watchdog이 무엇이고 왜 필요한지
2. ✅ 파일 시스템 이벤트의 종류와 동작 방식
3. ✅ Watchdog 설치 및 기본 사용법
4. ✅ 옵저버 패턴과 핸들러의 동작 원리
5. ✅ Django/FastAPI에서 자동 리로드가 어떻게 동작하는지
6. ✅ 고급 사용법 (필터링, 디바운싱 등)
7. ✅ 다른 도구와의 비교를 통한 통합적 이해

이제 Python 프로젝트에서 파일 모니터링을 효과적으로 사용할 수 있습니다!

