from datetime import datetime

from sqlalchemy import Index
from sqlmodel import BigInteger, Column, Field, ForeignKey

from oauth2fast_fastapi.models import AuthModel


class RolePermission(AuthModel, table=True):
    """
    Permissions assigned to roles.
    Defines what routes/methods a role can access.
    """

    __tablename__ = "role_permissions"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    role_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"))
    )
    route_path: str = Field(index=True)  # e.g., "/api/v1/users"
    method: str = Field(default="*")  # GET, POST, PUT, DELETE, or *
    is_allowed: bool = Field(default=True)
    expires_at: datetime | None = Field(default=None)

    # Ensure a role can't have duplicate permissions
    __table_args__ = (
        Index("ix_role_route_method", "role_id", "route_path", "method", unique=True),
    )
