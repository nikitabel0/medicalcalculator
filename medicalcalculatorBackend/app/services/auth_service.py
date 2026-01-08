from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.schemas import UserCreate
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки безопасности
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    default="pbkdf2_sha256",
    pbkdf2_sha256__default_rounds=30000
)


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хэширование пароля"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        # Ищем пользователя по email или username
        stmt = select(User).where((User.email == username) | (User.username == username))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        
        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Создание нового пользователя"""
        # Проверяем, существует ли пользователь с таким email
        existing_user = await AuthService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")
        
        # Проверяем, существует ли пользователь с таким username
        existing_user = await AuthService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise ValueError("Пользователь с таким username уже существует")
        
        # Хэшируем пароль
        hashed_password = AuthService.get_password_hash(user_data.password)
        
        # Создаем пользователя (по умолчанию обычный пользователь, не суперпользователь)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False  # По умолчанию обычный пользователь
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Декодирование JWT токена"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return {}