import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CatalogAdmin, DBSession
from app.repositories.callback_request_repository import CallbackRequestRepository
from app.schemas.callback_request import (
    CallbackRequestCreate,
    CallbackRequestRead,
    CallbackRequestUpdate,
)
from app.services.callback_request_service import CallbackRequestService

router = APIRouter()


def get_callback_request_repo(session: DBSession) -> CallbackRequestRepository:
    return CallbackRequestRepository(session)


CallbackRequestRepoDep = Annotated[CallbackRequestRepository, Depends(get_callback_request_repo)]


def get_callback_request_service(
    session: DBSession, repo: CallbackRequestRepoDep
) -> CallbackRequestService:
    return CallbackRequestService(session, repo)


CallbackRequestServiceDep = Annotated[CallbackRequestService, Depends(get_callback_request_service)]


@router.post("/", response_model=CallbackRequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(request_in: CallbackRequestCreate, service: CallbackRequestServiceDep):
    return await service.create_request(request_in)


@router.get("/", response_model=list[CallbackRequestRead])
async def get_requests(_: CatalogAdmin, service: CallbackRequestServiceDep):
    return await service.list_requests()


@router.patch("/{request_id}", response_model=CallbackRequestRead)
async def update_request_status(
    request_id: uuid.UUID,
    update_in: CallbackRequestUpdate,
    _: CatalogAdmin,
    service: CallbackRequestServiceDep,
):
    return await service.update_status(request_id, update_in)
