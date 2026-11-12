from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings

redis_pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
    socket_timeout=2.0,
)

def get_redis_client() -> Redis:
    return Redis(connection_pool=redis_pool)