import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.database import get_db
from user_service.models.user import User
from user_service.schemas.review import (
    ReviewCreate,
    ReviewOut,
    ReviewReplyCreate,
    ReviewReplyOut
)
from user_service.service.review import ReviewService
from user_service.service.user import get_current_user


router = APIRouter()


def get_review_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ReviewService:
    return ReviewService(db)


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.add_review(user_id=current_user.id, data=data)


@router.get("/reviews/product/{product_id}", response_model=List[ReviewOut])
async def get_product_review(product_id: uuid.UUID, service: Annotated[ReviewService, Depends(get_review_service)]):
    return await service.get_reviews_by_product(product_id)

@router.post("/reviews/reply", response_model=ReviewReplyOut, status_code=status.HTTP_201_CREATED)
async def create_review_reply(
    data: ReviewReplyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.add_reply(author_id=current_user.id, data=data)


@router.get("/reviews/{review_id}/replies", response_model=List[ReviewReplyOut])
async def get_review_replies(
    review_id: uuid.UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.get_replies_by_review(review_id)