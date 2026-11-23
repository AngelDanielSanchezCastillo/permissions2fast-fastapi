"""
Response schemas for permissions2fast API endpoints.

These schemas provide unified API response format with success/error patterns.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from tools2fast_fastapi import ErrorDetail


# ============ Permission Responses ============

class PermissionResponse(BaseModel):
    """Response for permission data."""
    id: UUID
    name: str
    permission_category_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None


class PermissionCreatedResponse(BaseModel):
    """Successful permission creation response."""
    success: Literal[True] = True
    message: str = "Permiso creado exitosamente"
    permission: PermissionResponse


class PermissionListResponse(BaseModel):
    """Successful permission list response."""
    success: Literal[True] = True
    message: str = "Éxito"
    permissions: list[PermissionResponse]
    count: int


class PermissionSingleResponse(BaseModel):
    """Successful single permission response."""
    success: Literal[True] = True
    message: str = "Éxito"
    permission: PermissionResponse


class PermissionErrorResponse(BaseModel):
    """Error response for permission operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


class PermissionUnexpectedErrorResponse(BaseModel):
    """Unexpected error response for permission operations."""
    success: Literal[False] = False
    error_type: Literal["unexpected"] = "unexpected"
    message: str = "Ha ocurrido un error"
    error: ErrorDetail | None = None


# ============ Permission Category Responses ============

class PermissionCategoryResponse(BaseModel):
    """Response for permission category data."""
    id: UUID
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None


class PermissionCategoryCreatedResponse(BaseModel):
    """Successful permission category creation response."""
    success: Literal[True] = True
    message: str = "Categoría creada exitosamente"
    category: PermissionCategoryResponse


class PermissionCategoryListResponse(BaseModel):
    """Successful permission category list response."""
    success: Literal[True] = True
    message: str = "Éxito"
    categories: list[PermissionCategoryResponse]
    count: int


class PermissionCategoryErrorResponse(BaseModel):
    """Error response for permission category operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ User Permission Responses ============

class UserPermissionResponse(BaseModel):
    """Response for user permission assignment data."""
    permission_id: UUID
    entity_type: str
    entity_id: UUID


class UserPermissionCreatedResponse(BaseModel):
    """Successful user permission assignment response."""
    success: Literal[True] = True
    message: str = "Permiso asignado exitosamente"
    user_permission: UserPermissionResponse


class UserPermissionErrorResponse(BaseModel):
    """Error response for user permission operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ Permission Route Responses ============

class PermissionRouteSuccessResponse(BaseModel):
    """Successful permission-route link response."""
    success: Literal[True] = True
    message: str = "Ruta vinculada al permiso exitosamente"


class PermissionRouteErrorResponse(BaseModel):
    """Error response for permission-route operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ Role Responses ============

class RoleResponse(BaseModel):
    """Response for role data."""
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None


class RoleCreatedResponse(BaseModel):
    """Successful role creation response."""
    success: Literal[True] = True
    message: str = "Rol creado exitosamente"
    role: RoleResponse


class RoleListResponse(BaseModel):
    """Successful role list response."""
    success: Literal[True] = True
    message: str = "Éxito"
    roles: list[RoleResponse]
    count: int


class RoleSingleResponse(BaseModel):
    """Successful single role response."""
    success: Literal[True] = True
    message: str = "Éxito"
    role: RoleResponse


class RoleErrorResponse(BaseModel):
    """Error response for role operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


class RoleUnexpectedErrorResponse(BaseModel):
    """Unexpected error response for role operations."""
    success: Literal[False] = False
    error_type: Literal["unexpected"] = "unexpected"
    message: str = "Ha ocurrido un error"
    error: ErrorDetail | None = None


# ============ User Role Responses ============

class RoleUserResponse(BaseModel):
    """Response for user role assignment data."""
    user_id: UUID
    role_id: UUID


class RoleUserCreatedResponse(BaseModel):
    """Successful user role assignment response."""
    success: Literal[True] = True
    message: str = "Rol asignado exitosamente"
    user_role: RoleUserResponse


class RoleUserErrorResponse(BaseModel):
    """Error response for user role operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ Role Permission Responses ============

class RolePermissionSuccessResponse(BaseModel):
    """Successful role-permission link response."""
    success: Literal[True] = True
    message: str = "Permiso añadido al rol exitosamente"


class RolePermissionErrorResponse(BaseModel):
    """Error response for role-permission operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ Route Responses ============

class RouteResponse(BaseModel):
    """Response for route data."""
    id: UUID
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None


class RouteCreatedResponse(BaseModel):
    """Successful route creation response."""
    success: Literal[True] = True
    message: str = "Ruta creada exitosamente"
    route: RouteResponse


class RouteListResponse(BaseModel):
    """Successful route list response."""
    success: Literal[True] = True
    message: str = "Éxito"
    routes: list[RouteResponse]
    count: int


class RouteErrorResponse(BaseModel):
    """Error response for route operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None


# ============ Delete Responses ============

class DeleteSuccessResponse(BaseModel):
    """Successful deletion response."""
    success: Literal[True] = True
    message: str = "Eliminado exitosamente"


class DeleteErrorResponse(BaseModel):
    """Error response for deletion operations."""
    success: Literal[False] = False
    error_type: Literal["controlled"] = "controlled"
    message: str
    error: ErrorDetail | None = None
