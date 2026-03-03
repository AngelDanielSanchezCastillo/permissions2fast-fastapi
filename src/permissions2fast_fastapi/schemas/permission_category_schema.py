from sqlmodel import SQLModel

class PermissionCategoryBase(SQLModel):
    name: str

class PermissionCategoryCreate(PermissionCategoryBase):
    pass

class PermissionCategoryRead(PermissionCategoryBase):
    id: int
