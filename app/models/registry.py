"""Import every mapped model so SQLAlchemy can build complete metadata."""

from app.models.base import BaseDB
from app.models.callback_request import CallbackRequest
from app.models.cart import CartItem
from app.models.category import Category
from app.models.favorite import Favorite
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_color import ProductColor
from app.models.product_engine import ProductEngine
from app.models.product_trim import ProductTrim
from app.models.review import Review
from app.models.session import Session
from app.models.user import User

__all__ = [
    "BaseDB",
    "CallbackRequest",
    "CartItem",
    "Category",
    "Favorite",
    "Order",
    "OrderItem",
    "Product",
    "ProductColor",
    "ProductEngine",
    "ProductTrim",
    "Review",
    "User",
    "Session",
]
