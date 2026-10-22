import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies import CatalogAdmin, CurrentUser, DBSession
from app.core.config import settings
from app.models.user import User
from app.repositories.product_repository import (
    ColorRepository,
    EngineRepository,
    ProductRepository,
    TrimRepository,
)
from app.schemas.product import (
    ColorCreate,
    ColorRead,
    EngineCreate,
    EngineRead,
    ProductRead,
    TrimCreate,
    TrimRead,
)
from app.services.product_service import ProductService
from app.services.s3_service import S3Service


def get_s3_service() -> S3Service:
    return S3Service()


S3ServiceDep = Annotated[S3Service, Depends(get_s3_service)]


router = APIRouter()


def require_product_image_uploader(user: CurrentUser) -> User:
    allowed_user_ids = {
        user_id.strip().casefold()
        for user_id in settings.PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS
        if user_id.strip()
    }
    if not allowed_user_ids or str(user.id).casefold() not in allowed_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to upload product images",
        )
    return user


ProductImageUploader = Annotated[User, Depends(require_product_image_uploader)]


def get_product_repo(session: DBSession) -> ProductRepository:
    return ProductRepository(session)


def get_engine_repo(session: DBSession) -> EngineRepository:
    return EngineRepository(session)


def get_color_repo(session: DBSession) -> ColorRepository:
    return ColorRepository(session)


def get_trim_repo(session: DBSession) -> TrimRepository:
    return TrimRepository(session)


ProductRepoDep = Annotated[ProductRepository, Depends(get_product_repo)]
EngineRepoDep = Annotated[EngineRepository, Depends(get_engine_repo)]
ColorRepoDep = Annotated[ColorRepository, Depends(get_color_repo)]
TrimRepoDep = Annotated[TrimRepository, Depends(get_trim_repo)]


def get_product_service(
    session: DBSession,
    products: ProductRepoDep,
    engines: EngineRepoDep,
    colors: ColorRepoDep,
    trims: TrimRepoDep,
) -> ProductService:
    return ProductService(session, products, engines, colors, trims)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]


@router.get("/", response_model=list[ProductRead])
async def get_products(
    service: ProductServiceDep,
    category_id: list[uuid.UUID] | None = Query(None),
    search: str | None = Query(None),
    min_price: Decimal | None = Query(None),
    max_price: Decimal | None = Query(None),
    sort: str | None = Query(None),
    active_only: bool = Query(True),
):
    return await service.list_products(
        category_id=category_id,
        search=search,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        active_only=active_only,
    )


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, service: ProductServiceDep):
    return await service.get_product_or_404(product_id)


@router.post(
    "/{product_id}/engines", response_model=EngineRead, status_code=status.HTTP_201_CREATED
)
async def create_product_engine(
    product_id: uuid.UUID, engine: EngineCreate, service: ProductServiceDep, _: CatalogAdmin
):
    return await service.add_engine(product_id, engine)


@router.post("/{product_id}/colors", response_model=ColorRead, status_code=status.HTTP_201_CREATED)
async def create_product_color(
    product_id: uuid.UUID, color: ColorCreate, service: ProductServiceDep, _: CatalogAdmin
):
    return await service.add_color(product_id, color)


@router.post("/{product_id}/trims", response_model=TrimRead, status_code=status.HTTP_201_CREATED)
async def create_product_trim(
    product_id: uuid.UUID, trim: TrimCreate, service: ProductServiceDep, _: CatalogAdmin
):
    return await service.add_trim(product_id, trim)


@router.delete("/{product_id}")
async def soft_delete_product(product_id: uuid.UUID, service: ProductServiceDep, _: CatalogAdmin):
    await service.soft_delete(product_id)
    return {"status": "ok", "message": f"Product {product_id} deactivated successfully"}


@router.post("/{product_id}/image", response_model=ProductRead)
async def upload_product_image(
    product_id: uuid.UUID,
    _: ProductImageUploader,
    service: ProductServiceDep,
    s3_service: S3ServiceDep,
    file: UploadFile = File(...),
):
    await service.get_product_or_404(product_id)
    image_url = await s3_service.upload_image(file)

    return await service.update_product_image(product_id, image_url)
