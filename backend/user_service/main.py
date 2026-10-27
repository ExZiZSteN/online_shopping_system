from contextlib import asynccontextmanager
from fastapi import FastAPI
from user_service.database import engine, Base
from user_service.api.router import router as user_router

import user_service.models.user
import user_service.models.review_replies
import user_service.models.reviews

@asynccontextmanager
async def lifespan():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="User Service", version='1.0.0', lifespan=lifespan)

app.include_router(user_router)