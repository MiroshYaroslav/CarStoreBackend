from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from app.models import UserDB
from app.schemas import UserRegister, UserLogin


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ADMIN_SECRET = "1234"

def register_user(db: Session, user: UserRegister):
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    is_admin = False
    if user.admin_code:
        if user.admin_code == ADMIN_SECRET:
            is_admin = True
        else:
            raise HTTPException(status_code=403, detail="Invalid admin code")

    hashed_pw = pwd_context.hash(user.password)
    new_user = UserDB(username=user.username, password_hash=hashed_pw, is_admin=is_admin)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"user_id": new_user.id, "username": new_user.username, "is_admin": new_user.is_admin}

def login_user(db: Session, user: UserLogin):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": db_user.id, "username": db_user.username, "is_admin": bool(db_user.is_admin)}
