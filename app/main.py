import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.database import engine
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

    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Application shutdown complete.")


app = FastAPI(title=settings.PROJECT_NAME, openapi_url="/api/v1/openapi.json", lifespan=lifespan)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(TimingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": f"{settings.PROJECT_NAME} works! Go to /docs for Swagger UI"}
