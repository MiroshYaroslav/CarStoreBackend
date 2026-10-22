from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import DBSession
from app.repositories.callback_contact_repository import CallbackContactRepository
from app.schemas.callback_contact import CallbackContactRead
from app.services.callback_contact_service import CallbackContactService

router = APIRouter()


def get_callback_contact_repo(session: DBSession) -> CallbackContactRepository:
    return CallbackContactRepository(session)


CallbackContactRepoDep = Annotated[CallbackContactRepository, Depends(get_callback_contact_repo)]


def get_callback_contact_service(
    session: DBSession, repo: CallbackContactRepoDep
) -> CallbackContactService:
    return CallbackContactService(session, repo)


CallbackContactServiceDep = Annotated[CallbackContactService, Depends(get_callback_contact_service)]


@router.get("/", response_model=list[CallbackContactRead])
async def get_callback_contacts(service: CallbackContactServiceDep):
    return await service.list_contacts()
