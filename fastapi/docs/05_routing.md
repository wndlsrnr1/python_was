# 5장: 라우팅 및 엔드포인트 작성

## 5.1 HTTP 메서드별 엔드포인트

FastAPI는 HTTP 메서드에 따라 다른 데코레이터를 제공합니다.

### GET 요청

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### POST 요청

```python
@app.post("/items/")
def create_item(item: Item):
    return item
```

### PUT 요청

```python
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}
```

### DELETE 요청

```python
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}
```

### Spring @RestController와 비교

**Spring Boot**:
```java
@RestController
public class ItemController {
    @GetMapping("/items/{itemId}")
    public Item getItem(@PathVariable int itemId) {
        return itemService.findById(itemId);
    }
    
    @PostMapping("/items")
    public Item createItem(@RequestBody Item item) {
        return itemService.save(item);
    }
    
    @PutMapping("/items/{itemId}")
    public Item updateItem(@PathVariable int itemId, @RequestBody Item item) {
        return itemService.update(itemId, item);
    }
    
    @DeleteMapping("/items/{itemId}")
    public void deleteItem(@PathVariable int itemId) {
        itemService.delete(itemId);
    }
}
```

**FastAPI**:
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return item_service.find_by_id(item_id)

@app.post("/items/")
def create_item(item: Item):
    return item_service.save(item)

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return item_service.update(item_id, item)

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    item_service.delete(item_id)
    return {"message": "Item deleted"}
```

## 5.2 경로 파라미터

경로에 포함된 변수를 경로 파라미터라고 합니다.

### 기본 사용법

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

`/items/42`로 접속하면 `item_id`는 42가 됩니다.

### 타입 검증

FastAPI는 타입 힌트를 사용하여 자동 검증합니다:

```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

`/items/abc`로 접속하면 자동으로 422 에러가 반환됩니다 (정수 타입이 아니므로).

### Spring @PathVariable과 비교

**Spring Boot**:
```java
@GetMapping("/items/{itemId}")
public Item getItem(@PathVariable int itemId) {
    return itemService.findById(itemId);
}
```

**FastAPI**:
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return item_service.find_by_id(item_id)
```

FastAPI는 타입 힌트만으로 자동 검증합니다.

## 5.3 쿼리 파라미터

URL의 `?` 뒤에 오는 파라미터를 쿼리 파라미터라고 합니다.

### 기본 사용법

```python
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

`/items/?skip=20&limit=5`로 접속하면 `skip=20`, `limit=5`가 전달됩니다.

### 선택적 파라미터

```python
from typing import Optional

@app.get("/items/")
def read_items(q: Optional[str] = None):
    return {"q": q}
```

`q` 파라미터는 선택적입니다. 없으면 `None`이 됩니다.

### Spring @RequestParam과 비교

**Spring Boot**:
```java
@GetMapping("/items")
public List<Item> getItems(
    @RequestParam(defaultValue = "0") int skip,
    @RequestParam(defaultValue = "10") int limit
) {
    return itemService.findAll(skip, limit);
}
```

**FastAPI**:
```python
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return item_service.find_all(skip, limit)
```

FastAPI는 기본값만으로 선택적 파라미터를 표현합니다.

## 5.4 Request Body 처리

POST나 PUT 요청에서 데이터를 전송할 때 Request Body를 사용합니다.

### Pydantic 모델 사용

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    quantity: int = 0

@app.post("/items/")
def create_item(item: Item):
    return item
```

이 코드는 자동으로:
1. JSON 요청 본문을 `Item` 객체로 변환
2. 타입 검증 (name은 str, price는 float 등)
3. 잘못된 타입이면 422 에러 반환

### Spring @RequestBody와 비교

**Spring Boot**:
```java
@PostMapping("/items")
public Item createItem(@RequestBody @Valid ItemDto itemDto) {
    return itemService.save(itemDto.toEntity());
}
```

**FastAPI**:
```python
@app.post("/items/")
def create_item(item: Item):
    return item_service.save(item)
```

FastAPI는 타입 힌트만으로 자동 검증 및 변환을 수행합니다.

## 5.5 Response 모델 정의

응답 형식을 명시적으로 정의할 수 있습니다.

### 기본 사용법

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

`response_model`을 지정하면:
1. 응답 형식이 API 문서에 표시됨
2. 응답 데이터가 자동으로 검증됨

### Spring ResponseEntity와 비교

**Spring Boot**:
```java
@GetMapping("/items/{itemId}")
public ResponseEntity<ItemResponse> getItem(@PathVariable int itemId) {
    ItemResponse item = itemService.findById(itemId);
    return ResponseEntity.ok(item);
}
```

**FastAPI**:
```python
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    return item_service.find_by_id(item_id)
```

FastAPI는 `response_model`만으로 응답 형식을 정의합니다.

## 5.6 상태 코드 지정

응답 상태 코드를 지정할 수 있습니다.

### 기본 사용법

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item
```

### Spring @ResponseStatus와 비교

**Spring Boot**:
```java
@PostMapping("/items")
@ResponseStatus(HttpStatus.CREATED)
public Item createItem(@RequestBody Item item) {
    return itemService.save(item);
}
```

**FastAPI**:
```python
@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return item_service.save(item)
```

## 5.7 실습 예제

`fastapi/codes/03_routing_example/` 디렉토리에 다양한 라우팅 예제가 있습니다.

### 예제 실행

```bash
cd fastapi/codes/03_routing_example
uvicorn main:app --reload
```

이 예제는 다음을 보여줍니다:
- HTTP 메서드별 엔드포인트
- 경로 파라미터
- 쿼리 파라미터
- Request Body 처리
- Response 모델

## 5.8 다음 단계

이제 FastAPI로 API 엔드포인트를 작성하는 방법을 배웠습니다. 다음 단계:

1. **06_uvicorn_gunicorn.md**: 서버 설정 및 이해
2. **07_production.md**: 프로덕션 배포 준비

---

**이전: [04_architecture.md](04_architecture.md) | 다음: [06_uvicorn_gunicorn.md](06_uvicorn_gunicorn.md) →**

