from sqlalchemy import Index
from sqlmodel import BigInteger, Column, Field, ForeignKey

from oauth2fast_fastapi.models import AuthModel


class UserRole(AuthModel, table=True):
    """
    Many-to-many relationship between Users and Roles.
    A user can have multiple roles.
    """

    __tablename__ = "user_roles"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"))
    )
    role_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"))
    )

    # Ensure a user can't have the same role twice
    __table_args__ = (Index("ix_user_role", "user_id", "role_id", unique=True),)
