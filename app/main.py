import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.routers import categories, products, reviews, phone_numbers, users, favorites

logger = logging.getLogger("bmw_api")
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Підключення до бази даних успішне!")
    except SQLAlchemyError as db_err:
        logger.exception("❌ Помилка підключення до БД: %s", db_err)
    yield
    logger.info("Штатне завершення роботи додатку")

app = FastAPI(
    title="BMW Catalog API",
    debug=True,
    lifespan=lifespan
)
logger.info("MAIN.PY IS RUNNING")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="app/images"), name="images")

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(phone_numbers.router)
app.include_router(users.router)
app.include_router(favorites.router)

@app.get("/")
def root():
    return {"message": "BMW Catalog API works!"}

logger.info("Registered routes:")
for r in app.routes:
    path = getattr(r, "path", None)
    methods = getattr(r, "methods", None)
    if path and methods:
        logger.info("  %s %s", methods, path)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    logger.info("Incoming request: %s %s from %s", request.method, request.url.path, client)
    try:
        response = await call_next(request)
        logger.info("Response %s for %s %s", response.status_code, request.method, request.url.path)
        return response
    except Exception as exc:
        logger.exception("Unhandled exception during request: %s", exc)
        raise
