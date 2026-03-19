from sqlmodel import Field, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel


class UserRole(AuthModel, table=True):
    """
    User Role mapping for RBAC.
    Description: Link table that maps users to their assigned roles.
    """

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user_id: int = Field(index=True, foreign_key="users.id")
    role_id: int = Field(index=True, foreign_key="roles.id")
