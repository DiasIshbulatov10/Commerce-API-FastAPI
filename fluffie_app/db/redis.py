from redis.asyncio import Redis as AioRedis

from ..core.config import settings

redis_async_conn = AioRedis.from_url(settings.redis_uri)
