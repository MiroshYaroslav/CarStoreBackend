from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import logging
from passlib.hash import bcrypt
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("bmw_api.users")


@router.get("/", response_model=list[schemas.UserRead])
async def list_users(db: AsyncSession = Depends(get_db)):
    try:
        res = await db.execute(select(models.User))
        return res.scalars().all()
    except Exception:
        logger.exception("Failed to list users")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=schemas.UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await db.get(models.User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get user")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=schemas.UserRead)
async def create_user(payload: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        hashed_password = bcrypt.hash(payload.password)
        user = models.User(
            email=payload.email,
            username=payload.username,
            password_hash=hashed_password
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Email or username already exists") from e
        return user
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to create user")
        raise HTTPException(status_code=500, detail="Internal server error")



@router.patch("/{user_id}", response_model=schemas.UserRead)
async def update_user(user_id: int, payload: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    try:
        user = await db.get(models.User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        data = payload.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(user, k, v)
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Email or username already exists") from e
        return user
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update user")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await db.get(models.User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await db.delete(user)
        await db.commit()
        return {"status": "ok", "message": f"User {user_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete user")
        raise HTTPException(status_code=500, detail="Internal server error")
