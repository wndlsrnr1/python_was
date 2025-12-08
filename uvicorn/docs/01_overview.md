# 1장: 개요 및 왜 필요한가

## 1.1 Uvicorn이란?

**Uvicorn**은 Python 웹 애플리케이션을 실행하기 위한 **ASGI HTTP 서버**입니다.

### 이름의 의미

- **Uvicorn**: "Unicorn"의 변형
- **ASGI**: Asynchronous Server Gateway Interface (비동기 서버 게이트웨이 인터페이스)

### Spring/Tomcat/Gunicorn과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring/Tomcat | Gunicorn | Uvicorn |
|--------------|----------|---------|
| Tomcat (서블릿 컨테이너) | WSGI 서버 | ASGI 서버 |
| 스레드 풀 모델 | 프로세스 기반 워커 | 이벤트 루프 기반 |
| 동기 처리 | 동기 처리 (기본) | 비동기 처리 |
| WAR 파일 배포 | Python 모듈 배포 | Python 모듈 배포 |

**핵심 차이점**: 
- **Tomcat**: Java 서블릿을 실행하는 컨테이너 (스레드 기반)
- **Gunicorn**: Python WSGI 애플리케이션을 실행하는 서버 (프로세스 기반)
- **Uvicorn**: Python ASGI 애플리케이션을 실행하는 서버 (이벤트 루프 기반)

## 1.2 왜 필요한가?

### 개발 서버의 한계

FastAPI나 Django를 개발할 때 다음과 같이 실행해봤을 것입니다:

```bash
# FastAPI
uvicorn main:app --reload

# Django
python manage.py runserver
```

이 명령어들은 **개발용 서버**입니다. 개발 서버의 문제점:

1. **단일 스레드**: 한 번에 하나의 요청만 처리 (기본)
2. **성능 부족**: 동시 접속자 수가 많으면 응답 지연
3. **안정성 부족**: 프로덕션 환경에서 충돌 시 복구 불가
4. **보안 취약**: 개발 편의 기능이 포함되어 있어 보안 위험

### 프로덕션 환경의 요구사항

실제 서비스를 운영하려면:

- **높은 동시성**: 여러 요청을 동시에 효율적으로 처리
- **비동기 지원**: I/O 대기 시간을 활용한 비동기 처리
- **WebSocket 지원**: 실시간 통신 지원
- **안정성**: 프로세스가 죽어도 자동 재시작
- **성능**: 최적화된 요청 처리

이러한 요구사항을 만족하는 것이 **Uvicorn**입니다.

## 1.3 ASGI 서버의 필요성

### WSGI의 한계

**WSGI** (Web Server Gateway Interface)는 Python 웹 애플리케이션과 서버 간의 표준 인터페이스입니다. 하지만:

- ❌ **동기만 지원**: 비동기 처리가 어려움
- ❌ **WebSocket 미지원**: 실시간 통신 불가
- ❌ **HTTP/2 제한적**: 최신 프로토콜 지원 부족

### ASGI의 등장

**ASGI** (Asynchronous Server Gateway Interface)는 WSGI의 비동기 버전입니다:

- ✅ **비동기 지원**: `async/await`를 통한 비동기 처리
- ✅ **WebSocket 지원**: 실시간 양방향 통신
- ✅ **HTTP/2 완전 지원**: 최신 프로토콜 지원
- ✅ **백그라운드 작업**: 장기 실행 작업 지원

### 언제 무엇을 사용할까?

| 상황 | 사용할 서버 |
|------|------------|
| Django (기본 모드) | Gunicorn (WSGI) |
| Django (Channels, WebSocket) | Uvicorn (ASGI) |
| FastAPI | Uvicorn (ASGI) |
| Flask | Gunicorn (WSGI) |
| Starlette | Uvicorn (ASGI) |

**핵심**: 비동기나 WebSocket이 필요하면 **Uvicorn**, 전통적인 동기 프레임워크면 **Gunicorn**

## 1.4 Uvicorn의 역할

Uvicorn은 다음과 같은 역할을 합니다:

