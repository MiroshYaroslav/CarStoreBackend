import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.api.dependencies import CatalogAdmin, DBSession
from app.core.idempotency import IdempotencyDep
from app.models.async_task import TaskStatus
from app.repositories.callback_request_repository import CallbackRequestRepository
from app.schemas.callback_request import (
    CallbackRequestCreate,
    CallbackRequestRead,
    CallbackRequestUpdate,
)
from app.services.callback_request_service import CallbackRequestService

router = APIRouter()


class AsyncTaskQueuedResponse(BaseModel):
    task_id: uuid.UUID
    status: TaskStatus
    status_url: str


class AsyncTaskStatusResponse(BaseModel):
    task_id: uuid.UUID
    status: TaskStatus
    result: dict | None = None
    error_message: str | None = None


def get_callback_request_repo(session: DBSession) -> CallbackRequestRepository:
    return CallbackRequestRepository(session)


CallbackRequestRepoDep = Annotated[
    CallbackRequestRepository, Depends(get_callback_request_repo)
]


def get_callback_request_service(
    session: DBSession, repo: CallbackRequestRepoDep
) -> CallbackRequestService:
    return CallbackRequestService(session, repo)


CallbackRequestServiceDep = Annotated[
    CallbackRequestService, Depends(get_callback_request_service)
]


@router.post("/", response_model=CallbackRequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_in: CallbackRequestCreate,
    response: Response,
    service: CallbackRequestServiceDep,
    idempotency: IdempotencyDep,
):
    return await idempotency.execute(
        response=response,
        status_code=status.HTTP_201_CREATED,
        action=lambda: service.create_request(request_in),
    )


@router.post(
    "/async",
    response_model=AsyncTaskQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_request_async(
    request_in: CallbackRequestCreate,
    response: Response,
    service: CallbackRequestServiceDep,
    idempotency: IdempotencyDep,
):
    async def _enqueue() -> AsyncTaskQueuedResponse:
        task = await service.enqueue_request(request_in)
        return AsyncTaskQueuedResponse(
            task_id=task.id,
            status=task.status,
            status_url=f"/api/v1/callback-requests/tasks/{task.id}",
        )

    return await idempotency.execute(
        response=response,
        status_code=status.HTTP_202_ACCEPTED,
        action=_enqueue,
    )


@router.get("/tasks/{task_id}", response_model=AsyncTaskStatusResponse)
async def get_async_task_status(task_id: uuid.UUID, service: CallbackRequestServiceDep):
    task = await service.get_task_status(task_id)
    return AsyncTaskStatusResponse(
        task_id=task.id,
        status=task.status,
        result=json.loads(task.result) if task.result else None,
        error_message=task.error_message,
    )


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