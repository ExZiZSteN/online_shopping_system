from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from catalog_service.database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


