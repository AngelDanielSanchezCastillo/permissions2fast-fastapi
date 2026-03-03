from datetime import datetime
from sqlmodel import SQLModel


class PermissionBase(SQLModel):
    name: str
    permission_category_id: int


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(SQLModel):
    name: str | None = None
    permission_category_id: int | None = None


class PermissionRead(PermissionBase):
    id: int

# Assignment Schemas

class PermissionRouteCreate(SQLModel):
    permission_id: int
    route_id: int

class UserPermissionCreate(SQLModel):
    user_id: int
    permission_id: int

class UserPermissionRead(SQLModel):
    permission_id: int
    entity_type: str
    entity_id: int
