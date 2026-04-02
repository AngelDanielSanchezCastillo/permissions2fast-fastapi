from datetime import datetime
from sqlmodel import SQLModel


class RoleBase(SQLModel):
    name: str
    description: str | None = None
    is_active: bool = True


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RoleRead(RoleBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Assignment Schemas

class RolePermissionCreate(SQLModel):
    permission_id: int


class UserRoleCreate(SQLModel):
    user_id: int
    role_id: int


class UserRoleRead(SQLModel):
    user_id: int
    role_id: int
