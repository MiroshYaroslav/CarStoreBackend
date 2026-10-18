import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.base import ConflictException, NotFoundException
from app.repositories.callback_request_repository import CallbackRequestRepository
from app.schemas.callback_request import CallbackRequestCreate, CallbackRequestUpdate
from app.services.base import BaseService


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
