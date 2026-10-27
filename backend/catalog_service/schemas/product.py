import uuid
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class VariantCreateSchema(BaseModel):
    article: int
    size: str = Field(..., max_length=4)
    color: str = Field(..., max_length=25)
    stock_quantity: int = Field(0, ge=0)
    price: float= Field(..., gt=0)


class ProductCreateSchema(BaseModel):
    category_id: int
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=300)
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(0, ge=0)
    variants: Optional[List[VariantCreateSchema]] = None


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: uuid.UUID
    article: int
    size: int
    color: str
    stock_quantity: int
    price: float


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: int
    category_id: int
    description: str
    price: float
    stock_quantity: int
    is_active: bool
    variants: List[ProductVariantOut] = []