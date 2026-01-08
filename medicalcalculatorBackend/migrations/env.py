import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import sys
import os

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.models import User

config = context.config

# ВАЖНО: Исправляем URL для Alembic - используем синхронный движок для миграций
# Заменяем asyncpg на psycopg2 в URL
sqlalchemy_url = config.get_main_option("sqlalchemy.url")
if sqlalchemy_url and "asyncpg" in sqlalchemy_url:
    # Заменяем asyncpg на пустую строку для синхронного драйвера
    sqlalchemy_url = sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context."""
    
    # Получаем исправленный URL
    connectable_config = config.get_section(config.config_ini_section, {})
    
    # Используем синхронный драйвер для миграций
    from sqlalchemy import create_engine
    from sqlalchemy.engine.url import make_url
    
    url = make_url(connectable_config.get("sqlalchemy.url", ""))
    
    # Если URL содержит asyncpg, заменяем его
    if url.drivername == "postgresql+asyncpg":
        url = url.set(drivername="postgresql")
    
    connectable = create_engine(url, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()