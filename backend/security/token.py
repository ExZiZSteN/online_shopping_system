import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


security_bearer = HTTPBearer(auto_error=False)

class TokenManager:
    """Класс для работы с Refresh Token"""
    def __init__(self):
        self._JWT_SECRET : str = os.getenv("JWT_SECRET")
        self._ALGORITHM : str = os.getenv("JWT_ALGORITHM")
        self._ACCESS_TOKEN_EXPIRE_MINUTES : int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        self._REFRESH_TOKEN_EXPIRE_DAYS : int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


    def create_token(
        self,
        subject: uuid.UUID | str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: Optional[Dict[str, Any]] = None
        ) -> str:
        '''Генерация JWT токена'''

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload: Dict[str, Any] = {
            "sub" : str(subject),
            "type" : token_type,
            "iat" : now,
            "exp" : expire,
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self._JWT_SECRET, algorithm=self._ALGORITHM)
        

    def create_access_token(
            self,
            user_id: uuid.UUID | str, 
            name: Optional[str] = None, 
            expires_delta: Optional[timedelta] = None
        ) -> str:
        '''Создание Access-токена'''
        delta = expires_delta or timedelta(minutes=self._ACCESS_TOKEN_EXPIRE_MINUTES)
        extra = {"name" : name} if name else None
        return self.create_token(
            subject=user_id,
            token_type="access",
            expires_delta=delta,
            extra_claims=extra
            )

    def create_refresh_token(
            self,
            user_id: uuid.UUID | str,
            expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Создание Refresh-токена"""
        delta = expires_delta or timedelta(days=self._REFRESH_TOKEN_EXPIRE_DAYS)
        return self.create_token(subject=user_id, token_type="refresh", expires_delta=delta)

    def decode_token(
        self,
        token: str,
        expected_type: Optional[str] = None
        ) -> Dict[str, Any]:
        '''
        Декодирует и верифицирует токен
        '''
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействителен или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self._JWT_SECRET, algorithms=[self._ALGORITHM])
            user_id: Optional[str] = payload.get("sub")
            token_type: Optional[str] = payload.get("type")

            if user_id is None:
                raise credentials_exception

            if expected_type and token_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Недопустимый тип токена. Ожидался {expected_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload
        except JWTError:
            raise credentials_exception


    def verify_refresh_token(self, refresh_token: str) -> uuid.UUID:
        '''
        Проверяет refresh-token на валидность и возвращает UUID пользователя
        '''
        payload = self.decode_token(refresh_token, expected_type="refresh")
        try:
            return uuid.UUID(payload["sub"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Некорректный идентификатор пользователя в токене",
            )


token_manager = TokenManager()

async def get_current_user_id(
        credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security_bearer)],
) -> uuid.UUID:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутсвует заголовок авторизации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = token_manager.decode_token(credentials.credentials, expected_type="access")
    try:
        return uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный идентификатор пользоваетля в токене",
            headers={"WWW-Authenticate": "Bearer"},
        ) 