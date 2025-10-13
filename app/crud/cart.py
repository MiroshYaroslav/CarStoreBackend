from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import CartDB, CarDB


def add_cart(db: Session, user_id: int, car_id: int):
    existing = db.query(CartDB).filter_by(user_id=user_id, car_id=car_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in cart")
    cart_item = CartDB(user_id=user_id, car_id=car_id)
    db.add(cart_item)
    db.commit()
    return {"detail": "Added to cart"}

def remove_cart(db: Session, user_id: int, car_id: int):
    item = db.query(CartDB).filter_by(user_id=user_id, car_id=car_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found in cart")
    db.delete(item)
    db.commit()
    return {"detail": "Removed from cart"}

def get_cart(db: Session, user_id: int):
    return (
        db.query(CarDB)
        .join(CartDB, CarDB.id == CartDB.car_id)
        .filter(CartDB.user_id == user_id)
        .all()
    )

def clear_cart(db: Session, user_id: int):
    deleted = db.query(CartDB).filter(CartDB.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return {"detail": f"Cleared {deleted} items from cart"}
