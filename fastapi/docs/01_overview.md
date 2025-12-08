# 1장: FastAPI 개요 및 왜 필요한가

## 1.1 FastAPI란?

**FastAPI**는 Python으로 **현대적인 웹 API**를 빠르게 개발하기 위한 웹 프레임워크입니다.

### 이름의 의미

- **Fast**: 빠른 성능 (NodeJS, Go와 비슷한 수준)
- **API**: RESTful API 개발에 최적화
- **Python**: Python 3.6+ 기반, 타입 힌트 활용

### Spring Boot와의 비교

Spring 개발자라면 다음과 같이 이해하면 됩니다:

| Spring Boot | FastAPI |
|------------|---------|
| Java 기반 웹 프레임워크 | Python 기반 웹 프레임워크 |
| @RestController로 API 개발 | 데코레이터로 API 개발 |
| Spring DI (의존성 주입) | FastAPI Dependency Injection |
| Spring Security | FastAPI Security |
| JPA/Hibernate | SQLAlchemy, Tortoise ORM 등 |
| Maven/Gradle 빌드 | pip 설치, Poetry 등 |
| WAR 파일 배포 | Python 모듈 배포 |

**핵심 차이점**: 
- **Spring Boot**: Java 생태계, 엔터프라이즈급 기능 풍부
- **FastAPI**: Python 생태계, 빠른 개발과 높은 성능에 집중

## 1.2 왜 FastAPI인가?

### 기존 Python 웹 프레임워크의 한계

#### Django

```python
# Django - 전통적인 방식
from django.http import JsonResponse

def my_view(request):
    return JsonResponse({"message": "Hello"})
```

**특징**:
- ✅ 풍부한 기능 (ORM, Admin, 인증 등)
- ⚠️ 무거움 (작은 API에는 과함)
- ⚠️ 비동기 지원 제한적 (최근 개선 중)

#### Flask

```python
# Flask - 경량 프레임워크
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify({"message": "Hello"})
```

**특징**:
- ✅ 가볍고 유연함
- ⚠️ 비동기 지원 부족
- ⚠️ 타입 힌트 활용 제한적
- ⚠️ API 문서 자동 생성 없음

### FastAPI의 장점

#### 1. 자동 API 문서 생성

FastAPI는 코드만 작성하면 자동으로 API 문서를 생성합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

이 코드만 작성하면:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

자동으로 생성됩니다. Spring에서는 Swagger 설정을 별도로 해야 하지만, FastAPI는 기본 제공입니다.

#### 2. 타입 힌트 기반 검증

Python 타입 힌트를 활용하여 자동 검증과 직렬화를 제공합니다:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    quantity: int

@app.post("/items/")
def create_item(item: Item):
    return item
```

`item` 파라미터는 자동으로:
- JSON에서 Python 객체로 변환
- 타입 검증 (name은 str, price는 float 등)
- 잘못된 타입이면 자동으로 422 에러 반환

Spring에서는 `@Valid`와 DTO 클래스를 별도로 작성해야 하지만, FastAPI는 타입 힌트만으로 처리합니다.

#### 3. 비동기 지원

FastAPI는 비동기 처리를 기본으로 지원합니다:

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    await asyncio.sleep(1)  # 비동기 I/O 작업
    return {"message": "Hello"}
```

Spring의 `@Async`와 유사하지만, FastAPI는 더 간단한 문법을 제공합니다.

#### 4. 높은 성능

FastAPI는 Starlette와 Pydantic을 기반으로 하여 매우 빠릅니다:

| 프레임워크 | 요청/초 (대략) |
|----------|--------------|
| FastAPI | ~50,000 |
| Flask | ~20,000 |
| Django | ~15,000 |
| Spring Boot | ~30,000 |

**참고**: 실제 성능은 사용 사례에 따라 다릅니다.

## 1.3 FastAPI의 역할

FastAPI는 다음과 같은 역할을 합니다:

