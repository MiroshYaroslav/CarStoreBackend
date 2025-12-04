from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from app.models import Category, Product, Review

logger = logging.getLogger(__name__)

async def get_categories(db: AsyncSession):
    try:
        result = await db.execute(select(Category))
        return result.scalars().all()
    except Exception:
        logger.exception("Error in get_categories")
        raise

async def get_products(db: AsyncSession):
    try:
        result = await db.execute(select(Product))
        return result.scalars().all()
    except Exception:
        logger.exception("Error in get_products")
        raise

async def get_reviews(db: AsyncSession):
    try:
        result = await db.execute(select(Review))
        return result.scalars().all()
    except Exception:
        logger.exception("Error in get_reviews")
        raise

