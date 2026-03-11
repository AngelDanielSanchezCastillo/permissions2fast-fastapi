from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from oauth2fast_fastapi.models import AuthModel
from .permission_route_model import PermissionRoute

class Permission(AuthModel, table=True):
    """
    Permission definition for RBAC.
    Description: Represents a specific action or access right.
    """
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    permission_category_id: int = Field(foreign_key="permission_categories.id")
    
    # Relación Many-to-Many hacia Route a través de PermissionRoute
    #routes: List["Route"] = Relationship(back_populates="permissions", link_model=PermissionRoute)

