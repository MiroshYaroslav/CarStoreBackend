from app.models.callback_request import CallbackRequest
from app.repositories.base import BaseRepository


class CallbackRequestRepository(BaseRepository[CallbackRequest]):
    _model = CallbackRequest
