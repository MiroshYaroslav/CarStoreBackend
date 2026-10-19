from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    callback_contacts,
    callback_requests,
    cart,
    categories,
    favorites,
    orders,
    products,
    reviews,
    users,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(categories.router, prefix="/categories", tags=["categories"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
router.include_router(
    callback_requests.router, prefix="/callback-requests", tags=["callback-requests"]
)
router.include_router(
    callback_contacts.router, prefix="/callback-contacts", tags=["callback-contacts"]
)
router.include_router(cart.router, prefix="/cart", tags=["cart"])
router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
router.include_router(orders.router, prefix="/orders", tags=["orders"])
