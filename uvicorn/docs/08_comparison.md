# 8장: Gunicorn/Spring과의 비교 정리

## 8.1 전체 비교표

| 특성 | Spring/Tomcat | Gunicorn | Uvicorn |
|------|--------------|----------|---------|
| **프로토콜** | 서블릿 스펙 | WSGI | ASGI |
| **동시성 모델** | 스레드 풀 | 프로세스 풀 | 이벤트 루프 |
| **I/O 처리** | 블로킹 I/O | 블로킹 I/O | 비동기 I/O |
| **WebSocket** | 지원 | 미지원 | 지원 |
| **비동기 지원** | 제한적 | 제한적 | 완전 지원 |
| **메모리 사용** | 중간 | 높음 | 낮음 |
| **CPU 활용** | 멀티 코어 | 멀티 코어 | 단일 코어 (GIL) |

## 8.2 아키텍처 비교

### Spring/Tomcat

```
클라이언트 요청
    ↓
Tomcat (서블릿 컨테이너)
    ↓
스레드 풀 (Thread Pool)
    ├─→ 스레드 1 → 서블릿 → Spring 컨트롤러
    ├─→ 스레드 2 → 서블릿 → Spring 컨트롤러
    └─→ 스레드 3 → 서블릿 → Spring 컨트롤러
```

**특징**:
- 스레드 기반 동시성
- OS 스레드 스위칭
- 공유 메모리

### Gunicorn

```
클라이언트 요청
    ↓
Gunicorn (마스터 프로세스)
    ↓
워커 프로세스 풀
    ├─→ 워커 1 → WSGI 앱
    ├─→ 워커 2 → WSGI 앱
    └─→ 워커 3 → WSGI 앱
```

**특징**:
- 프로세스 기반 동시성
- 프로세스 간 메모리 격리
- 멀티 코어 활용

### Uvicorn

```
클라이언트 요청
    ↓
Uvicorn (이벤트 루프)
    ↓
비동기 워커
    ├─→ 요청 1 처리 (논블로킹)
    ├─→ 요청 2 처리 (논블로킹)
    └─→ 요청 3 처리 (논블로킹)
```

**특징**:
- 이벤트 루프 기반 동시성
- 단일 프로세스
- 높은 동시성

## 8.3 동시성 처리 비교

### 스레드 모델 (Spring/Tomcat)

```java
@GetMapping("/endpoint")
public String endpoint() {
    // 스레드가 블로킹됨
    String data = db.query();  // 1초 대기
    return data;
}
```

**특징**:
- 각 요청이 별도 스레드에서 처리
- 스레드 수에 비례하여 동시성 확보
- 컨텍스트 스위칭 오버헤드

### 프로세스 모델 (Gunicorn)

```python
def endpoint():
    # 프로세스가 블로킹됨
    data = db.query()  # 1초 대기
    return data
```

**특징**:
- 각 요청이 별도 프로세스에서 처리
- 프로세스 수에 비례하여 동시성 확보
- 메모리 사용량 높음

### 이벤트 루프 모델 (Uvicorn)

```python
async def endpoint():
    # 이벤트 루프가 블로킹되지 않음
    data = await db.query()  # 1초 대기 (다른 작업 가능)
    return data
```

**특징**:
- 단일 이벤트 루프가 여러 요청 처리
- I/O 대기 중에도 다른 요청 처리 가능
- 높은 동시성

## 8.4 성능 특성 비교

### I/O 집약적 작업

| 작업 유형 | Spring/Tomcat | Gunicorn | Uvicorn |
|----------|--------------|----------|---------|
| **DB 쿼리** | 블로킹 | 블로킹 | 논블로킹 ✅ |
| **API 호출** | 블로킹 | 블로킹 | 논블로킹 ✅ |
| **파일 I/O** | 블로킹 | 블로킹 | 논블로킹 ✅ |

**결론**: I/O 집약적 작업에서는 **Uvicorn**이 가장 효율적입니다.

### CPU 집약적 작업

| 작업 유형 | Spring/Tomcat | Gunicorn | Uvicorn |
|----------|--------------|----------|---------|
| **계산 작업** | 효율적 ✅ | 효율적 ✅ | GIL 제약 ⚠️ |
| **이미지 처리** | 효율적 ✅ | 효율적 ✅ | GIL 제약 ⚠️ |

**결론**: CPU 집약적 작업에서는 **Spring/Tomcat** 또는 **Gunicorn**이 더 효율적입니다.

### 동시 연결 수

| 서버 | 동시 연결 수 | 메모리 사용 |
|------|------------|------------|
| **Spring/Tomcat** | 스레드 수에 비례 | 중간 |
| **Gunicorn** | 워커 수에 비례 | 높음 |
| **Uvicorn** | 매우 높음 (이벤트 루프) | 낮음 ✅ |

**결론**: 높은 동시 연결 수가 필요하면 **Uvicorn**이 유리합니다.

## 8.5 사용 시나리오

