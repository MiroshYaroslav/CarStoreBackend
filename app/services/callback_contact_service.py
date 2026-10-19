from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.callback_contact_repository import CallbackContactRepository
from app.services.base import BaseService


class CallbackContactService(BaseService):
    def __init__(self, session: AsyncSession, repository: CallbackContactRepository):
        super().__init__(session)
        self._repository = repository

    async def list_contacts(self):
        return await self._repository.get_many()
