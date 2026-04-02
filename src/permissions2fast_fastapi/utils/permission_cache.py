"""
Permission Cache Utility

This module provides Redis caching for user permissions.
Caching permissions significantly improves performance by avoiding database queries on every request.
"""

import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from ..settings import settings

# Global Redis client
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client.

    Returns:
        Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        # Build Redis URL from settings
        password_part = f":{settings.redis.password.get_secret_value()}@" if settings.redis.password else ""
        redis_url = f"redis://{password_part}{settings.redis.host}:{settings.redis.port}/{settings.redis.db}"
        
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=settings.redis.decode_responses,
        )

    return _redis_client


async def close_redis_client():
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


def _permission_key(user_id: int) -> str:
    """Generate Redis key for user permissions."""
    return f"user_permissions:{user_id}"


async def cache_user_permissions(
    user_id: int, permissions: list[dict[str, Any]], ttl: int | None = None
):
    """
    Cache user permissions in Redis.

    Args:
        user_id: User's ID
        permissions: List of permission dictionaries
        ttl: Time to live in seconds (default: from settings)
    """
    client = await get_redis_client()
    key = _permission_key(user_id)
    ttl = ttl or 300  # Default 5 minutes

    # Store as JSON
    await client.setex(
        key,
        ttl,
        json.dumps(permissions, default=str),  # default=str handles datetime
    )


async def get_user_permissions(user_id: int) -> list[dict[str, Any]] | None:
    """
    Retrieve user permissions from cache.

    Args:
        user_id: User's ID

    Returns:
        List of permissions or None if not cached
    """
    client = await get_redis_client()
    key = _permission_key(user_id)

    cached = await client.get(key)
    if cached:
        return json.loads(cached)

    return None


async def invalidate_user_cache(user_id: int):
    """
    Clear user's cached permissions.
    Call this when user permissions change.

    Args:
        user_id: User's ID
    """
    client = await get_redis_client()
    await client.delete(_permission_key(user_id))


async def check_route_access(
    user_id: int, route_path: str, method: str = "GET"
) -> bool | None:
    """
    Fast permission check using cached data.

    Args:
        user_id: User's ID
        route_path: Route path to check
        method: HTTP method

    Returns:
        True if allowed, False if denied, None if not in cache
    """
    permissions = await get_user_permissions(user_id)

    if permissions is None:
        return None

    # Check for exact match or wildcard
    for perm in permissions:
        if perm["route_path"] == route_path:
            if perm["method"] in (method, "*"):
                # Check expiration if present
                if perm.get("expires_at"):
                    expires = datetime.fromisoformat(perm["expires_at"])
                    if datetime.utcnow() > expires:
                        continue

                return perm["is_allowed"]

    # No specific permission found
    return None
