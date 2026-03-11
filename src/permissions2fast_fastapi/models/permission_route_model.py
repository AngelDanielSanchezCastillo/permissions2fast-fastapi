from sqlmodel import Field, SQLModel, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel

class PermissionRoute(AuthModel, table=True):
    """
    Permission Route mapping for RBAC.
    Description: Maps permissions to specific API routes.
    """
    __tablename__ = "permission_routes"

    id: int | None = Field(default=None, primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id")
    route_id: int = Field(foreign_key="routes.id")

