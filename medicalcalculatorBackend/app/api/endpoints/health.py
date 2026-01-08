from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from app.database import get_db
from app.schemas import HealthCheck

router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Проверка здоровья приложения и подключения к базе данных
    """
    # Проверяем подключение к базе данных
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthCheck(
        status="healthy",
        database=db_status,
        timestamp=datetime.utcnow()
    )

@router.get("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    """
    Тестовый эндпоинт для проверки работы с БД
    """
    result = await db.execute(text("SELECT version()"))
    version = result.scalar()
    
    return {
        "database": "PostgreSQL",
        "version": version,
        "status": "connected"
    }