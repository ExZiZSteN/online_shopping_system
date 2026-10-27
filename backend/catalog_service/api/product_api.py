import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.database import get_db
from catalog_service.schemas.product import ProductCreateSchema, ProductOut
from catalog_service.service.product import ProductService
from security.token import get_current_user_id


router = APIRouter(prefix="/products", tags=["products"])

def get_product_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ProductService:
    return ProductService(db)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreateSchema,
    seller_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProductService, Depends(get_product_service)],
):
    return await service.create_product(seller_id=seller_id, data=body)

@router.get("", response_model=List[ProductOut])
async def list_products(
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    service: Annotated[ProductService, Depends(get_product_service)] = None,
):
    return await service.list_product(category_id=category_id, min_price=min_price, max_price=max_price)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product_details(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
):
    return await service.get_product_by_id(product_id)

@router.get("/{product_id}/rendered-variants")
async def get_product_variants_rendered(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
):
    return await service.render_product_variants_flyweight(product_id)