# 6장: uvicorn과 gunicorn 이해

## 6.1 Uvicorn이란?

**Uvicorn**은 Python ASGI 애플리케이션을 실행하기 위한 **ASGI HTTP 서버**입니다.

### FastAPI와 Uvicorn의 관계

FastAPI는 웹 프레임워크이고, Uvicorn은 서버입니다:

```
클라이언트 요청
    ↓
Uvicorn (ASGI 서버)
    ↓
FastAPI (웹 프레임워크)
    ↓
비즈니스 로직
```

이 관계는 Spring Boot와 Tomcat의 관계와 유사합니다:

```
클라이언트 요청
    ↓
Tomcat (서블릿 컨테이너)
    ↓
Spring Boot (웹 프레임워크)
    ↓
비즈니스 로직
```

### Spring/Tomcat과의 비교

| Spring/Tomcat | FastAPI/Uvicorn |
|--------------|----------------|
| Tomcat (서블릿 컨테이너) | Uvicorn (ASGI 서버) |
| 스레드 풀 모델 | 이벤트 루프 기반 |
| 동기 처리 | 비동기 처리 |
| WAR 파일 배포 | Python 모듈 배포 |

## 6.2 Uvicorn 단독 사용

### 개발 환경

개발 환경에서는 Uvicorn을 단독으로 사용하는 것이 일반적입니다:

```bash
uvicorn main:app --reload
```

**장점**:
- 간단한 설정
- 자동 리로드 지원 (`--reload`)
- 빠른 시작

**단점**:
- 단일 프로세스 (멀티프로세싱 없음)
- 프로세스가 죽으면 서비스 중단

### 프로덕션 환경 (소규모)

소규모 프로덕션 환경에서도 Uvicorn 단독 사용이 가능합니다:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**주의**: 단일 프로세스이므로 높은 트래픽에는 부적합합니다.

## 6.3 Gunicorn + Uvicorn 워커

### 왜 Gunicorn을 사용하는가?

프로덕션 환경에서는 **Gunicorn + Uvicorn 워커** 조합을 권장합니다.

**Gunicorn**은:
- 여러 워커 프로세스를 관리
- 프로세스가 죽으면 자동 재시작
- 로드 밸런싱

**Uvicorn 워커**는:
- 각 워커에서 ASGI 애플리케이션 실행
- 비동기 처리

### 아키텍처

```
클라이언트 요청
    ↓
Gunicorn (마스터 프로세스)
    ↓
┌─────────┬─────────┬─────────┐
│ Worker1 │ Worker2 │ Worker3 │ (Uvicorn 워커)
│         │         │         │
│ FastAPI │ FastAPI │ FastAPI │
└─────────┴─────────┴─────────┘
```

이 구조는 Spring Boot의 여러 인스턴스를 로드 밸런서 뒤에 두는 것과 유사합니다.

### 설치

```bash
pip install gunicorn uvicorn
```

### 실행

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

여기서:
- `-w 4`: 워커 수 4개
- `-k uvicorn.workers.UvicornWorker`: Uvicorn 워커 사용

### 설정 파일 사용

`gunicorn.conf.py` 파일 생성:

```python
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

실행:

```bash
gunicorn main:app -c gunicorn.conf.py
```

## 6.4 워커 수 결정

### 워커 수 공식

일반적인 공식:

```
워커 수 = (CPU 코어 수 × 2) + 1
```

예: 4코어 CPU → `(4 × 2) + 1 = 9` 워커

### 실제 고려 사항

- **CPU 집약적 작업**: 코어 수와 비슷하게
- **I/O 집약적 작업**: 더 많은 워커 가능 (비동기 처리)
- **메모리 제약**: 워커당 메모리 사용량 고려

### Spring과 비교

**Spring Boot**:
- 스레드 풀 크기 설정
- 일반적으로 200-500 스레드

**Gunicorn + Uvicorn**:
- 프로세스 기반 (워커 수)
- 일반적으로 4-8 워커

## 6.5 실습 예제

`fastapi/codes/04_server_setup/` 디렉토리에 서버 설정 예제가 있습니다.

### Uvicorn 단독 실행

```bash
cd fastapi/codes/04_server_setup
uvicorn main:app --reload
```

### Gunicorn + Uvicorn 실행

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

또는 설정 파일 사용:

```bash
gunicorn main:app -c gunicorn.conf.py
```

## 6.6 Spring/Tomcat과의 비교

### 아키텍처 비교

| 특성 | Spring/Tomcat | Gunicorn + Uvicorn |
|------|--------------|-------------------|
| **서버** | Tomcat | Gunicorn |
| **프레임워크** | Spring Boot | FastAPI |
| **동시성 모델** | 스레드 풀 | 프로세스 + 이벤트 루프 |
| **I/O 처리** | 블로킹 I/O | 비동기 I/O |
| **메모리 사용** | 스레드당 스택 메모리 | 프로세스당 메모리 |

### 배포 방식 비교

**Spring Boot**:
```bash
# WAR 파일로 빌드
mvn package

# Tomcat에 배포
cp target/myapp.war $TOMCAT_HOME/webapps/
```

**FastAPI**:
```bash
# Python 모듈로 실행
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 6.7 언제 무엇을 사용할까?

### Uvicorn 단독

- ✅ 개발 환경
- ✅ 소규모 프로덕션 (트래픽 낮음)
- ✅ 빠른 프로토타이핑

### Gunicorn + Uvicorn

- ✅ 프로덕션 환경
- ✅ 높은 트래픽
- ✅ 안정성 요구

## 6.8 다음 단계

이제 uvicorn과 gunicorn의 역할을 이해했습니다. 다음 단계:

1. **07_production.md**: 프로덕션 배포 준비
2. **08_comparison.md**: Spring과의 종합 비교

---

**이전: [05_routing.md](05_routing.md) | 다음: [07_production.md](07_production.md) →**

