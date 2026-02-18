from datetime import datetime

from sqlmodel import SQLModel


class RoleBase(SQLModel):
    name: str
    description: str | None = None
    is_active: bool = True


class RoleCreate(RoleBase):
    """Create a new role. Note: tenant_id will be added by tenant2fast_fastapi."""
    pass


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RoleRead(RoleBase):
    """Role read schema. Note: tenant_id will be added by tenant2fast_fastapi."""
    id: int
    created_at: datetime
    updated_at: datetime



class RolePermissionBase(SQLModel):
    route_path: str
    method: str = "*"
    is_allowed: bool = True
    expires_at: datetime | None = None


class RolePermissionCreate(RolePermissionBase):
    role_id: int


class RolePermissionRead(RolePermissionBase):
    id: int
    role_id: int
    created_at: datetime
    updated_at: datetime


class UserRoleCreate(SQLModel):
    user_id: int
    role_id: int


class UserRoleRead(SQLModel):
    id: int
    user_id: int
    role_id: int
    created_at: datetime
    updated_at: datetime
