from sqlmodel import Field, SQLModel, UniqueConstraint
from oauth2fast_fastapi.models import AuthModel

class PermissionAssignment(AuthModel, table=True):
    """
    Polymorphic Permission Assignment for RBAC.
    Description: Assigns a permission directly to an entity (e.g. User or Role).
    """
    __tablename__ = "permission_assignments"

    permission_id: int = Field(foreign_key="permissions.id", index=True)
    entity_type: str = Field(index=True) # e.g., "User", "Team"
    entity_id: int = Field(index=True)

    __table_args__ = (
        UniqueConstraint("permission_id", "entity_type", "entity_id", name="uq_permission_assignment"),
    )