1. **HTTP 요청 처리**: 클라이언트로부터 HTTP 요청을 받아 처리
2. **라우팅**: URL 경로와 HTTP 메서드에 따라 적절한 함수 호출
3. **요청 검증**: 타입 힌트 기반 자동 검증
4. **응답 직렬화**: Python 객체를 JSON으로 자동 변환
5. **API 문서 생성**: OpenAPI 스펙 기반 자동 문서 생성

### 아키텍처 개요

```
클라이언트 요청
    ↓
Uvicorn/Gunicorn (ASGI 서버)
    ↓
FastAPI 애플리케이션
    ↓
라우터 → 엔드포인트 함수
    ↓
비즈니스 로직 처리
    ↓
응답 반환 (JSON)
```

이 구조는 Spring Boot의 구조와 유사합니다:

```
클라이언트 요청
    ↓
Tomcat (서블릿 컨테이너)
    ↓
Spring Boot 애플리케이션
    ↓
DispatcherServlet → Controller
    ↓
비즈니스 로직 처리
    ↓
응답 반환 (JSON)
```

## 1.4 언제 FastAPI를 사용할까?

### FastAPI가 적합한 경우

- ✅ **RESTful API 개발**: 마이크로서비스, 백엔드 API
- ✅ **빠른 프로토타이핑**: 빠른 개발이 필요한 경우
- ✅ **비동기 I/O 집약적**: 데이터베이스, 외부 API 호출이 많은 경우
- ✅ **타입 안정성**: Python 타입 힌트를 활용하고 싶은 경우
- ✅ **자동 문서화**: API 문서를 자동으로 생성하고 싶은 경우

### 다른 프레임워크가 적합한 경우

- **Django**: 관리자 페이지, 풀스택 웹 애플리케이션
- **Flask**: 매우 간단한 API, 높은 유연성이 필요한 경우
- **Spring Boot**: Java 생태계, 엔터프라이즈급 기능이 필요한 경우

## 1.5 Spring Boot와의 주요 차이점

### 1. 언어와 생태계

| 특성 | Spring Boot | FastAPI |
|------|------------|---------|
| 언어 | Java | Python |
| 패키지 관리 | Maven/Gradle | pip/Poetry |
| 타입 시스템 | 정적 타입 (컴파일 타임) | 동적 타입 + 타입 힌트 (런타임 검증) |
| 성능 | JVM 기반, 높은 성능 | Python 기반, 빠른 개발 |

### 2. 의존성 주입

**Spring Boot**:
```java
@RestController
public class UserController {
    @Autowired
    private UserService userService;
    
    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();
    }
}
```

**FastAPI**:
```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_user_service():
    return UserService()

@app.get("/users")
def get_users(user_service: UserService = Depends(get_user_service)):
    return user_service.find_all()
```

### 3. 요청/응답 처리

**Spring Boot**:
```java
@PostMapping("/items")
public Item createItem(@RequestBody @Valid ItemDto itemDto) {
    // DTO를 Entity로 변환
    Item item = itemDto.toEntity();
    return itemService.save(item);
}
```

**FastAPI**:
```python
@app.post("/items")
def create_item(item: Item):
    # Pydantic 모델이 자동으로 검증 및 변환
    return item_service.save(item)
```

## 1.6 간단한 "Hello World" 예제

가장 간단한 FastAPI 애플리케이션:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

이 코드를 `main.py`에 저장하고:

```bash
uvicorn main:app --reload
```

실행하면 `http://127.0.0.1:8000`에서 API를 사용할 수 있습니다.

Spring Boot와 비교하면:

```java
@RestController
public class HelloController {
    @GetMapping("/")
    public Map<String, String> hello() {
        return Map.of("message", "Hello World");
    }
}
```

FastAPI가 더 간결합니다.

## 1.7 다음 단계

이제 FastAPI가 무엇인지, 왜 필요한지 이해했습니다. 다음 단계:

1. **02_basic_setup.md**: 실제로 설치하고 실행해보기
2. **03_asgi_protocol.md**: ASGI 프로토콜이 어떻게 동작하는지 학습

---

**이전: [00_chapter.md](00_chapter.md) | 다음: [02_basic_setup.md](02_basic_setup.md) →**

