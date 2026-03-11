from sqlmodel import Field, SQLModel, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel

class PermissionRoute(AuthModel, table=True):
    """
    Permission Route mapping for RBAC.
    Description: Maps permissions to specific API routes.
    """
    __tablename__ = "permission_routes"

    permission_id: int = Field(foreign_key="permissions.id")
    route_id: int = Field(foreign_key="routes.id")

    __table_args__ = (
        UniqueConstraint("permission_id", "route_id", name="uq_permission_route"),
    )