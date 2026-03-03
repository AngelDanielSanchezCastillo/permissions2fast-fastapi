"""Schemas for permissions2fast-fastapi"""

from .role_schema import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleRead,
    RolePermissionCreate,
    UserRoleCreate,
    UserRoleRead,
)
from .permission_schema import (
    PermissionBase,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    PermissionRouteCreate,
    UserPermissionCreate,
    UserPermissionRead,
)
from .permission_category_schema import (
    PermissionCategoryBase,
    PermissionCategoryCreate,
    PermissionCategoryRead,
)
from .route_schema import (
    RouteBase,
    RouteCreate,
    RouteRead,
)

__all__ = [
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleRead",
    "RolePermissionCreate",
    "UserRoleCreate",
    "UserRoleRead",
    "PermissionBase",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
    "PermissionRouteCreate",
    "UserPermissionCreate",
    "UserPermissionRead",
    "PermissionCategoryBase",
    "PermissionCategoryCreate",
    "PermissionCategoryRead",
    "RouteBase",
    "RouteCreate",
    "RouteRead",
]
