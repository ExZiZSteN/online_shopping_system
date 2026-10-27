import uuid
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from catalog_service.models.product import Product
from catalog_service.models.product_variant import ProductVariant
from catalog_service.schemas.product import ProductCreateSchema, ProductVariantOut


class ProductFlyweight:


    def __init__(self, product_id: uuid.UUID, title: str, description: str, category_id: int, seller_id: uuid.UUID):
        self.product_id = product_id
        self.title = title
        self.description = description
        self.category_id = category_id
        self.seller_id = seller_id


    def display(self, size: str, color: str, price: float, stock_quantity: int) -> dict:
        return {
            "product_id": str(self.product_id),
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "seller_id": str(self.seller_id),
            "size": size,
            "color": color,
            "price": price,
            "stock_quantity": stock_quantity,
        }


class ProductFlyweightFactory:

    def __init__(self):
        self._flyweights: Dict[uuid.UUID, ProductFlyweight] = {}


    def get_flyweight(self, product: Product) -> ProductFlyweight:
        if product.id not in self._flyweights:
            self._flyweights[product.id] = ProductFlyweight(
                product_id=product.id,
                title=product.title,
                description=product.description,
                category_id=product.category_id,
                seller_id=product.seller_id,
            )
        return self._flyweights[product.id]


    def remove_flyweight(self, product_id: uuid.UUID):
        self._flyweights.pop(product_id, None)


    @property
    def total_flyweight(self) -> int:
        return len(self._flyweights)


product_flyweight_factory= ProductFlyweightFactory()


class ProductService:
    def __init__(self, db: AsyncSession, factory: Optional[ProductFlyweightFactory] = None):
        self.db = db
        self.flyweight_factory = factory or product_flyweight_factory


    async def create_product(self, seller_id: uuid.UUID, data: ProductCreateSchema) -> Product:
        new_product = Product(
            seller_id=seller_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            price=data.price,
            stock_quantity=data.stock_quantity,
            is_active=True,
        )
        self.db.add(new_product)
        await self.db.flush()

        if data.variants:
            for v_data in data.variants:
                variant = ProductVariant(
                    product_id=new_product.id,
                    article=v_data.article,
                    size=v_data.size,
                    color=v_data.color,
                    stock_quantity=v_data.stock_quantity,
                    price=v_data.price,
                )
                self.db.add(variant)

        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product

    async def get_product_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id, Product.is_active == True).options(selectinload(Product.variants))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_product(
            self, 
            category_id: Optional[int] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            ) -> List[Product]:

        stmt = select(Product).where(Product.is_active == True).options(selectinload(Product.variants))

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def render_product_variants_flyweight(self, product_id: uuid.UUID) -> List[dict]:
        product = await self.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        flyweight = self.flyweight_factory.get_flyweight(product)
        rendered_variants = []
        for variant in product.variants:
            variant_info = flyweight.display(
                size=variant.size,
                color=variant.color,
                price=variant.price,
                stock_quantity=variant.stock_quantity,
            )
            rendered_variants.append(variant_info)

        return rendered_variants