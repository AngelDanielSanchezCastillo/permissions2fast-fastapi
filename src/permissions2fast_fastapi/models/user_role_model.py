from sqlmodel import Field, SQLModel, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel

class UserRole(AuthModel, table=True):
    """
    User Role mapping for RBAC.
    Description: Maps users to their assigned roles.
    """
    __tablename__ = "user_role"

    role_id: int = Field(foreign_key="roles.id", index=True)
    user_id: int = Field(index=True, foreign_key="users.id")

    __table_args__ = (
        UniqueConstraint("role_id", "user_id", name="uq_user_role"),
    )
