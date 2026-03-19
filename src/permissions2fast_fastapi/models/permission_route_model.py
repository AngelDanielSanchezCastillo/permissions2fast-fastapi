from sqlmodel import Field, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel


class PermissionRoute(AuthModel, table=True):
    """
    Permission Route mapping for RBAC.
    Description: Link table that maps permissions to specific API routes.
    """

    __tablename__ = "permission_routes"
    __table_args__ = (
        UniqueConstraint("permission_id", "route_id", name="uq_permission_route"),
    )

    permission_id: int = Field(foreign_key="permissions.id", index=True)
    route_id: int = Field(foreign_key="routes.id", index=True)
