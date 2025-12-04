from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import asc, desc, func
from sqlalchemy.exc import IntegrityError
import logging

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger("bmw_api.products")


@router.get("/", response_model=list[schemas.ProductRead])
async def get_products(
        category_id: list[int] | None = Query(None, description="Filter by category_id"),
        search: str | None = Query(None, description="Search by product name"),
        min_price: float | None = Query(None, description="Minimum base price"),
        max_price: float | None = Query(None, description="Maximum base price"),
        sort: str | None = Query(
            None,
            description="Sort options: price-asc, price-desc, power-asc, power-desc"
        ),
        db: AsyncSession = Depends(get_db),
):
    try:
        query = select(models.Product).options(
            selectinload(models.Product.engines),
            selectinload(models.Product.colors),
            selectinload(models.Product.trims)
        )

        if category_id:
            query = query.where(models.Product.category_id.in_(category_id))

        if search:
            query = query.where(models.Product.name.ilike(f"%{search.strip()}%"))

        if min_price is not None:
            query = query.where(models.Product.base_price >= min_price)
        if max_price is not None:
            query = query.where(models.Product.base_price <= max_price)

        if sort:
            if sort == "price-asc":
                query = query.order_by(asc(models.Product.base_price))
            elif sort == "price-desc":
                query = query.order_by(desc(models.Product.base_price))
            elif sort in ["power-asc", "power-desc"]:
                max_power_subquery = (
                    select(func.max(models.ProductEngine.power))
                    .where(models.ProductEngine.product_id == models.Product.id)
                    .scalar_subquery()
                )

                if sort == "power-asc":
                    query = query.order_by(asc(max_power_subquery))
                elif sort == "power-desc":
                    query = query.order_by(desc(max_power_subquery))

        result = await db.execute(query)
        return result.scalars().unique().all()

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    try:
        query = select(models.Product).options(
            selectinload(models.Product.engines),
            selectinload(models.Product.colors),
            selectinload(models.Product.trims)
        ).where(models.Product.id == product_id)

        result = await db.execute(query)
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return product

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/{product_id}/engines", response_model=schemas.EngineRead)
async def create_product_engine(
        product_id: int,
        engine: schemas.EngineCreate,
        db: AsyncSession = Depends(get_db)
):
    product = await db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_engine = models.ProductEngine(**engine.model_dump(), product_id=product_id)
    db.add(new_engine)
    try:
        await db.commit()
        await db.refresh(new_engine)
        return new_engine
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Error creating engine")


@router.post("/{product_id}/colors", response_model=schemas.ColorRead)
async def create_product_color(
        product_id: int,
        color: schemas.ColorCreate,
        db: AsyncSession = Depends(get_db)
):
    product = await db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_color = models.ProductColor(**color.model_dump(), product_id=product_id)
    db.add(new_color)
    try:
        await db.commit()
        await db.refresh(new_color)
        return new_color
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Error creating color")


@router.post("/{product_id}/trims", response_model=schemas.TrimRead)
async def create_product_trim(
        product_id: int,
        trim: schemas.TrimCreate,
        db: AsyncSession = Depends(get_db)
):
    product = await db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_trim = models.ProductTrim(**trim.model_dump(), product_id=product_id)
    db.add(new_trim)
    try:
        await db.commit()
        await db.refresh(new_trim)
        return new_trim
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Error creating trim")