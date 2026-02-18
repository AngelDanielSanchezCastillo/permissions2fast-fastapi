"""Schemas for permissions2fast-fastapi"""

from .role_schema import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RolePermissionBase,
    RolePermissionCreate,
    RolePermissionRead,
    UserRoleCreate,
    UserRoleRead,
)
from .permission_schema import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)

__all__ = [
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "RolePermissionBase",
    "RolePermissionCreate",
    "RolePermissionRead",
    "UserRoleCreate",
    "UserRoleRead",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
]
