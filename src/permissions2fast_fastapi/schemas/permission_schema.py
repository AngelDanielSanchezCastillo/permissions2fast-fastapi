from datetime import datetime

from sqlmodel import SQLModel


class PermissionBase(SQLModel):
    user_id: int
    route_path: str
    method: str = "*"
    is_allowed: bool = True
    expires_at: datetime | None = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(SQLModel):
    route_path: str | None = None
    method: str | None = None
    is_allowed: bool | None = None
    expires_at: datetime | None = None


class PermissionRead(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
