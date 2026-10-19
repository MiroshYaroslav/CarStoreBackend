from app.models.callback_contact import CallbackContact
from app.repositories.base import BaseRepository


class CallbackContactRepository(BaseRepository[CallbackContact]):
    _model = CallbackContact
