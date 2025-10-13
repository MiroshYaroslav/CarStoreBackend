from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import FavoriteDB, CarDB


def add_favorite(db: Session, user_id: int, car_id: int):
    existing = db.query(FavoriteDB).filter_by(user_id=user_id, car_id=car_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")
    fav = FavoriteDB(user_id=user_id, car_id=car_id)
    db.add(fav)
    db.commit()
    return {"detail": "Added to favorites"}

def remove_favorite(db: Session, user_id: int, car_id: int):
    fav = db.query(FavoriteDB).filter_by(user_id=user_id, car_id=car_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Not found in favorites")
    db.delete(fav)
    db.commit()
    return {"detail": "Removed from favorites"}

def get_favorites(db: Session, user_id: int):
    return (
        db.query(CarDB)
        .join(FavoriteDB, CarDB.id == FavoriteDB.car_id)
        .filter(FavoriteDB.user_id == user_id)
        .all()
    )

def clear_favorites(db: Session, user_id: int):
    deleted = db.query(FavoriteDB).filter(FavoriteDB.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return {"detail": f"Cleared {deleted} items from favorites"}
