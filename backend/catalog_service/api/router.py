from fastapi import APIRouter
from catalog_service.api.product_api import router as product_router

router = APIRouter()
router.include_router(product_router)