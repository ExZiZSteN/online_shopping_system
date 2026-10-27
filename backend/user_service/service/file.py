import os
import uuid
from pathlib import Path
from typing import List, Optional

from minio import Minio
import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.models.file import File
from user_service.models.reviews import Review



class FileValidator:
    """Подсистема валидации формата, размера и лимитов прикрепляемых файлов"""


    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
    MAX_FILE_SIZE = 20*1024*1024 # 20 MB
    MAX_FILES_PER_REVIEW = 5

    @classmethod
    def validate_media_type(cls, file: UploadFile) -> str:
        content_type = file.content_type
        if content_type in cls.ALLOWED_IMAGE_TYPES:
            return "image"
        if content_type in cls.ALLOWED_VIDEO_TYPES:
            return "video"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недопустимый формат файла. " \
            "Разрешены только фото (JPEG, PNG, WEBP) и ведео (MP4, WEBM, MOV)"
        )

    @classmethod
    def validate_file_size(cls, size_in_bytes: int) -> None:
        if size_in_bytes > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Размер файла превышает максимально допустимый ({cls.MAX_FILE_SIZE // (1024 * 1024)} МБ)"
            )


class MinioStorageSubSystem:
    """Подсистема взаимодействия с MinIO"""

    def __init__(self) -> None:
        self.endpoint = os.getenv("MINIO_ENDPOINT")
        self.access_key= os.getenv("MINIO_ACCESS_KEY")
        self.secret_key = os.getenv("MINIO_SECRET_KEY")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME")
        self.secure = os.getenv("MINIO_SECURE").lower() == "true"

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        self._ensure_bucket_exists()


    def _ensure_bucket_exists(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except Exception:
            pass


    def upload_file_stream(self, upload_file: UploadFile) -> str:
        """Загружает файл в бакет MinIO и возвращает сгенерированное имя объекта"""
        file_ext = Path(upload_file.filename or "").suffix.lower()
        unique_object_name = f"reviews/{uuid.uuid4()}{file_ext}"

        file_size = upload_file.size or 0
        if file_size > 0:
            FileValidator.validate_file_size(file_size)

        upload_file.file.seek(0)

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=unique_object_name,
            data=upload_file.file,
            length=file_size if file_size > 0 else -1,
            part_size=10 * 1024 * 1024 if file_size <= 0 else 0,
            content_type=upload_file.content_type,
        )
        return unique_object_name


    def remove_object(self, object_name: str) -> None:
        """Удаляет файл из MinIO при сбое в БД."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except Exception:
            pass



class FileRepositorySubsystem:
    """Репозиторий методанных в PostgreSql"""
    def  __init__(self, db: AsyncSession):
        self.db = db


    async def get_review(self, review_id: uuid.UUID) -> Optional[Review]:
        stmt = select(Review).where(Review.id == review_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()


    async def count_review_files(self, review_id: uuid.UUID) -> int:
        stmt = select(func.count(File.id)).where(File.review_id == review_id)
        res = await self.db.execute(stmt)
        return res.scalar() or 0


    async def save_file_record(self, owner_id: uuid.UUID, review_id: uuid.UUID, filename: str) -> File:
        file_record = File(
            owner_id=owner_id,
            filename=filename,
            review_id= review_id,
        )
        self.db.add(file_record)
        await self.db.commit()
        await self.db.refresh(file_record)
        return file_record


    async def get_review_files(self, review_id: uuid.UUID) -> List[File]:
        stmt = select(File).where(File.review_id == review_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())



class FileFacade:
    def __init__(self, db: AsyncSession):
        self.validator = FileValidator()
        self.storage = MinioStorageSubSystem()
        self.repository = FileRepositorySubsystem(db)


    async def upload_review_media(
            self,
            owner_id: uuid.UUID,
            review_id: uuid.UUID,
            upload_file: UploadFile,
    ) -> File:
        
        review = await self.repository.get_review(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв не найден")
        if review.user_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя прикрепить медиафайлы к чужому отзыву",
            )

        current_count = await self.repository.count_review_files(review_id)
        if current_count >= self.validator.MAX_FILES_PER_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"К отзыву нельзхя прикрепить больше {self.validator.MAX_FILES_PER_REVIEW} фото/видео",
            )

        self.validator.validate_media_type(upload_file)

        saved_object_name = self.storage.upload_file_stream(upload_file)

        try:
            return await self.repository.save_file_record(
                owner_id=owner_id,
                filename=saved_object_name,
                review_id=review_id,
            )
        except Exception:
            self.storage.remove_object(saved_object_name)
            raise

    async def get_review_attachments(self, review_id: uuid.UUID) -> List[File]:
        return await self.repository.get_review_files(review_id)