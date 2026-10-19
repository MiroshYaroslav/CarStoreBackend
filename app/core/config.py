from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    PROJECT_NAME: str = "BMW Catalog API"
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, gt=0)
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    AWS_BUCKET_NAME: str | None = None
    AWS_REGION: str | None = None
    AWS_CLOUDFRONT_DOMAIN: str | None = None
    PRODUCT_IMAGE_UPLOAD_ALLOWED_USER_IDS: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @property
    def DATABASE_URL(self) -> str:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=int(self.POSTGRES_PORT),
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)


settings = Settings()
