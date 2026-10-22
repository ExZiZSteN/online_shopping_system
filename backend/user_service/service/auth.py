import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_service.models.user import User
from user_service.service.user import UserService
from user_service.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from security.password import PasswordHasher
from security.token import token_manager

class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_hasher = PasswordHasher()
        self.user_service = UserService()


    async def register(self, data: RegisterRequest):
        '''Регистрация пользователя в системе'''

        existing = self.user_service.get_user_by_email(user_email=data.email)

        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = self.password_hasher.hash(data.password)
        user = User(
            name=data.name,
            email=data.email,
            password_hash=hashed_password,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user


    async def login(self, data: LoginRequest):
        '''Аутентификация пользователя и выпуск Access и Refresh токенов'''

        user = await self.user_service.get_user_by_email(data.email)
        
        if not user or not self.password_hasher.verify(plain_password=data.password, hashed_password=user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный адрес электронной почты или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = token_manager.create_access_token(
            user_id=user.id,
            name=user.name,
            )

        refresh_token = token_manager.create_refresh_token(
            user_id=user.id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )


    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:

        user_id: uuid.UUID = await token_manager.verify_refresh_token(refresh_token)
        user = await self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        access_token = token_manager.create_access_token(user_id=user_id, name=user.name)

        new_refresh_token = token_manager.create_refresh_token(user_id=user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )