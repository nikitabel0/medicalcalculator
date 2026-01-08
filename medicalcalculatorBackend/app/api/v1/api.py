from fastapi import APIRouter
from app.api.endpoints import auth, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])

@api_router.get("/")
async def root():
    return {
        "message": "Medical Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "register": "/api/auth/register",
            "login": "/api/auth/login",
            "me": "/api/auth/me",
            "health": "/api/health/health"
        }
    }