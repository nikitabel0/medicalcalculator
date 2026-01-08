from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas import TokenData

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Получение текущего пользователя из токена"""
    token = credentials.credentials
    payload = AuthService.decode_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен",
        )
    
    token_data = TokenData(username=username)
    user = await AuthService.get_user_by_username(db, username=token_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен",
        )
    
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    """Получение текущего активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    return current_user


async def get_current_superuser(current_user = Depends(get_current_user)):
    """Проверка, что пользователь - суперпользователь (админ)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return current_user