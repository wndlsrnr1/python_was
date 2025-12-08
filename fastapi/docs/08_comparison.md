# 8장: Spring과의 종합 비교 정리

## 8.1 아키텍처 비교

### 전체 구조

**Spring Boot**:
```
클라이언트 요청
    ↓
Tomcat (서블릿 컨테이너)
    ↓
DispatcherServlet
    ↓
HandlerMapping → Controller
    ↓
비즈니스 로직
    ↓
응답 반환
```

**FastAPI**:
```
클라이언트 요청
    ↓
Uvicorn/Gunicorn (ASGI 서버)
    ↓
FastAPI 애플리케이션
    ↓
라우터 → 엔드포인트 함수
    ↓
비즈니스 로직
    ↓
응답 반환
```

### 비교표

| 특성 | Spring Boot | FastAPI |
|------|------------|---------|
| **언어** | Java | Python |
| **서버** | Tomcat, Jetty 등 | Uvicorn, Gunicorn |
| **프로토콜** | 서블릿 스펙 | ASGI |
| **동시성 모델** | 스레드 풀 | 이벤트 루프 + 프로세스 |
| **I/O 처리** | 블로킹 I/O | 비동기 I/O |
| **타입 시스템** | 정적 타입 (컴파일 타임) | 동적 타입 + 타입 힌트 (런타임 검증) |

## 8.2 주요 개념 매핑

### 웹 프레임워크

| Spring Boot | FastAPI |
|------------|---------|
| `@RestController` | `@app.get()`, `@app.post()` 등 |
| `@RequestMapping` | 데코레이터 (`@app.get()`) |
| `@PathVariable` | 경로 파라미터 (`item_id: int`) |
| `@RequestParam` | 쿼리 파라미터 (`q: str = None`) |
| `@RequestBody` | Pydantic 모델 (`item: Item`) |
| `@ResponseBody` | 함수 반환값 (자동 JSON 변환) |

### 의존성 주입

| Spring Boot | FastAPI |
|------------|---------|
| `@Autowired` | `Depends()` |
| `@Component` | 함수 또는 클래스 |
| `@Service` | 함수 또는 클래스 |
| `@Repository` | 함수 또는 클래스 |

### 미들웨어/인터셉터

| Spring Boot | FastAPI |
|------------|---------|
| `HandlerInterceptor` | `@app.middleware("http")` |
| `preHandle()` | 미들웨어 함수 시작 |
| `postHandle()` | 미들웨어 함수 종료 |

### 요청/응답 처리

| Spring Boot | FastAPI |
|------------|---------|
| `@Valid` + DTO | Pydantic 모델 (타입 힌트) |
| `ResponseEntity<T>` | `response_model` 파라미터 |
| `@ResponseStatus` | `status_code` 파라미터 |

## 8.3 코드 비교 예제

### 기본 REST API

**Spring Boot**:
```java
@RestController
@RequestMapping("/api/items")
public class ItemController {
    @Autowired
    private ItemService itemService;
    
    @GetMapping("/{id}")
    public ResponseEntity<Item> getItem(@PathVariable int id) {
        Item item = itemService.findById(id);
        return ResponseEntity.ok(item);
    }
    
    @PostMapping
    public ResponseEntity<Item> createItem(@RequestBody @Valid ItemDto itemDto) {
        Item item = itemService.save(itemDto.toEntity());
        return ResponseEntity.status(HttpStatus.CREATED).body(item);
    }
}
```

**FastAPI**:
```python
from fastapi import FastAPI, Depends, status
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
    price: float

def get_item_service():
    return ItemService()

@app.get("/api/items/{id}")
def get_item(id: int, service: ItemService = Depends(get_item_service)):
    return service.find_by_id(id)

@app.post("/api/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item, service: ItemService = Depends(get_item_service)):
    return service.save(item)
```

### 의존성 주입

**Spring Boot**:
```java
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
    
    public User findById(int id) {
        return userRepository.findById(id);
    }
}
```

**FastAPI**:
```python
def get_user_repository():
    return UserRepository()

def get_user_service(repo: UserRepository = Depends(get_user_repository)):
    return UserService(repo)

@app.get("/users/{id}")
def get_user(id: int, service: UserService = Depends(get_user_service)):
    return service.find_by_id(id)
```

