from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List

# Forward reference for relationship
from oauth2fast_fastapi.models import AuthModel

class PermissionCategory(AuthModel, table=True):
    """
    Permission Category definition for RBAC.
    Description: Groups related permissions together.
    """
    __tablename__ = "permission_categories"

    name: str = Field(index=True, unique=True)
    
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    #permissions: List["Permission"] = Relationship(back_populates="category")
