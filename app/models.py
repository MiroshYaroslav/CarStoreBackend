from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, SmallInteger, TIMESTAMP, func, \
    UniqueConstraint, DateTime, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone


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
    base_price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id", ondelete="SET NULL"), nullable=True)
    image = Column(String, nullable=True)


    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product")

    engines = relationship("ProductEngine", back_populates="product", cascade="all, delete-orphan")
    colors = relationship("ProductColor", back_populates="product", cascade="all, delete-orphan")
    trims = relationship("ProductTrim", back_populates="product", cascade="all, delete-orphan")


class ProductEngine(Base):
    __tablename__ = "product_engine"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    volume = Column(Numeric(3, 1), nullable=False)
    power = Column(Integer, nullable=False)
    acceleration = Column(Numeric(4, 2), nullable=False)

    top_speed = Column(Integer, nullable=True)

    price_modifier = Column(Numeric(10, 2), default=0)
    fuel_type = Column(String(50), default="Petrol")

    product = relationship("Product", back_populates="engines")


class ProductColor(Base):
    __tablename__ = "product_color"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    hex_code = Column(String(7))
    price_modifier = Column(Numeric(10, 2), default=0)
    image_url = Column(String(255))

    product = relationship("Product", back_populates="colors")


class ProductTrim(Base):
    __tablename__ = "product_trim"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price_modifier = Column(Numeric(10, 2), default=0)

    product = relationship("Product", back_populates="trims")


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
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")


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


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"), nullable=False)

    engine_id = Column(Integer, ForeignKey("product_engine.id"), nullable=True)
    color_id = Column(Integer, ForeignKey("product_color.id"), nullable=True)
    trim_id = Column(Integer, ForeignKey("product_trim.id"), nullable=True)

    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

    engine = relationship("ProductEngine")
    color = relationship("ProductColor")
    trim = relationship("ProductTrim")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    status = Column(String, default="pending")
    total_price = Column(Float)

    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("product.id"))

    engine_id = Column(Integer, ForeignKey("product_engine.id"), nullable=True)
    color_id = Column(Integer, ForeignKey("product_color.id"), nullable=True)
    trim_id = Column(Integer, ForeignKey("product_trim.id"), nullable=True)

    quantity = Column(Integer, default=1)
    price_per_unit = Column(Float)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    engine = relationship("ProductEngine")
    color = relationship("ProductColor")
    trim = relationship("ProductTrim")