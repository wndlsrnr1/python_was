# 2장: WSGI/ASGI 프로토콜 이해

## 2.1 WSGI란?

**WSGI**(Web Server Gateway Interface)는 Python 웹 애플리케이션과 웹 서버 간의 **표준 인터페이스**입니다.

### Spring과의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

- **서블릿 스펙**: Java 웹 애플리케이션과 서버 간의 표준 인터페이스
- **WSGI**: Python 웹 애플리케이션과 서버 간의 표준 인터페이스

둘 다 **표준화된 인터페이스**를 통해 애플리케이션과 서버를 분리합니다.

## 2.2 서블릿 컨테이너 vs WSGI 서버

Spring/Tomcat 경험자라면 "서블릿이 컨테이너 기반"이라는 말을 들어봤을 것입니다. 이와 WSGI 서버의 차이를 명확히 이해해봅시다.

### 서블릿이 컨테이너 기반이라는 뜻

**서블릿 컨테이너**(예: Tomcat)는 서블릿의 **생명주기를 관리**하는 환경입니다:

1. **생명주기 관리**: 서블릿의 생성, 초기화, 실행, 종료를 관리
2. **환경 제공**: 서블릿이 실행될 수 있는 환경(컨텍스트, 세션 등) 제공
3. **요청 처리**: HTTP 요청을 받아 서블릿에 전달하고, 서블릿의 응답을 클라이언트에 전송

비유하자면, **컨테이너는 집**이고 **서블릿은 그 집에서 사는 사람**입니다. 사람은 집 안에서만 살 수 있고, 집이 없으면 살 수 없습니다.

```
Tomcat (컨테이너)
    ↓
서블릿이 컨테이너 안에서 실행
    ↓
Spring 애플리케이션
```

### WSGI는 인터페이스, Gunicorn은 서버

중요한 점은 **WSGI는 서버가 아니라 인터페이스(규약)**라는 것입니다:

- **WSGI**: 애플리케이션과 서버 간의 통신 규약 (인터페이스)
- **Gunicorn**: WSGI 규약을 구현한 서버

비유하자면:
- **WSGI**: 전화 통화 규칙 (인터페이스)
- **Gunicorn**: 전화기 (서버)

### 서블릿 컨테이너 vs WSGI 서버의 차이

| 특성 | 서블릿 컨테이너 (Tomcat) | WSGI 서버 (Gunicorn) |
|------|------------------------|---------------------|
| **역할** | 서블릿의 생명주기 관리 + 요청 처리 | WSGI 규약에 따라 요청 처리 |
| **관계** | 서블릿이 컨테이너 **안에서** 실행 | 서버가 애플리케이션을 **호출** |
| **생명주기** | 컨테이너가 서블릿의 생명주기 관리 | 서버가 애플리케이션을 직접 호출 |
| **환경 제공** | 컨테이너가 환경(컨텍스트 등) 제공 | 서버가 환경 정보를 전달 |

**핵심 차이**:
- **서블릿**: 컨테이너가 서블릿을 **관리**하고, 서블릿은 컨테이너 **안에서** 실행
- **WSGI**: 서버가 애플리케이션을 **호출**하고, 애플리케이션은 독립적으로 존재

### 구조 비교

**Spring/Tomcat 구조**:
```
Tomcat (컨테이너)
    ├─→ 서블릿 1 (컨테이너 안에서 실행)
    ├─→ 서블릿 2 (컨테이너 안에서 실행)
    └─→ Spring 애플리케이션
```

**Python/Gunicorn 구조**:
```
Gunicorn (서버)
    ↓
WSGI 인터페이스 호출
    ↓
Django 애플리케이션 (독립적으로 존재)
```

**차이점**: 서블릿은 컨테이너에 **의존**하지만, WSGI 애플리케이션은 서버에 **의존하지 않고** 인터페이스만 따릅니다.

### 서블릿 vs WSGI: 객체 vs 함수

가장 핵심적인 차이는 **서블릿은 객체이고, WSGI는 함수**라는 점입니다.

#### 서블릿 (객체 기반)

서블릿은 **클래스**로 정의되며, 컨테이너가 **객체**를 생성하고 관리합니다:

```java
// 서블릿은 클래스로 정의됨
@WebServlet("/hello")
public class HelloServlet extends HttpServlet {
    // Tomcat이 이 클래스의 인스턴스를 생성하고 관리
    // 서블릿 = 객체
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        resp.getWriter().println("Hello");
    }
}
```

**특징**:
- 서블릿은 **클래스**(객체)로 정의됨
- 컨테이너가 서블릿 **객체**를 생성하고 관리
- 서블릿 객체는 컨테이너의 일부처럼 동작
- 컨테이너 없이는 존재할 수 없음

#### WSGI (함수 기반)

WSGI는 **함수**로 정의되며, 서버가 필요할 때 **호출**합니다:

```python
# WSGI는 함수로 정의됨
def application(environ, start_response):
    # 이 함수는 독립적으로 존재
    # 서버가 필요할 때 호출
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello']
```

