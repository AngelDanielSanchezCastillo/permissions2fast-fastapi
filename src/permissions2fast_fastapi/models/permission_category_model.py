from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, List
from oauth2fast_fastapi.models import AuthModel

if TYPE_CHECKING:
    from .permission_model import Permission


class PermissionCategory(AuthModel, table=True):
    """
    Permission Category definition for RBAC.
    Description: Groups related permissions together.
    """

    __tablename__ = "permission_categories"

    name: str = Field(index=True, unique=True)

    # One-to-Many: una categoría tiene muchos permisos
    permissions: List["Permission"] = Relationship(back_populates="category")
