import json
from typing import Any

from redis.asyncio import Redis

from ..settings import settings

# Global redis pool
_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """Get or initialize the Redis client from settings."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password.get_secret_value() if settings.redis.password else None,
            decode_responses=settings.redis.decode_responses,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose() # type: ignore
        _redis_client = None


async def get_cached_permissions(user_id: int, tenant_id: int | str | None) -> list[str] | None:
    """Get cached permissions for a user within a tenant context."""
    if not settings.redis_rbac_enabled:
        return None
        
    client = get_redis_client()
    tenant_part = str(tenant_id) if tenant_id is not None else "global"
    key = f"rbac:{user_id}:{tenant_part}"
    
    data = await client.get(key)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    return None


async def set_cached_permissions(user_id: int, tenant_id: int | str | None, permissions: list[str]) -> None:
    """Set cached permissions for a user within a tenant context."""
    if not settings.redis_rbac_enabled:
        return
        
    client = get_redis_client()
    tenant_part = str(tenant_id) if tenant_id is not None else "global"
    key = f"rbac:{user_id}:{tenant_part}"
    
    await client.setex(
        key,
        settings.cache_ttl_seconds,
        json.dumps(permissions)
    )


async def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cached permissions for a specific user across all tenants."""
    if not settings.redis_rbac_enabled:
        return
        
    client = get_redis_client()
    # Find all keys for this user
    pattern = f"rbac:{user_id}:*"
    
    # Use scan to avoid blocking Redis with keys() on large datasets
    cursor = b'0'
    while cursor:
        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            await client.delete(*keys)
