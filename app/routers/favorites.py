from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import logging

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/favorites", tags=["favorites"])
logger = logging.getLogger("bmw_api.favorites")


@router.get("/", response_model=list[schemas.FavoriteRead])
async def list_favorites(user_id: int | None = Query(None, description="Filter by user_id"), db: AsyncSession = Depends(get_db)):
    try:
        query = select(models.Favorite)
        if user_id is not None:
            query = query.where(models.Favorite.user_id == user_id)
        res = await db.execute(query)
        return res.scalars().all()
    except Exception:
        logger.exception("Failed to list favorites")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{fav_id}", response_model=schemas.FavoriteRead)
async def get_favorite(fav_id: int, db: AsyncSession = Depends(get_db)):
    try:
        fav = await db.get(models.Favorite, fav_id)
        if not fav:
            raise HTTPException(status_code=404, detail="Favorite not found")
        return fav
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get favorite")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _validate_refs(db: AsyncSession, user_id: int | None, product_id: int | None):
    if user_id is not None:
        if not await db.get(models.User, user_id):
            raise HTTPException(status_code=400, detail="user_id not found")
    if product_id is not None:
        if not await db.get(models.Product, product_id):
            raise HTTPException(status_code=400, detail="product_id not found")


@router.post("/", response_model=schemas.FavoriteRead)
async def create_favorite(payload: schemas.FavoriteCreate, db: AsyncSession = Depends(get_db)):
    try:
        data = payload.model_dump()
        await _validate_refs(db, data.get("user_id"), data.get("product_id"))
        fav = models.Favorite(**data)
        db.add(fav)
        try:
            await db.commit()
            await db.refresh(fav)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail="This product is already in favorites for the user") from e
        return fav
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create favorite")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{fav_id}", response_model=schemas.FavoriteRead)
async def update_favorite(fav_id: int, payload: schemas.FavoriteUpdate, db: AsyncSession = Depends(get_db)):
    try:
        fav = await db.get(models.Favorite, fav_id)
        if not fav:
            raise HTTPException(status_code=404, detail="Favorite not found")
        data = payload.model_dump(exclude_unset=True)
        await _validate_refs(db, data.get("user_id"), data.get("product_id"))
        for k, v in data.items():
            setattr(fav, k, v)
        try:
            await db.commit()
            await db.refresh(fav)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail="This product is already in favorites for the user") from e
        return fav
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update favorite")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{fav_id}", response_model=dict)
async def delete_favorite(fav_id: int, db: AsyncSession = Depends(get_db)):
    try:
        fav = await db.get(models.Favorite, fav_id)
        if not fav:
            raise HTTPException(status_code=404, detail="Favorite not found")
        await db.delete(fav)
        await db.commit()
        return {"status": "ok", "message": f"Favorite {fav_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete favorite")
        raise HTTPException(status_code=500, detail="Internal server error")
