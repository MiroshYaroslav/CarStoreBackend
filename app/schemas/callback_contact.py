from app.schemas.base import BasePydanticModel


class CallbackContactRead(BasePydanticModel):
    id: int
    number: str
    description: str
