import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import DBSession, get_optional_user
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemCreate, CartItemRead
from app.services.cart_service import CartService

router = APIRouter()


def get_cart_repo(session: DBSession) -> CartRepository:
    return CartRepository(session)


def get_product_repo(session: DBSession) -> ProductRepository:
    return ProductRepository(session)


CartRepoDep = Annotated[CartRepository, Depends(get_cart_repo)]
ProductRepoDep = Annotated[ProductRepository, Depends(get_product_repo)]


def get_cart_service(
    session: DBSession, repo: CartRepoDep, products: ProductRepoDep
) -> CartService:
    return CartService(session, repo, products)


CartServiceDep = Annotated[CartService, Depends(get_cart_service)]


@router.get("/", response_model=list[CartItemRead])
async def get_cart(
    service: CartServiceDep,
    user: User | None = Depends(get_optional_user),
    session_id: str | None = Query(None),
):
    return await service.get_cart(user_id=user.id if user else None, session_id=session_id)


@router.post("/", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item_in: CartItemCreate, service: CartServiceDep, user: User | None = Depends(get_optional_user)
):
    return await service.add_to_cart(item_in=item_in, user_id=user.id if user else None)


@router.delete("/{item_id}")
async def remove_from_cart(item_id: uuid.UUID, service: CartServiceDep):
    await service.remove_item(item_id)
    return {"status": "ok", "message": "Item removed from cart"}
