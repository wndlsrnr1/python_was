# 8장: Spring/Tomcat과의 비교 정리

## 8.1 아키텍처 비교

### 프로세스 모델 vs 스레드 모델

| 특성 | Spring/Tomcat | Python/Gunicorn |
|------|--------------|-----------------|
| **실행 단위** | 스레드 (Thread) | 프로세스 (Process) |
| **메모리 공유** | 공유 힙 메모리 | 프로세스별 독립 메모리 |
| **장점** | 메모리 효율적, 컨텍스트 스위칭 빠름 | 프로세스 격리, 안정성 높음 |
| **단점** | 스레드 안전성 고려 필요 | 메모리 사용량 큼 |

### 요청 처리 흐름

**Spring/Tomcat**:
```
요청 → Tomcat 스레드 풀 → 서블릿 컨테이너 → Spring 컨트롤러
```

**Python/Gunicorn**:
```
요청 → Gunicorn 마스터 → 워커 프로세스 → WSGI 애플리케이션
```

## 8.2 설정 방식 비교

### Tomcat: server.xml

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

**공통점**: 모두 설정 파일로 서버 동작 제어  
**차이점**: XML vs Python 설정 파일

## 8.3 배포 방식 비교

### Spring/Tomcat: WAR 파일

```bash
# 빌드
mvn clean package

# 배포
cp target/myapp.war $CATALINA_HOME/webapps/
```

### Python/Gunicorn: 패키지/모듈

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
gunicorn myproject.wsgi:application
```

**차이점**: 
- WAR는 컴파일된 바이트코드 포함
- Python은 소스코드 직접 실행

## 8.4 성능 특성 비교

### 동시성 처리

| 항목 | Spring/Tomcat | Python/Gunicorn |
|------|--------------|-----------------|
| **기본 모델** | 스레드 풀 | 프로세스 풀 |
| **동시 요청 수** | 스레드 수에 비례 | 워커 수에 비례 |
| **메모리 사용** | 상대적으로 적음 | 상대적으로 많음 |
| **컨텍스트 스위칭** | 빠름 | 느림 |

### I/O 집약적 작업

- **Tomcat**: 스레드가 블로킹되면 다른 스레드가 처리
- **Gunicorn (sync)**: 워커가 블로킹되면 다른 워커가 처리
- **Gunicorn (gevent)**: 비동기 I/O로 높은 동시성

### CPU 집약적 작업

- **Tomcat**: 멀티스레드로 CPU 코어 활용
- **Gunicorn**: 멀티프로세스로 CPU 코어 활용 (GIL 제약 있음)

## 8.5 선택 가이드

### Spring/Tomcat을 선택하는 경우

- 기존 Java 생태계 활용
- 엔터프라이즈급 기능 필요 (JTA, JMS 등)
- 높은 처리량과 낮은 메모리 사용 중요

### Python/Gunicorn을 선택하는 경우

- Python 생태계 활용 (Django, FastAPI 등)
- 빠른 개발 속도 중요
- 데이터 분석/머신러닝 통합 필요

## 8.6 핵심 정리

### 공통점

1. **웹 서버 역할**: HTTP 요청을 받아 애플리케이션에 전달
2. **동시성 처리**: 여러 요청을 동시에 처리
3. **설정 파일**: 서버 동작을 설정 파일로 제어
4. **프로덕션 배포**: 리버스 프록시(Nginx/Apache)와 함께 사용

### 차이점

1. **실행 모델**: 스레드 vs 프로세스
2. **메모리 관리**: 공유 vs 격리
3. **언어**: Java vs Python
4. **프로토콜**: 서블릿 스펙 vs WSGI/ASGI

### 학습 포인트

Spring/Tomcat 경험자가 Python/Gunicorn을 이해할 때:

1. **역할은 동일**: 둘 다 웹 애플리케이션 서버
2. **구현 방식이 다름**: 스레드 vs 프로세스
3. **프로토콜이 다름**: 서블릿 스펙 vs WSGI/ASGI
4. **설정 방식이 다름**: XML vs Python

이러한 차이점을 이해하면 Python 웹 서버를 효과적으로 사용할 수 있습니다.

## 8.7 마무리

이 교과서를 통해 다음을 학습했습니다:

1. ✅ Gunicorn이 무엇이고 왜 필요한지
2. ✅ WSGI/ASGI 프로토콜의 동작 원리
3. ✅ Gunicorn 설치 및 기본 사용법
4. ✅ 프로세스 모델과 워커의 동작 방식
5. ✅ Django에서 Gunicorn 사용하기
6. ✅ FastAPI에서 Uvicorn 사용하기
7. ✅ 프로덕션 환경 설정 방법
8. ✅ Spring/Tomcat과의 비교를 통한 통합적 이해

이제 Django나 FastAPI 프로젝트를 프로덕션 환경에 배포할 준비가 되었습니다!

---

**이전: [07_config.md](07_config.md) | 처음으로: [00_chapter.md](00_chapter.md)**

