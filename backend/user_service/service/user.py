import uuid
from jose import JWTError
from typing import Annotated
from fastapi import status, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_service.database import get_db
from user_service.models.user import User
from backend.security.token import token_manager

security = HTTPBearer(auto_error=False)

class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


    async def get_user_by_email(self, user_email: str) -> Optional[User]:
        stmt = select(User).where(User.email == user_email)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


async def get_current_user(
        credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
        db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительные учетные данные",
        headers={"WWW-Authenticate": "Bearer"}
    )
    if not token:
        raise credentials_exception
         
    try:
        payload = token_manager.decode_token(token, expected_type='access')
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user