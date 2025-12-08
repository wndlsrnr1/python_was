# 4장: FastAPI 아키텍처 및 동작 원리

## 4.1 FastAPI 요청 처리 흐름

FastAPI가 HTTP 요청을 처리하는 전체 흐름을 이해해봅시다.

### 전체 흐름도

```
클라이언트 요청
    ↓
Uvicorn (ASGI 서버)
    ↓
FastAPI 애플리케이션 (ASGI callable)
    ↓
미들웨어 처리
    ↓
라우터 매칭
    ↓
의존성 주입 (Dependency Injection)
    ↓
엔드포인트 함수 실행
    ↓
응답 직렬화 (JSON)
    ↓
응답 반환
```

### Spring MVC와의 비교

```
Spring MVC:
요청 → DispatcherServlet → HandlerMapping → Interceptor → Controller → 응답

FastAPI:
요청 → Uvicorn → FastAPI → 미들웨어 → 라우터 → 의존성 주입 → 엔드포인트 함수 → 응답
```

## 4.2 라우터 동작 원리

### 라우터 등록

FastAPI는 데코레이터를 사용하여 라우트를 등록합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

이 코드는 내부적으로 다음과 같이 동작합니다:

1. `@app.get("/items/{item_id}")` 데코레이터가 실행됨
2. 경로 패턴과 HTTP 메서드가 라우터에 등록됨
3. 함수가 해당 라우트의 핸들러로 저장됨

### 라우터 매칭

요청이 오면 FastAPI는 다음 순서로 라우트를 찾습니다:

1. **HTTP 메서드 확인**: GET, POST, PUT, DELETE 등
2. **경로 패턴 매칭**: `/items/{item_id}` 패턴과 실제 경로 비교
3. **경로 파라미터 추출**: `{item_id}` 부분을 추출하여 함수 인자로 전달

### Spring @RequestMapping과 비교

**Spring Boot**:
```java
@RestController
public class ItemController {
    @GetMapping("/items/{itemId}")
    public Item getItem(@PathVariable int itemId) {
        return itemService.findById(itemId);
    }
}
```

**FastAPI**:
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return item_service.find_by_id(item_id)
```

**차이점**:
- Spring: 어노테이션 기반, 컴파일 타임 검증
- FastAPI: 데코레이터 기반, 런타임 검증 (타입 힌트 활용)

## 4.3 의존성 주입 시스템

FastAPI는 강력한 의존성 주입 시스템을 제공합니다.

### 기본 사용법

```python
from fastapi import Depends, FastAPI

app = FastAPI()

def get_db():
    # 데이터베이스 연결 반환
    db = create_db_connection()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
def read_items(db = Depends(get_db)):
    return db.query("SELECT * FROM items")
```

### 의존성 체인

의존성은 체인으로 연결할 수 있습니다:

```python
def get_db():
    return create_db_connection()

def get_user_service(db = Depends(get_db)):
    return UserService(db)

@app.get("/users/")
def read_users(service = Depends(get_user_service)):
    return service.find_all()
```

### Spring DI와 비교

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
@app.get("/users/")
def read_users(service: UserService = Depends(get_user_service)):
    return service.find_all()
```

**차이점**:
- Spring: 필드 주입, 생성자 주입 등 다양한 방식
- FastAPI: 함수 파라미터 주입, 더 명시적

## 4.4 미들웨어 동작

FastAPI는 미들웨어를 통해 요청/응답을 가로챌 수 있습니다.

### 미들웨어 예제

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

이 미들웨어는 모든 요청의 처리 시간을 응답 헤더에 추가합니다.

### Spring Interceptor와 비교

**Spring Boot**:
```java
@Component
public class ProcessTimeInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, 
                           HttpServletResponse response, 
                           Object handler) {
        request.setAttribute("startTime", System.currentTimeMillis());
        return true;
    }
    
    @Override
    public void postHandle(HttpServletRequest request, 
                          HttpServletResponse response, 
                          Object handler, 
                          ModelAndView modelAndView) {
        long startTime = (Long) request.getAttribute("startTime");
        long processTime = System.currentTimeMillis() - startTime;
        response.setHeader("X-Process-Time", String.valueOf(processTime));
    }
}
```

**FastAPI**:
```python
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

FastAPI가 더 간결합니다.

## 4.5 요청 검증 및 직렬화

FastAPI는 Pydantic을 사용하여 자동 검증과 직렬화를 수행합니다.

### 타입 힌트 기반 검증

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

이 코드는 자동으로:
1. JSON 요청 본문을 `Item` 객체로 변환
2. 타입 검증 (name은 str, price는 float 등)
3. 잘못된 타입이면 422 에러 반환

### Spring @Valid와 비교

**Spring Boot**:
```java
@RestController
public class ItemController {
    @PostMapping("/items")
    public Item createItem(@RequestBody @Valid ItemDto itemDto) {
        // DTO를 Entity로 변환
        return itemService.save(itemDto.toEntity());
    }
}
```

**FastAPI**:
```python
@app.post("/items/")
def create_item(item: Item):
    # 자동으로 검증 및 변환
    return item_service.save(item)
```

FastAPI가 더 간단합니다.

## 4.6 응답 직렬화

FastAPI는 Python 객체를 자동으로 JSON으로 변환합니다:

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {
        "item_id": item_id,
        "name": "Example",
        "price": 9.99
    }
```

이 함수는 자동으로 JSON 응답을 생성합니다:

```json
{
    "item_id": 42,
    "name": "Example",
    "price": 9.99
}
```

### Response 모델 정의

응답 형식을 명시적으로 정의할 수 있습니다:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ItemResponse(BaseModel):
    item_id: int
    name: str
    price: float

@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    return ItemResponse(
        item_id=item_id,
        name="Example",
        price=9.99
    )
```

## 4.7 실습 예제

`fastapi/codes/02_architecture_demo/` 디렉토리에 아키텍처 시각화 예제가 있습니다.

### 예제 실행

```bash
cd fastapi/codes/02_architecture_demo
uvicorn main:app --reload
```

이 예제는 다음을 보여줍니다:
- 라우터 매칭
- 의존성 주입
- 미들웨어 동작
- 요청 검증

## 4.8 다음 단계

이제 FastAPI의 내부 구조와 동작 원리를 이해했습니다. 다음 단계:

1. **05_routing.md**: 실제 API 엔드포인트 작성 방법 학습
2. **06_uvicorn_gunicorn.md**: 서버 설정 및 이해

---

**이전: [03_asgi_protocol.md](03_asgi_protocol.md) | 다음: [05_routing.md](05_routing.md) →**

