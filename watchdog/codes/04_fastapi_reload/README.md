# FastAPI 자동 리로드 예제

## 실행 방법

### 1. FastAPI 애플리케이션 생성

```bash
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

### 2. 개발 서버 실행 (자동 리로드)

```bash
uvicorn main:app --reload
```

### 3. 파일 변경 테스트

다른 터미널에서 파일을 수정해보세요:

```bash
# main.py 수정
echo '    return {"message": "Updated!"}' >> main.py
```

서버가 자동으로 재시작되는 것을 확인할 수 있습니다.

## 자동 리로드 확인

서버 로그에서 다음과 같은 메시지를 볼 수 있습니다:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
```

파일을 변경하면:

```
INFO:     Detected file change in 'main.py'. Reloading...
INFO:     Started server process [12346]
```

## 주의사항

- 프로덕션 환경에서는 `--reload` 옵션을 사용하지 마세요
- 자동 리로드는 개발 환경에서만 사용하세요

