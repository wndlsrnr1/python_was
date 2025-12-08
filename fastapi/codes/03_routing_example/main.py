from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Pydantic 모델 정의
class Item(BaseModel):
    name: str
    price: float
    quantity: int = 0

class ItemResponse(BaseModel):
    item_id: int
    name: str
    price: float
    quantity: int

# GET: 경로 파라미터
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": "Example", "price": 9.99}

# GET: 쿼리 파라미터
@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10, q: Optional[str] = None):
    return {"skip": skip, "limit": limit, "q": q}

# POST: Request Body
@app.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    return {"item_id": 1, **item.dict()}

# PUT: 경로 파라미터 + Request Body
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}

# DELETE: 경로 파라미터
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    return {"message": f"Item {item_id} deleted"}

# Response 모델 사용
@app.get("/items/{item_id}/detail", response_model=ItemResponse)
def get_item_detail(item_id: int):
    return ItemResponse(
        item_id=item_id,
        name="Example",
        price=9.99,
        quantity=10
    )