### Spring/Tomcat을 선택하는 경우

- ✅ 기존 Java 생태계 활용
- ✅ 엔터프라이즈급 기능 필요 (JTA, JMS 등)
- ✅ CPU 집약적 작업
- ✅ 높은 처리량과 낮은 메모리 사용 중요

### Gunicorn을 선택하는 경우

- ✅ Django (기본 모드), Flask 등 전통적인 프레임워크
- ✅ CPU 집약적 작업
- ✅ 프로세스 격리가 필요한 경우
- ✅ 멀티 코어 활용이 중요한 경우

### Uvicorn을 선택하는 경우

- ✅ FastAPI, Django Channels 등 비동기 프레임워크
- ✅ I/O 집약적 작업
- ✅ WebSocket 지원 필요
- ✅ 높은 동시 연결 수 필요
- ✅ 낮은 메모리 사용 중요

## 8.6 하이브리드 접근

### Gunicorn + Uvicorn 워커

프로덕션 환경에서는 두 가지를 결합할 수 있습니다:

```bash
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4
```

**장점**:
- ✅ 멀티 코어 활용 (Gunicorn)
- ✅ 비동기 I/O 처리 (Uvicorn)
- ✅ 프로세스 격리 (안정성)
- ✅ 높은 동시성

**이것이 프로덕션 환경에서 가장 권장되는 방식입니다.**

## 8.7 배포 방식 비교

### Spring/Tomcat: WAR 파일

```bash
# 빌드
mvn clean package

# 배포
cp target/myapp.war $CATALINA_HOME/webapps/
```

### Gunicorn/Uvicorn: Python 패키지

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
gunicorn main:app --worker-class uvicorn.workers.UvicornWorker
```

**차이점**:
- WAR는 컴파일된 바이트코드 포함
- Python은 소스코드 직접 실행

## 8.8 설정 방식 비교

### Spring/Tomcat: server.xml

```xml
<Connector port="8080" 
           maxThreads="200" 
           connectionTimeout="20000" />
```

### Gunicorn: gunicorn.conf.py

```python
bind = "0.0.0.0:8000"
workers = 4
timeout = 30
```

### Uvicorn: 명령줄 옵션

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**공통점**: 모두 설정 파일로 서버 동작 제어  
**차이점**: XML vs Python 설정 파일 vs 명령줄 옵션

## 8.9 핵심 정리

### 공통점

1. **웹 서버 역할**: HTTP 요청을 받아 애플리케이션에 전달
2. **동시성 처리**: 여러 요청을 동시에 처리
3. **설정 파일**: 서버 동작을 설정 파일로 제어
4. **프로덕션 배포**: 리버스 프록시(Nginx/Apache)와 함께 사용

### 차이점

1. **실행 모델**: 스레드 vs 프로세스 vs 이벤트 루프
2. **메모리 관리**: 공유 vs 격리 vs 단일 프로세스
3. **언어**: Java vs Python
4. **프로토콜**: 서블릿 스펙 vs WSGI vs ASGI

### 학습 포인트

Spring/Tomcat 경험자가 Python/Uvicorn을 이해할 때:

1. **역할은 동일**: 둘 다 웹 애플리케이션 서버
2. **구현 방식이 다름**: 스레드 vs 이벤트 루프
3. **프로토콜이 다름**: 서블릿 스펙 vs ASGI
4. **동시성 모델이 다름**: 스레드 풀 vs 이벤트 루프

이러한 차이점을 이해하면 Python 웹 서버를 효과적으로 사용할 수 있습니다.

## 8.10 선택 가이드 요약

| 상황 | 권장 서버 | 이유 |
|------|----------|------|
| FastAPI 사용 | Uvicorn | ASGI 필요 |
| Django (기본) | Gunicorn | WSGI 충분 |
| Django (Channels) | Uvicorn | WebSocket 필요 |
| 높은 동시 연결 | Uvicorn | 이벤트 루프 효율적 |
| CPU 집약적 | Gunicorn/Spring | 멀티 코어 활용 |
| 프로덕션 배포 | Gunicorn + Uvicorn | 최적의 조합 |

---

**이전: [07_config.md](07_config.md) | [목차로 돌아가기](00_chapter.md)**

---

## 마무리

이 교과서를 통해 다음을 학습했습니다:

1. ✅ Uvicorn이 무엇이고 왜 필요한지
2. ✅ ASGI 프로토콜의 동작 원리
3. ✅ Uvicorn 설치 및 기본 사용법
4. ✅ 이벤트 루프와 비동기 처리 원리
5. ✅ FastAPI에서 Uvicorn 사용하기
6. ✅ Django에서 ASGI 모드로 사용하기
7. ✅ 프로덕션 환경 설정 방법
8. ✅ Gunicorn/Spring과의 비교를 통한 통합적 이해

이제 FastAPI나 Django 프로젝트를 프로덕션 환경에 배포할 준비가 되었습니다!

