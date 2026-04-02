"""Utilities for permissions2fast-fastapi"""

from .permission_cache import (
    cache_user_permissions,
    get_user_permissions,
    invalidate_user_cache,
    get_redis_client,
    close_redis_client,
    check_route_access,
)

__all__ = [
    "cache_user_permissions",
    "get_user_permissions",
    "invalidate_user_cache",
    "get_redis_client",
    "close_redis_client",
    "check_route_access",
]
