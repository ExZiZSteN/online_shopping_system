import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.models.reviews import Review
from user_service.models.review_replies import ReviewReply
from user_service.schemas.review import ReviewCreate, ReviewReplyCreate


class FeedbackEntityFactory(ABC):

    @abstractmethod
    def create_review(self, user_id: uuid.UUID, data: ReviewCreate) -> Review:
        pass

    @abstractmethod
    def create_reply(self, author_id: uuid.UUID, data: ReviewReplyCreate) -> ReviewReply:
        pass


class StandardFeedbackFactory(FeedbackEntityFactory):

    def create_review(self, user_id: uuid.UUID, data: ReviewCreate) -> Review:
        if not (1 <= data.rating <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Рейтинг должен находиться в диапозоне от 1 до 5",
            )

        cleaned_comment = data.comment.strip() if data.comment else None

        return Review(
            user_id=user_id,
            product_id=data.product_id,
            rating=data.rating,
            comment=cleaned_comment,
        )

    def create_reply(self, author_id: uuid.UUID, data: ReviewReplyCreate) -> ReviewReply:
        cleaned_comment = data.comment.strip() if data.comment else None
        if not cleaned_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Текст ответа не может быть пустым",
            )
        return ReviewReply(
            review_id=data.review_id,
            author_id=author_id,
            reply_text=cleaned_comment, 
        )


class ReviewService:

    def __init__(
        self,
        db: AsyncSession,
        factory: Optional[FeedbackEntityFactory] = None,
        ):
        self.db = db
        self.factory = factory or StandardFeedbackFactory()


    async def get_review_by_id(self, review_id: uuid.UUID) -> Review:
        stmt = select(Review).where(Review.id == review_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


    async def get_reviews_by_product(self, product_id: uuid.UUID) -> List[Review]:
        stmt = select(Review).where(Review.product_id == product_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


    async def get_replies_by_review(self, review_id: uuid.UUID) -> list[ReviewReply]:
        stmt = select(ReviewReply).where(ReviewReply.review_id == review_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


    async def add_review(self, user_id: uuid.UUID, data: ReviewCreate) -> Review:
        review = self.factory.create_review(user_id=user_id, data=data)

        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review


    async def add_reply(self, author_id: uuid.UUID, data: ReviewReplyCreate) -> ReviewReply:
        review = await self.get_review_by_id(data.review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Отзыв, на который формируется ответ, не найден",
            )
        
        reply = self.factory.create_reply(author_id=author_id, data=data)

        self.db.add(reply)
        await self.db.commit()
        await self.db.refresh(reply)
        return reply


