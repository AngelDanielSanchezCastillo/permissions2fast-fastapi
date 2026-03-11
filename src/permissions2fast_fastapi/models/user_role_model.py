from sqlmodel import Field, SQLModel, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel

class UserRole(AuthModel, table=True):
    """
    User Role mapping for RBAC.
    Description: Maps users to their assigned roles.
    """
    __tablename__ = "user_role"

    role_id: int = Field(primary_key=True, foreign_key="roles.id")
    user_id: int = Field(primary_key=True, index=True, foreign_key="users.id")
