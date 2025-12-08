from fastapi import FastAPI
from typing import Optional

app = FastAPI(
    title="My FastAPI App", description="FastAPI + Uvicorn 예제", version="1.0.0"
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI with Uvicorn!"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


@app.post("/items/")
def create_item(item: dict):
    return {"item": item, "status": "created"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
