from sqlmodel import BigInteger, Column, Field

from oauth2fast_fastapi.models import AuthModel


class Role(AuthModel, table=True):
    """
    Role definition for RBAC.
    Roles can have multiple permissions assigned to them.
    Note: tenant_id will be added by tenant2fast_fastapi module.
    """

    __tablename__ = "roles"

    id: int = Field(
        default=None, sa_column=Column(BigInteger, index=True, primary_key=True)
    )
    name: str = Field(index=True)  # e.g., "Admin", "Editor", "Viewer"
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)

