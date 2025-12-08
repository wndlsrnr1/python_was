# 2장: 기본 설치 및 실행

## 2.1 설치

### 가상환경 설정 (권장)

Python 프로젝트에서는 가상환경을 사용하는 것이 좋습니다:

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

가상환경이 활성화되면 터미널 프롬프트에 `(venv)`가 표시됩니다.

### FastAPI 설치

```bash
pip install fastapi
```

### Uvicorn 설치

FastAPI를 실행하려면 ASGI 서버가 필요합니다. Uvicorn을 설치합니다:

```bash
pip install uvicorn
```

또는 표준 라이브러리 포함 설치 (권장):

```bash
pip install "uvicorn[standard]"
```

`[standard]` 옵션은 다음을 포함합니다:
- `httptools`: 빠른 HTTP 파싱
- `uvloop`: 빠른 이벤트 루프 (Linux/Mac)
- `websockets`: WebSocket 지원
- `watchfiles`: 자동 리로드

### 한 번에 설치

```bash
pip install fastapi "uvicorn[standard]"
```

설치 확인:

```bash
python -c "import fastapi; print(fastapi.__version__)"
uvicorn --version
```

## 2.2 최소한의 FastAPI 애플리케이션 만들기

`fastapi/codes/01_basic_setup/main.py` 파일을 생성합니다:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

이것이 가장 간단한 FastAPI 애플리케이션입니다.

### 코드 설명

1. **`from fastapi import FastAPI`**: FastAPI 클래스를 import
2. **`app = FastAPI()`**: FastAPI 애플리케이션 인스턴스 생성
3. **`@app.get("/")`**: GET 메서드로 "/" 경로에 대한 엔드포인트 등록
4. **`def read_root()`**: 엔드포인트 함수 정의

Spring Boot와 비교하면:

```java
@RestController
public class HelloController {
    @GetMapping("/")
    public Map<String, String> readRoot() {
        return Map.of("message", "Hello World");
    }
}
```

FastAPI가 더 간결합니다.

## 2.3 실행

### 기본 실행

터미널에서 다음 명령어를 실행합니다:

```bash
cd fastapi/codes/01_basic_setup
uvicorn main:app
```

여기서:
- `main`: `main.py` 파일 (확장자 제외)
- `app`: `main.py` 파일 내의 `app` 변수 (FastAPI 인스턴스)

출력 예시:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 브라우저에서 확인

브라우저에서 `http://127.0.0.1:8000` 접속하면:

```json
{"message":"Hello World"}
```

JSON 응답이 표시됩니다.

### 자동 API 문서 확인

FastAPI는 자동으로 API 문서를 생성합니다:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

브라우저에서 접속하면 인터랙티브한 API 문서를 확인할 수 있습니다.

Spring Boot에서는 Swagger 설정을 별도로 해야 하지만, FastAPI는 기본 제공입니다.

## 2.4 자동 리로드 (개발 모드)

개발 중에는 코드 변경 시 자동으로 서버를 재시작하는 것이 편리합니다:

```bash
uvicorn main:app --reload
```

코드를 수정하고 저장하면 자동으로 서버가 재시작됩니다.

**주의**: 프로덕션 환경에서는 `--reload` 옵션을 사용하지 마세요.

## 2.5 포트 및 호스트 변경

### 포트 변경

```bash
uvicorn main:app --port 8080
```

기본 포트는 8000입니다. 8080으로 변경하면 `http://127.0.0.1:8080`에서 접속할 수 있습니다.

### 호스트 변경

```bash
uvicorn main:app --host 0.0.0.0
```

모든 네트워크 인터페이스에서 접근 가능합니다. 기본값은 `127.0.0.1` (로컬호스트만)입니다.

### 함께 사용

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

## 2.6 더 복잡한 예제

경로 파라미터와 쿼리 파라미터를 사용하는 예제:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

이 코드를 실행하고:

- `http://127.0.0.1:8000/items/42` 접속 → `{"item_id": 42, "q": null}`
- `http://127.0.0.1:8000/items/42?q=test` 접속 → `{"item_id": 42, "q": "test"}`

Spring Boot와 비교하면:

```java
@GetMapping("/items/{item_id}")
public Map<String, Object> readItem(
    @PathVariable int itemId,
    @RequestParam(required = false) String q
) {
    return Map.of("item_id", itemId, "q", q);
}
```

FastAPI가 더 간결하고 타입 힌트로 자동 검증됩니다.

## 2.7 로그 레벨 설정

```bash
uvicorn main:app --log-level debug
```

로그 레벨: `critical`, `error`, `warning`, `info`, `debug`, `trace`

기본값은 `info`입니다.

## 2.8 실습 예제

`fastapi/codes/01_basic_setup/` 디렉토리에 다음 파일들이 있습니다:

- `main.py`: 기본 FastAPI 애플리케이션
- `README.md`: 실행 방법 안내

각 파일을 실행해보며 동작을 확인해보세요.

### 실행 방법

```bash
# 1. 디렉토리로 이동
cd fastapi/codes/01_basic_setup

# 2. 서버 실행
uvicorn main:app --reload

# 3. 브라우저에서 확인
# - http://127.0.0.1:8000
# - http://127.0.0.1:8000/docs
# - http://127.0.0.1:8000/items/42?q=test
```

## 2.9 종료

터미널에서 `Ctrl+C`를 누르면 uvicorn이 종료됩니다.

## 2.10 다음 단계

이제 FastAPI를 설치하고 실행하는 방법을 배웠습니다. 다음 단계:

1. **03_asgi_protocol.md**: ASGI 프로토콜이 어떻게 동작하는지 학습
2. **04_architecture.md**: FastAPI 내부 구조 이해

---

**이전: [01_overview.md](01_overview.md) | 다음: [03_asgi_protocol.md](03_asgi_protocol.md) →**

