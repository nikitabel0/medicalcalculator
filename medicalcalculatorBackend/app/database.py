from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")
sync_engine = create_engine(SYNC_DATABASE_URL)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """Зависимость для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()