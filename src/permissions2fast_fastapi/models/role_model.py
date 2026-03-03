from sqlmodel import BigInteger, Column, Field
from sqlmodel import BigInteger, Column, Field, SQLModel

from oauth2fast_fastapi.models import AuthModel


class Role(AuthModel, table=True):
    """
    Role definition for RBAC.
    Description: Role model
    """

    __tablename__ = "roles"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)

