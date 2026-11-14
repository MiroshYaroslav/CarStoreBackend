import asyncio
import json
import uuid

import boto3
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.base import AppException, ConflictException, NotFoundException
from app.models.async_task import AsyncTask, TaskStatus
from app.repositories.callback_request_repository import CallbackRequestRepository
from app.schemas.callback_request import CallbackRequestCreate, CallbackRequestUpdate
from app.services.base import BaseService

sqs_client = boto3.client("sqs", region_name=settings.AWS_REGION or "eu-central-1")


class CallbackRequestService(BaseService):
    def __init__(self, session: AsyncSession, repository: CallbackRequestRepository):
        super().__init__(session)
        self._repository = repository

    async def list_requests(self):
        return await self._repository.get_many()

    async def create_request(self, request_in: CallbackRequestCreate):
        try:
            result = await self._repository.create(request_in.model_dump())
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Callback request conflicts with existing data")

    async def update_status(self, request_id: uuid.UUID, update_in: CallbackRequestUpdate):
        try:
            result = await self._repository.update(
                request_id, update_in.model_dump(exclude_unset=True)
            )
            if not result:
                raise NotFoundException("Request not found")
            await self._session.commit()
            return result
        except IntegrityError:
            await self._session.rollback()
            raise ConflictException("Callback request conflicts with existing data")

    async def enqueue_request(self, request_in: CallbackRequestCreate) -> AsyncTask:
        if not settings.SQS_QUEUE_URL:
            raise AppException("SQS queue is not configured", status_code=503)

        payload_dict = jsonable_encoder(request_in.model_dump())
        task = AsyncTask(status=TaskStatus.PENDING, payload=json.dumps(payload_dict))
        self._session.add(task)
        await self._session.commit()

        message_body = json.dumps({"task_id": str(task.id), "data": payload_dict})
        await asyncio.to_thread(
            sqs_client.send_message,
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=message_body,
        )
        return task

    async def get_task_status(self, task_id: uuid.UUID) -> AsyncTask:
        result = await self._session.execute(
            select(AsyncTask).where(AsyncTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundException("Task not found")
        return task