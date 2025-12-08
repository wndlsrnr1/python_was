import os
import logging
from fastapi import FastAPI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

# 환경 변수에서 설정 읽기
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "FastAPI Production Example"}

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "database_url": DATABASE_URL if DEBUG else "***",
        "debug": DEBUG
    }

