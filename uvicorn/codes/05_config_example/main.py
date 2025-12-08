from fastapi import FastAPI

app = FastAPI(title="Config Example", version="1.0.0")


@app.get("/")
def read_root():
    return {"message": "Gunicorn + Uvicorn 설정 예제"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
