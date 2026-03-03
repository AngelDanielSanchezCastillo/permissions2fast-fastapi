from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from oauth2fast_fastapi.models import AuthModel

class Permission(AuthModel, table=True):
    """
    Permission definition for RBAC.
    Description: Represents a specific action or access right.
    """
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    permission_category_id: int = Field(foreign_key="permission_categories.id")
    
    # Relationships
    # category: "PermissionCategory" = Relationship(back_populates="permissions")
