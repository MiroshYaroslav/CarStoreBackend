import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.database import engine
from app.core.redis import get_redis_client, redis_pool
from app.exceptions.base import AppException
from app.exceptions.handlers import (
    app_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)
from app.middlewares.timing import TimingMiddleware

logger = logging.getLogger("bmw_api")
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
    except SQLAlchemyError as db_err:
        logger.exception("Database connection failed: %s", db_err)
        raise

    app.state.redis = get_redis_client()

    try:
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized.")
    except Exception as redis_err:
        logger.warning(f"Redis is not available at startup: {redis_err}")

    try:
        yield
    finally:
        await app.state.redis.aclose()
        await redis_pool.disconnect()
        await engine.dispose()
        logger.info("Application shutdown complete.")


middlewares = [
    Middleware(TimingMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
    Middleware(GZipMiddleware, minimum_size=1000),
]

exception_handlers = {
    AppException: app_exception_handler,
    RequestValidationError: validation_exception_handler,
    Exception: global_exception_handler,
}

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
    middleware=middlewares,
    exception_handlers=exception_handlers,
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": f"{settings.PROJECT_NAME} works! Go to /docs for Swagger UI"}
