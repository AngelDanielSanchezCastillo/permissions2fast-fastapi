from sqlmodel import BigInteger, Column, Field

from oauth2fast_fastapi.models import AuthModel


class RoleLevel(AuthModel, table=True):
    __tablename__ = "role_levels"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
