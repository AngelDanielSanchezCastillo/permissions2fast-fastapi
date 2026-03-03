from sqlmodel import Field, SQLModel
from oauth2fast_fastapi.models import AuthModel

class PermissionAssignment(AuthModel, table=True):
    """
    Polymorphic Permission Assignment for RBAC.
    Description: Assigns a permission directly to an entity (e.g. User or Role).
    """
    __tablename__ = "permission_assignments"

    permission_id: int = Field(primary_key=True, foreign_key="permissions.id")
    entity_type: str = Field(primary_key=True, index=True) # e.g., "User", "Team"
    entity_id: int = Field(primary_key=True, index=True)
