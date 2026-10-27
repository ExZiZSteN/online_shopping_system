import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, File as FastAPIFile, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.database import get_db
from user_service.models.user import User
from user_service.schemas.review import (
    ReviewCreate,
    ReviewOut,
    ReviewReplyCreate,
    ReviewReplyOut
)
from user_service.schemas.file import FileOut
from user_service.service.review import ReviewService
from user_service.service.file import FileFacade
from user_service.service.user import get_current_user


router = APIRouter(prefix="/reviews")

def get_file_facade(db: Annotated[AsyncSession, Depends(get_db)]) -> FileFacade:
    return FileFacade(db)

def get_review_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ReviewService:
    return ReviewService(db)


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.add_review(user_id=current_user.id, data=data)


@router.get("/product/{product_id}", response_model=List[ReviewOut])
async def get_product_review(product_id: uuid.UUID, service: Annotated[ReviewService, Depends(get_review_service)]):
    return await service.get_reviews_by_product(product_id)

@router.post("/reply", response_model=ReviewReplyOut, status_code=status.HTTP_201_CREATED)
async def create_review_reply(
    data: ReviewReplyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.add_reply(author_id=current_user.id, data=data)


@router.get("/{review_id}/replies", response_model=List[ReviewReplyOut])
async def get_review_replies(
    review_id: uuid.UUID,
    service: Annotated[ReviewService, Depends(get_review_service)],
):
    return await service.get_replies_by_review(review_id)


@router.post(
    "/{review_id}/media",
    response_model=FileOut,
    status_code=status.HTTP_201_CREATED,
    summary="Прикрепить фото или видео к отзыву (максимум 5)",
)
async def attach_media_to_review(
    review_id: uuid.UUID,
    file: Annotated[UploadFile, FastAPIFile(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    file_facade: Annotated[FileFacade, Depends(get_file_facade)],
):
    return await file_facade.upload_review_media(
        owner_id=current_user.id,
        review_id=review_id,
        upload_file=file,
    )


@router.get(
    "/{review_id}/media",
    response_model=List[FileOut],
    summary="Получить список фото/видео отзыва"
)
async def get_review_media(
    review_id: uuid.UUID,
    file_facade: Annotated[FileFacade, Depends(get_file_facade)],
):
    return await file_facade.get_review_attachments(review_id)