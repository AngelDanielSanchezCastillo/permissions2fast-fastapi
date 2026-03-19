from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, List
from oauth2fast_fastapi.models import AuthModel
from .permission_route_model import PermissionRoute

if TYPE_CHECKING:
    from .permission_category_model import PermissionCategory
    from .route_model import Route


class Permission(AuthModel, table=True):
    """
    Permission definition for RBAC.
    Description: Represents a specific action or access right.
    """

    __tablename__ = "permissions"

    name: str = Field(index=True, unique=True)
    permission_category_id: int = Field(foreign_key="permission_categories.id")

    # Many-to-One: un permiso pertenece a una categoría
    category: "PermissionCategory" = Relationship(back_populates="permissions")

    # Many-to-Many hacia Route a través de PermissionRoute (link model)
    routes: List["Route"] = Relationship(back_populates="permissions", link_model=PermissionRoute)
