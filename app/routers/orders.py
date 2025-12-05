from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app import models, schemas
from app.routers.users import get_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=schemas.OrderRead)
async def create_order(
        order_data: schemas.OrderCreate,
        user: models.User = Depends(get_user),
        db: AsyncSession = Depends(get_db)
):

    cart_query = select(models.CartItem).options(
        selectinload(models.CartItem.product),
        selectinload(models.CartItem.engine),
        selectinload(models.CartItem.color),
        selectinload(models.CartItem.trim),
    ).where(models.CartItem.user_id == user.id)

    result = await db.execute(cart_query)
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_price = 0
    new_order_items = []

    for item in cart_items:
        item_price = item.product.base_price
        if item.engine: item_price += item.engine.price_modifier
        if item.color: item_price += item.color.price_modifier
        if item.trim: item_price += item.trim.price_modifier

        total_price += item_price * item.quantity

        new_order_item = models.OrderItem(
            product_id=item.product_id,
            engine_id=item.engine_id,
            color_id=item.color_id,
            trim_id=item.trim_id,
            quantity=item.quantity,
            price_per_unit=item_price
        )
        new_order_items.append(new_order_item)

    new_order = models.Order(
        user_id=user.id,
        total_price=total_price,
        status="created",
        **order_data.model_dump()
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    for order_item in new_order_items:
        order_item.order_id = new_order.id
        db.add(order_item)

    for item in cart_items:
        await db.delete(item)

    await db.commit()

    query = select(models.Order).options(
        selectinload(models.Order.items).options(
            selectinload(models.OrderItem.product).options(
                selectinload(models.Product.engines),
                selectinload(models.Product.colors),
                selectinload(models.Product.trims),
            ),
            selectinload(models.OrderItem.engine),
            selectinload(models.OrderItem.color),
            selectinload(models.OrderItem.trim),
        )
    ).where(models.Order.id == new_order.id)

    result = await db.execute(query)
    final_order = result.scalars().first()

    return final_order


@router.get("/", response_model=list[schemas.OrderRead])
async def get_my_orders(
    user: models.User = Depends(get_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Order).options(
        selectinload(models.Order.items).options(
            selectinload(models.OrderItem.product).options(
                selectinload(models.Product.engines),
                selectinload(models.Product.colors),
                selectinload(models.Product.trims),
            ),
            selectinload(models.OrderItem.engine),
            selectinload(models.OrderItem.color),
            selectinload(models.OrderItem.trim),
        )
    ).where(models.Order.user_id == user.id).order_by(models.Order.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()