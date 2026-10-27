
from fastapi import APIRouter, Depends, status

from typing import Annotated, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.models.user import User
from user_service.database import get_db
from user_service.api.user_api import router as user_router
from user_service.api.review_api import router as review_router


router = APIRouter()
router.include_router(user_router)
router.include_router(review_router)