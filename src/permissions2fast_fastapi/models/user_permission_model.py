from datetime import datetime

from sqlalchemy import Index
from sqlmodel import BigInteger, Column, Field, ForeignKey

from oauth2fast_fastapi.models import AuthModel


# User-specific route permissions (beyond role-based permissions)
# This allows fine-grained control: grant/deny specific routes to individual users
class UserPermission(AuthModel, table=True):
    __tablename__ = "user_permissions"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    )
    route_path: str = Field(index=True)  # e.g., "/api/v1/reports"
    method: str = Field(
        default="*"
    )  # HTTP method: GET, POST, PUT, DELETE, or * for all
    is_allowed: bool = Field(
        default=True
    )  # True to grant access, False to explicitly deny
    expires_at: datetime | None = Field(
        default=None
    )  # Optional expiration for temporary access

    # Create composite index for faster lookups
    __table_args__ = (
        Index("ix_user_route_method", "user_id", "route_path", "method", unique=True),
    )
