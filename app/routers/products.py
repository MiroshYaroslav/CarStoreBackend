from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, desc
import logging

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger("bmw_api.products")


@router.get("/", response_model=list[schemas.ProductRead])
async def get_products(
    category_id: list[int] | None = Query(None, description="Filter by category_id"),
    search: str | None = Query(None, description="Search by product name"),
    min_price: float | None = Query(None, description="Minimum price"),
    max_price: float | None = Query(None, description="Maximum price"),
    sort: str | None = Query(
        None,
        description="Sort: price-asc, price-desc, power-asc, power-desc, top_speed-asc, top_speed-desc"
    ),
    db: AsyncSession = Depends(get_db),
):

    try:
        query = select(models.Product)

        if category_id:
            query = query.where(models.Product.category_id.in_(category_id))

        if search:
            query = query.where(models.Product.name.ilike(f"%{search.strip()}%"))

        if min_price is not None:
            query = query.where(models.Product.price >= min_price)
        if max_price is not None:
            query = query.where(models.Product.price <= max_price)

        if sort:
            if sort == "price-asc":
                query = query.order_by(asc(models.Product.price))
            elif sort == "price-desc":
                query = query.order_by(desc(models.Product.price))
            elif sort == "power-asc":
                query = query.order_by(asc(models.Product.power))
            elif sort == "power-desc":
                query = query.order_by(desc(models.Product.power))
            elif sort == "top_speed-asc":
                query = query.order_by(asc(models.Product.top_speed))
            elif sort == "top_speed-desc":
                query = query.order_by(desc(models.Product.top_speed))

        result = await db.execute(query)
        return result.scalars().all()

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):

    try:
        result = await db.execute(
            select(models.Product).where(models.Product.id == product_id)
        )
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return product

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=schemas.ProductRead)
async def create_product(
    product: schemas.ProductCreate,
    db: AsyncSession = Depends(get_db)
):

    try:
        payload = product.model_dump()

        if payload.get("category_id") == 0:
            payload["category_id"] = None

        if payload.get("category_id") is not None:
            res = await db.execute(
                select(models.Category).where(models.Category.id == payload["category_id"])
            )
            if not res.scalars().first():
                raise HTTPException(status_code=400, detail="category_id not found")

        new_product = models.Product(**payload)

        db.add(new_product)
        try:
            await db.commit()
            await db.refresh(new_product)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Database integrity error")

        return new_product

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{product_id}", response_model=schemas.ProductRead)
async def update_product(product_id: int, update: schemas.ProductUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(models.Product).where(models.Product.id == product_id))
        product = result.scalars().first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        data = update.model_dump(exclude_unset=True)

        if "category_id" in data and data["category_id"] == 0:
            data["category_id"] = None

        if "category_id" in data and data["category_id"] is not None:
            res = await db.execute(select(models.Category).where(models.Category.id == data["category_id"]))
            if not res.scalars().first():
                raise HTTPException(status_code=400, detail="category_id not found")

        for k, v in data.items():
            setattr(product, k, v)
        await db.commit()
        await db.refresh(product)
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{product_id}", response_model=dict)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):

    try:
        result = await db.execute(select(models.Product).where(models.Product.id == product_id))
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await db.delete(product)
        await db.commit()

        return {"status": "ok", "message": f"Product {product_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")
