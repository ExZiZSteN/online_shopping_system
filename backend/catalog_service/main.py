from contextlib import asynccontextmanager
from fastapi import FastAPI

from catalog_service.database import engine, Base
from catalog_service.api.router import router as catalog_router

import catalog_service.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Catalog Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(catalog_router)