### 미들웨어/인터셉터

**Spring Boot**:
```java
@Component
public class LoggingInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, 
                           HttpServletResponse response, 
                           Object handler) {
        logger.info("Request: {} {}", request.getMethod(), request.getRequestURI());
        return true;
    }
}
```

**FastAPI**:
```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response
```

## 8.4 배포 방식 비교

### 빌드 및 배포

**Spring Boot**:
```bash
# 빌드
mvn package

# 실행
java -jar target/myapp.jar
```

**FastAPI**:
```bash
# 설치 (의존성)
pip install -r requirements.txt

# 실행
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 패키징

| Spring Boot | FastAPI |
|------------|---------|
| JAR/WAR 파일 | Python 모듈 |
| Maven/Gradle | pip/Poetry |
| 단일 실행 파일 가능 | 가상환경 필요 |

### 서비스 등록

**Spring Boot** (systemd):
```ini
[Service]
ExecStart=/usr/bin/java -jar /var/www/app.jar
```

**FastAPI** (systemd):
```ini
[Service]
ExecStart=/var/www/venv/bin/gunicorn main:app -c gunicorn.conf.py
```

## 8.5 성능 비교

### 처리 방식

| 특성 | Spring Boot | FastAPI |
|------|------------|---------|
| **동기 처리** | 스레드 풀 | 프로세스 기반 |
| **비동기 처리** | CompletableFuture | async/await (네이티브) |
| **동시 연결** | 스레드 수에 제한 | 이벤트 루프 (높은 동시성) |
| **메모리 사용** | 스레드당 스택 메모리 | 프로세스당 메모리 |

### 실제 성능

**참고**: 실제 성능은 사용 사례에 따라 다릅니다.

- **CPU 집약적**: Spring Boot가 유리할 수 있음 (JVM 최적화)
- **I/O 집약적**: FastAPI가 유리할 수 있음 (비동기 처리)
- **동시 연결 수**: FastAPI가 유리할 수 있음 (이벤트 루프)

## 8.6 언제 무엇을 사용할까?

### Spring Boot를 선택하는 경우

- ✅ Java 생태계 사용
- ✅ 엔터프라이즈급 기능 필요 (보안, 트랜잭션 등)
- ✅ 기존 Java 인프라 활용
- ✅ 대규모 팀 협업 (타입 안정성)

### FastAPI를 선택하는 경우

- ✅ Python 생태계 사용
- ✅ 빠른 프로토타이핑
- ✅ 비동기 I/O 집약적 작업
- ✅ 자동 API 문서 생성 중요
- ✅ 타입 힌트 활용하고 싶음

## 8.7 학습 경로 비교

### Spring Boot 학습 경로

1. Java 기초
2. Spring Framework 이해
3. Spring Boot 시작
4. REST API 개발
5. 데이터베이스 연동 (JPA)
6. 보안 (Spring Security)
7. 배포

### FastAPI 학습 경로

1. Python 기초
2. FastAPI 시작
3. REST API 개발
4. 데이터베이스 연동 (SQLAlchemy 등)
5. 보안 (OAuth2, JWT)
6. 배포

**공통점**: 둘 다 REST API 개발에 집중하고, 프레임워크 특화 기능을 학습합니다.

## 8.8 마무리

이 교과서를 통해 다음을 배웠습니다:

1. **FastAPI 기본**: 설치, 실행, 기본 사용법
2. **ASGI 프로토콜**: FastAPI와 서버 간 통신 방식
3. **아키텍처**: FastAPI 내부 구조와 동작 원리
4. **라우팅**: API 엔드포인트 작성 방법
5. **서버 이해**: uvicorn과 gunicorn의 역할
6. **프로덕션 배포**: 실제 운영 환경 배포 방법
7. **Spring 비교**: 기존 지식과의 연결

이제 FastAPI를 사용하여 웹 API를 개발할 수 있습니다!

---

**이전: [07_production.md](07_production.md) | 처음으로: [00_chapter.md](00_chapter.md)**

