
from fastapi import APIRouter, Depends, status

from typing import Annotated, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession


from user_service.models.user import User
from user_service.database import get_db

from user_service.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from user_service.service.auth import AuthService
from user_service.service.user import UserService, get_current_user

router = APIRouter()

def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(db)


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)]
    ) -> User:
    return await service.register(body)


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)]
    ) -> TokenResponse:
    return await service.login(data=body)

@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(body: RefreshTokenRequest, service: Annotated[AuthService, Depends(get_auth_service)]):
    return await service.refresh_tokens(body.refresh_token)

@router.get("/me", response_model=UserOut)
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/verify")
async def verify_token_for_gateway(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Эндпоинт верификации токена.
    Используется API Gateway (auth_request) или межсервисными HTTP-клиентами
    для проверки валидности токена и извлечения X-User-Id.
    """
    return {
        "status": "valid",
        "user_id": str(current_user.id),
        "user_name": current_user.name,
    }