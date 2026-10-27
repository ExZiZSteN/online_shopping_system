import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from catalog_service.database import Base

if TYPE_CHECKING:
    from catalog_service.models.product import Product


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    article: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[str] = mapped_column(String(4), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    