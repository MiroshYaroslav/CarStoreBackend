from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=30,
    max_overflow=20,
    pool_timeout=15,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionMaker = async_sessionmaker(
    bind=engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False
)