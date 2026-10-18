import secrets
import uuid

from app.core.security import (
    create_access_token as issue_access_token,
)
from app.core.security import (
    get_password_hash as hash_password,
)
from app.core.security import (
    verify_password as check_password,
)


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return check_password(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def create_access_token(subject: uuid.UUID | str) -> str:
        return issue_access_token(subject)

    @staticmethod
    def create_refresh_token(session_id: uuid.UUID) -> tuple[str, str]:
        secret = secrets.token_urlsafe(32)
        token = f"{session_id}.{secret}"
        return token, hash_password(secret)

    @staticmethod
    def verify_refresh_token(secret: str, token_hash: str) -> bool:
        return check_password(secret, token_hash)
