from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, SmallInteger, TIMESTAMP, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10,2), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="SET NULL"), nullable=True)

    power = Column(Integer, nullable=True)
    top_speed = Column(Integer, nullable=True)
    acceleration = Column(Numeric(4,2), nullable=True)

    image = Column(String, nullable=True)

    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(100), nullable=False)
    rating = Column(SmallInteger, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    product = relationship("Product", back_populates="reviews")

class PhoneNumber(Base):
    __tablename__ = "phone_number"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    username = Column(String(100), unique=True, nullable=True)

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_favorites_user_product"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="favorites")
    product = relationship("Product")
