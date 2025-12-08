from fastapi import FastAPI, Depends, Request
import time

app = FastAPI()

# 미들웨어: 요청 처리 시간 측정
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 의존성: 데이터베이스 연결 시뮬레이션
def get_db():
    """데이터베이스 연결 의존성"""
    db = {"connected": True}
    print("데이터베이스 연결 생성")
    try:
        yield db
    finally:
        print("데이터베이스 연결 종료")
        db["connected"] = False

# 의존성: 서비스 레이어
def get_item_service(db = Depends(get_db)):
    """아이템 서비스 의존성"""
    return {"db": db, "service": "ItemService"}

@app.get("/")
def read_root():
    return {"message": "FastAPI 아키텍처 데모"}

@app.get("/items/{item_id}")
def read_item(item_id: int, service = Depends(get_item_service)):
    """라우터 매칭, 의존성 주입, 응답 직렬화 데모"""
    return {
        "item_id": item_id,
        "service": service,
        "message": "의존성 주입이 작동합니다"
    }