**특징**:
- WSGI는 **함수**(또는 callable 객체)로 정의됨
- 서버가 필요할 때 함수를 **호출**
- 함수는 독립적으로 존재하며 서버에 의존하지 않음
- 어떤 WSGI 서버와도 호환 가능

#### 실행 방식의 차이

**서블릿 (컨테이너 기반)**:
```
1. Tomcat 시작
2. Tomcat이 서블릿 클래스를 로드하고 객체 생성
3. 서블릿 객체는 Tomcat의 일부처럼 동작
4. 요청이 오면 → Tomcat이 자신이 관리하는 서블릿 객체의 메서드 호출
5. 서블릿은 Tomcat의 환경(컨텍스트, 세션 등)을 직접 사용
```

**WSGI (서버 호출 방식)**:
```
1. Gunicorn 시작
2. Django 애플리케이션 함수는 이미 독립적으로 존재 (Gunicorn과 무관)
3. 요청이 오면 → Gunicorn이 Django 애플리케이션 함수를 호출
4. 애플리케이션은 서버로부터 환경 정보(environ)를 받아서 사용
```

#### 왜 이 차이가 중요한가?

**서블릿의 경우**:
- 서블릿은 컨테이너의 일부이므로 컨테이너의 기능을 직접 사용
- 컨텍스트, 세션 등을 컨테이너가 제공
- 컨테이너 없이는 실행 불가
- 특정 컨테이너(Tomcat, Jetty 등)에 종속적

**WSGI의 경우**:
- 애플리케이션은 독립적이므로 어떤 WSGI 서버와도 호환 가능
- Gunicorn, uWSGI, Waitress 등 어떤 서버든 사용 가능
- 서버는 단순히 함수를 호출하는 역할
- 서버에 독립적이며 인터페이스만 따름

## 2.3 WSGI Callable 규약

WSGI 애플리케이션은 다음 규약을 따라야 합니다:

1. **Callable 객체**: 함수 또는 `__call__` 메서드를 가진 클래스 인스턴스
2. **인자**: `environ` (환경 변수 딕셔너리), `start_response` (응답 시작 함수)
3. **반환값**: 응답 바이트의 이터러블 (리스트, 제너레이터 등)

### 최소한의 WSGI 애플리케이션 예제

```python
def simple_app(environ, start_response):
    """가장 간단한 WSGI 애플리케이션"""
    status = '200 OK'
    headers = [('Content-Type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    return [b'Hello, WSGI!\n']
```

이 애플리케이션을 gunicorn으로 실행하면:

```bash
gunicorn simple_app:simple_app
```

### Django의 WSGI 애플리케이션

Django 프로젝트를 생성하면 `myproject/wsgi.py` 파일이 자동 생성됩니다:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_wsgi_application()
```

이 `application` 객체가 WSGI callable입니다. Gunicorn은 이 객체를 호출하여 요청을 처리합니다.

## 2.4 ASGI란?

**ASGI**(Asynchronous Server Gateway Interface)는 WSGI의 비동기 버전입니다.

### WSGI vs ASGI

| 특성 | WSGI | ASGI |
|------|------|------|
| 동기/비동기 | 동기만 지원 | 비동기 지원 |
| WebSocket | 지원 안 함 | 지원 |
| HTTP/2 | 제한적 | 완전 지원 |
| 사용 프레임워크 | Django (기본), Flask | FastAPI, Django (Channels) |

### FastAPI와 ASGI

FastAPI는 ASGI를 사용합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

이 `app` 객체는 ASGI 애플리케이션입니다. ASGI 서버(예: uvicorn)가 이를 실행합니다.

## 2.5 Gunicorn과 WSGI/ASGI

- **Gunicorn**: 주로 **WSGI 서버**로 사용 (Django 등)
- **Uvicorn**: **ASGI 서버** (FastAPI 등)
- **Gunicorn + Uvicorn 워커**: Gunicorn이 uvicorn 워커를 사용하여 ASGI 애플리케이션 실행 가능

이 조합은 나중에 6장에서 자세히 다룹니다.

## 2.6 서블릿 스펙과의 비교

### 서블릿 스펙 (Spring)

```java
@WebServlet("/hello")
public class HelloServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {
        resp.getWriter().println("Hello");
    }
}
```

### WSGI (Python)

```python
def hello_app(environ, start_response):
    if environ['REQUEST_METHOD'] == 'GET':
        status = '200 OK'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'Hello']
```

**차이점**:
- **서블릿**: 객체 지향, 서블릿 컨테이너가 생명주기 관리
- **WSGI**: 함수 기반, 서버가 직접 호출

## 2.7 다음 단계

이제 WSGI/ASGI 프로토콜이 어떻게 동작하는지 이해했습니다. 다음 단계:

1. **03_basic_setup.md**: 실제로 설치하고 실행해보기
2. **04_worker_model.md**: 프로세스 모델과 워커 이해

---

**이전: [01_overview.md](01_overview.md) | 다음: [03_basic_setup.md](03_basic_setup.md) →**

