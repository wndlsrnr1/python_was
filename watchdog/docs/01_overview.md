# 1장: 개요 및 왜 필요한가

## 1.1 Watchdog이란?

**Watchdog**은 Python에서 파일 시스템 이벤트를 모니터링하는 라이브러리입니다.

### 이름의 의미

- **Watchdog**: "파일을 감시하는 개"라는 의미
- 파일이나 디렉토리의 변경 사항을 감지하고 알림을 제공

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring | Python/Watchdog |
|--------|----------------|
| `java.nio.file.WatchService` | `watchdog.observers` |
| 이벤트 리스너 | `FileSystemEventHandler` |
| Spring Boot DevTools (자동 리로드) | Django/FastAPI 자동 리로드 |

**핵심 차이점**: 
- **Java WatchService**: Java 표준 라이브러리의 파일 감시 기능
- **Watchdog**: Python에서 크로스 플랫폼 파일 모니터링을 제공하는 라이브러리

## 1.2 왜 필요한가?

### 개발 중의 불편함

코드를 수정할 때마다:

1. 서버를 수동으로 재시작해야 함
2. 변경 사항을 확인하기 위해 매번 새로고침
3. 개발 속도 저하

### 자동 리로드의 필요성

개발 중에는 다음과 같은 기능이 필요합니다:

- ✅ **파일 변경 감지**: 코드 파일이 수정되면 자동으로 감지
- ✅ **자동 재시작**: 서버를 자동으로 재시작하여 변경 사항 반영
- ✅ **즉시 반영**: 수정 후 바로 결과 확인 가능

이러한 기능을 제공하는 것이 **Watchdog**입니다.

## 1.3 Django/FastAPI에서의 활용

### Django의 자동 리로드

```bash
python manage.py runserver
```

이 명령어를 실행하면:
- 코드 파일 변경 시 자동으로 감지
- 서버 자동 재시작
- 변경 사항 즉시 반영

**내부 동작**: Django는 watchdog을 사용하여 파일 변경을 감지합니다.

### FastAPI/Uvicorn의 자동 리로드

```bash
uvicorn main:app --reload
```

이 명령어를 실행하면:
- 코드 파일 변경 시 자동으로 감지
- 서버 자동 재시작
- 변경 사항 즉시 반영

**내부 동작**: Uvicorn은 watchdog을 사용하여 파일 변경을 감지합니다.

### Spring Boot DevTools와 비교

Spring Boot DevTools도 유사한 기능을 제공합니다:

```java
// application.properties
spring.devtools.restart.enabled=true
```

**공통점**: 
- 파일 변경 감지
- 자동 재시작
- 개발 생산성 향상

**차이점**:
- **Spring Boot DevTools**: Java WatchService 사용
- **Django/FastAPI**: Watchdog 사용

## 1.4 Watchdog의 역할

Watchdog은 다음과 같은 역할을 합니다:

1. **파일 시스템 모니터링**: 지정된 디렉토리나 파일을 감시
2. **이벤트 감지**: 파일 생성, 수정, 삭제 등의 이벤트 감지
3. **이벤트 알림**: 이벤트 발생 시 핸들러 호출
4. **크로스 플랫폼**: Windows, Linux, Mac 모두 지원

### 아키텍처 개요

```
파일 시스템 변경
    ↓
Watchdog (옵저버)
    ↓
이벤트 감지
    ↓
핸들러 호출
    ↓
사용자 정의 동작 실행
```

이 구조는 Spring의 이벤트 리스너 패턴과 유사합니다.

## 1.5 파일 모니터링의 활용 사례

### 개발 도구

- **자동 리로드**: Django, FastAPI, Flask 등
- **테스트 자동 실행**: 파일 변경 시 테스트 자동 실행
- **빌드 자동화**: 소스 코드 변경 시 자동 빌드

### 운영 도구

- **로그 모니터링**: 로그 파일 변경 감지
- **설정 파일 감시**: 설정 변경 시 자동 재로드
- **백업 트리거**: 파일 변경 시 자동 백업

### 일반적인 사용 예

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"파일이 수정되었습니다: {event.src_path}")

observer = Observer()
observer.schedule(MyHandler(), path="/path/to/watch", recursive=True)
observer.start()
```

## 1.6 Spring의 파일 감시와 비교

### Java WatchService

```java
WatchService watchService = FileSystems.getDefault().newWatchService();
Path path = Paths.get("/path/to/watch");
path.register(watchService, StandardWatchEventKinds.ENTRY_MODIFY);

WatchKey key;
while ((key = watchService.take()) != null) {
    for (WatchEvent<?> event : key.pollEvents()) {
        System.out.println("파일 변경: " + event.context());
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
        print(f"파일 변경: {event.src_path}")

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

## 1.7 다음 단계

이제 watchdog이 무엇인지, 왜 필요한지 이해했습니다. 다음 단계:

1. **02_file_events.md**: 파일 시스템 이벤트가 어떻게 동작하는지 학습
2. **03_basic_setup.md**: 실제로 설치하고 사용해보기

---

**다음: [02_file_events.md](02_file_events.md) →**

