from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
import logging

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/cart", tags=["cart"])
logger = logging.getLogger("bmw_api.cart")


@router.get("/", response_model=list[schemas.CartItemRead])
async def list_cart_items(
        user_id: int | None = Query(None, description="Filter by user_id"),
        db: AsyncSession = Depends(get_db),
):
    try:
        query = select(models.CartItem).options(
            selectinload(models.CartItem.product),
            selectinload(models.CartItem.engine),
            selectinload(models.CartItem.color),
            selectinload(models.CartItem.trim)
        )
        if user_id is not None:
            query = query.where(models.CartItem.user_id == user_id)

        query = query.order_by(models.CartItem.created_at.desc())

        res = await db.execute(query)
        return res.scalars().all()
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


async def _validate_refs(db: AsyncSession, data: dict):
    if data.get("user_id"):
        if not await db.get(models.User, data["user_id"]):
            raise HTTPException(status_code=400, detail="user_id not found")

    if data.get("product_id"):
        if not await db.get(models.Product, data["product_id"]):
            raise HTTPException(status_code=400, detail="product_id not found")

    if data.get("engine_id"):
        if not await db.get(models.ProductEngine, data["engine_id"]):
            raise HTTPException(status_code=400, detail="engine_id not found")

    if data.get("color_id"):
        if not await db.get(models.ProductColor, data["color_id"]):
            raise HTTPException(status_code=400, detail="color_id not found")

    if data.get("trim_id"):
        if not await db.get(models.ProductTrim, data["trim_id"]):
            raise HTTPException(status_code=400, detail="trim_id not found")


@router.post("/", response_model=schemas.CartItemRead)
async def create_cart_item(payload: schemas.CartItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        data = payload.model_dump()

        await _validate_refs(db, data)

        stmt = select(models.CartItem).where(
            and_(
                models.CartItem.user_id == data["user_id"],
                models.CartItem.product_id == data["product_id"],
                models.CartItem.engine_id == data.get("engine_id"),
                models.CartItem.color_id == data.get("color_id"),
                models.CartItem.trim_id == data.get("trim_id")
            )
        )
        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        final_item_id = None

        if existing_item:
            existing_item.quantity += data.get("quantity", 1)
            final_item_id = existing_item.id
        else:
            new_item = models.CartItem(**data)
            db.add(new_item)
            await db.commit()
            final_item_id = new_item.id

        await db.commit()


        query = select(models.CartItem).options(
            selectinload(models.CartItem.product),
            selectinload(models.CartItem.engine),
            selectinload(models.CartItem.color),
            selectinload(models.CartItem.trim)
        ).where(models.CartItem.id == final_item_id)

        result = await db.execute(query)
        refreshed_item = result.scalars().first()

        return refreshed_item

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{item_id}", response_model=schemas.CartItemRead)
async def update_cart_item(item_id: int, payload: schemas.CartItemUpdate, db: AsyncSession = Depends(get_db)):
    try:
        item = await db.get(models.CartItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        if payload.quantity is not None:
            if payload.quantity <= 0:

                raise HTTPException(status_code=400, detail="Quantity must be > 0")
            item.quantity = payload.quantity

        await db.commit()

        query = select(models.CartItem).options(
            selectinload(models.CartItem.product),
            selectinload(models.CartItem.engine),
            selectinload(models.CartItem.color),
            selectinload(models.CartItem.trim)
        ).where(models.CartItem.id == item_id)

        result = await db.execute(query)
        return result.scalars().first()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{item_id}", response_model=dict)
async def delete_cart_item(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        item = await db.get(models.CartItem, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        await db.delete(item)
        await db.commit()
        return {"status": "ok", "message": f"Cart item {item_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Internal server error")