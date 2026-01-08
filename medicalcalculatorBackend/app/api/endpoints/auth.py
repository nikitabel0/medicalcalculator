from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user, get_current_superuser

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    - **email**: Email пользователя
    - **username**: Имя пользователя
    - **full_name**: Полное имя (опционально)
    - **password**: Пароль (минимум 6 символов)
    """
    try:
        user = await AuthService.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Вход пользователя
    
    - **username**: Email или имя пользователя
    - **password**: Пароль
    """
    user = await AuthService.authenticate_user(
        db, form_data.username, form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.get("/admin-only")
async def admin_only(current_user = Depends(get_current_superuser)):
    """Эндпоинт только для администраторов"""
    return {
        "message": f"Добро пожаловать, администратор {current_user.username}!",
        "user": current_user.username,
        "is_admin": True
    }