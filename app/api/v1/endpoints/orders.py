from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUser, DBSession, get_optional_user
from app.models.user import User
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import OrderService

router = APIRouter()


def get_order_repo(session: DBSession) -> OrderRepository:
    return OrderRepository(session)


def get_order_item_repo(session: DBSession) -> OrderItemRepository:
    return OrderItemRepository(session)


def get_cart_repo(session: DBSession) -> CartRepository:
    return CartRepository(session)


OrderRepoDep = Annotated[OrderRepository, Depends(get_order_repo)]
OrderItemRepoDep = Annotated[OrderItemRepository, Depends(get_order_item_repo)]
CartRepoDep = Annotated[CartRepository, Depends(get_cart_repo)]


def get_order_service(
    session: DBSession, orders: OrderRepoDep, items: OrderItemRepoDep, cart: CartRepoDep
) -> OrderService:
    return OrderService(session, orders, items, cart)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate, service: OrderServiceDep, user: User | None = Depends(get_optional_user)
):
    return await service.create_order(order_in, user_id=user.id if user else None)


@router.get("/my", response_model=list[OrderRead])
async def get_my_orders(user: CurrentUser, service: OrderServiceDep):
    return await service.list_user_orders(user.id)
