"""Routers for permissions2fast-fastapi"""

from .roles_router import router as roles_router
from .permissions_router import router as permissions_router

__all__ = [
    "roles_router",
    "permissions_router",
]
