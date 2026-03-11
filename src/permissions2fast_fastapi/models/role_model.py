from sqlmodel import BigInteger, Column, Field, SQLModel, Relationship
from typing import List
from oauth2fast_fastapi.models import AuthModel
from .user_role_model import UserRole


class Role(AuthModel, table=True):
    """
    Role definition for RBAC.
    Description: Role model
    """

    __tablename__ = "roles"

    name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)

    # Relación Many-to-Many hacia User a través de UserRol
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)

