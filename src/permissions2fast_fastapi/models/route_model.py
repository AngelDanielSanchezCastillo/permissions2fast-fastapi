from uuid import UUID

from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, List
from oauth2fast_fastapi.models import AuthSoftDeleteModel
from .permission_route_model import PermissionRoute

if TYPE_CHECKING:
    from .permission_model import Permission


class Route(AuthSoftDeleteModel, table=True):
    """
    Route definition for RBAC.
    Description: Represents an API endpoint or accessible resource path.
    """

    __tablename__ = "routes"

    name: str = Field(index=True, unique=True)  # The path / route name

    # Many-to-Many hacia Permission a través de PermissionRoute (link model)
    permissions: List["Permission"] = Relationship(back_populates="routes", link_model=PermissionRoute)