1. **HTTP 요청 수신**: 클라이언트로부터 HTTP 요청을 받음
2. **ASGI 애플리케이션 호출**: Python 애플리케이션의 ASGI 인터페이스를 호출
3. **비동기 처리**: 이벤트 루프를 통한 비동기 I/O 처리
4. **응답 전송**: 애플리케이션의 응답을 클라이언트에 전송
5. **WebSocket 지원**: WebSocket 연결 관리

### 아키텍처 개요

```
클라이언트 요청
    ↓
Uvicorn (이벤트 루프)
    ↓
비동기 워커
    ↓
FastAPI/Django ASGI 애플리케이션
    ↓
응답 반환
```

이 구조는 Spring의 Tomcat이 여러 스레드로 요청을 처리하는 것과 유사하지만, **이벤트 루프 기반**이라는 차이가 있습니다.

## 1.5 비동기 처리의 장점

### 동기 처리의 문제

전통적인 동기 처리 방식:

```python
# 동기 방식 (Gunicorn + Django)
def get_user_data(user_id):
    user = db.query(user_id)  # DB 쿼리 (1초 대기)
    posts = api.get_posts(user_id)  # API 호출 (2초 대기)
    return {"user": user, "posts": posts}  # 총 3초 소요
```

**문제점**: 각 요청이 순차적으로 처리되어, 10개 요청이 오면 30초가 걸립니다.

### 비동기 처리의 해결

비동기 처리 방식 (Uvicorn + FastAPI):

```python
# 비동기 방식 (Uvicorn + FastAPI)
async def get_user_data(user_id):
    user = await db.query(user_id)  # DB 쿼리 (1초 대기, 다른 작업 가능)
    posts = await api.get_posts(user_id)  # API 호출 (2초 대기, 다른 작업 가능)
    return {"user": user, "posts": posts}  # 총 3초지만 동시에 여러 요청 처리
```

**장점**: I/O 대기 시간 동안 다른 요청을 처리할 수 있어, 10개 요청도 약 3초 내에 처리 가능합니다.

### 실제 성능 비교

| 상황 | 동기 처리 (Gunicorn) | 비동기 처리 (Uvicorn) |
|------|---------------------|---------------------|
| CPU 집약적 작업 | ✅ 효율적 | ⚠️ GIL 제약 |
| I/O 집약적 작업 | ⚠️ 대기 시간 낭비 | ✅ 효율적 |
| 동시 연결 수 | 제한적 (워커 수에 비례) | 매우 높음 (이벤트 루프) |
| 메모리 사용 | 높음 (프로세스당) | 낮음 (단일 프로세스) |

## 1.6 Spring/Tomcat과의 비교

### 아키텍처 비교

| 특성 | Spring/Tomcat | Uvicorn |
|------|--------------|---------|
| **동시성 모델** | 스레드 풀 | 이벤트 루프 |
| **I/O 처리** | 블로킹 I/O | 비동기 I/O |
| **메모리 사용** | 스레드당 스택 메모리 | 단일 프로세스 |
| **컨텍스트 스위칭** | OS 스레드 스위칭 | 사용자 공간 스위칭 |

### 비동기 처리 비교

**Spring (비동기 모드)**:
```java
@GetMapping("/async")
public CompletableFuture<String> async() {
    return CompletableFuture.supplyAsync(() -> {
        // 비동기 작업
        return "result";
    });
}
```

**FastAPI (비동기 모드)**:
```python
@app.get("/async")
async def async_endpoint():
    # 비동기 작업
    return "result"
```

**공통점**: 둘 다 비동기 처리를 지원하지만, Spring은 스레드 풀을 사용하고, Uvicorn은 이벤트 루프를 사용합니다.

## 1.7 다음 단계

이제 uvicorn이 무엇인지, 왜 필요한지 이해했습니다. 다음 단계:

1. **02_asgi_protocol.md**: ASGI 프로토콜이 어떻게 동작하는지 학습
2. **03_basic_setup.md**: 실제로 설치하고 실행해보기

---

**다음: [02_asgi_protocol.md](02_asgi_protocol.md) →**

