import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

BASE_DIR = Path(__file__).resolve().parent.parent
config_path = BASE_DIR / "config.yml"

if not config_path.exists():
    raise FileNotFoundError(f"Config file not found at {config_path}")

with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

db_conf = config["database"]
DATABASE_URL = (
    f"postgresql+asyncpg://{db_conf['user']}:{db_conf['password']}@"
    f"{db_conf['host']}:{db_conf['port']}/{db_conf['name']}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db
