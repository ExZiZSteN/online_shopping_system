
from fastapi import APIRouter, Depends, status

from typing import Annotated, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.models.user import User
from user_service.database import get_db
from user import router as user_router
from router import router as review_router


router = APIRouter()
router.include_router(user_router)
router.include_router(review_router)