from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.api.v1.api import api_router
from app.database import engine, Base
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Medical Calculator Backend...")
    
    # Создание таблиц при запуске
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Could not create database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title="Medical Calculator Backend",
    version="1.0.0",
    description="Backend API для медицинского калькулятора с аутентификацией",
    lifespan=lifespan,
)

# Настройка CORS
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Подключаем маршруты
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Добро пожаловать в Medical Calculator Backend API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/api/auth/register",
            "login": "/api/auth/login",
            "me": "/api/auth/me",
            "health": "/api/health/health",
            "docs": "/docs",
        }
    }