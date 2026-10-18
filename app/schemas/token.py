from app.schemas.base import BasePydanticModel
from app.schemas.user import UserRead


class Token(BasePydanticModel):
    access_token: str
    token_type: str
    user: UserRead


class AccessToken(BasePydanticModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BasePydanticModel):
    sub: str | None = None
