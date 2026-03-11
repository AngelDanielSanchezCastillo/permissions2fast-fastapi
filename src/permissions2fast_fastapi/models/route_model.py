from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from oauth2fast_fastapi.models import AuthModel
from .permission_route_model import PermissionRoute

class Route(AuthModel, table=True):
    """
    Route definition for RBAC.
    Description: Represents an API endpoint or accessible resource path.
    """
    __tablename__ = "routes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True) # The path
    is_active: bool = Field(default=True)

    # Relación Many-to-Many hacia Permission a través de PermissionRoute
    #permissions: List["Permission"] = Relationship(back_populates="routes", link_model=PermissionRoute)