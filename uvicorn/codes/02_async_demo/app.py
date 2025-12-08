import asyncio
import time
from fastapi import FastAPI

app = FastAPI()

@app.get("/sync")
def sync_endpoint():
    """동기 엔드포인트 (시뮬레이션)"""
    time.sleep(1)  # 1초 대기 (블로킹)
    return {"message": "Sync response", "time": time.time()}

@app.get("/async")
async def async_endpoint():
    """비동기 엔드포인트"""
    await asyncio.sleep(1)  # 1초 대기 (논블로킹)
    return {"message": "Async response", "time": time.time()}

@app.get("/delay/{seconds}")
async def delay_endpoint(seconds: int):
    """지정된 시간만큼 대기하는 엔드포인트"""
    await asyncio.sleep(seconds)
    return {"message": f"Waited {seconds} seconds", "time": time.time()}

