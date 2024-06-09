import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.auth import router as auth_router
from src.api.users import router as users_router
from src.broker.consumer import get_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    consumer = get_consumer()
    consuming = asyncio.create_task(consumer.consume())
    await asyncio.gather(consuming)
    yield
    

app = FastAPI(
    title="Auth service",
    description="Digital twin auth microservice.",
    version="0.0.1",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(users_router)
