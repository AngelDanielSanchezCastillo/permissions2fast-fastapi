from sqlmodel import Field, SQLModel
from oauth2fast_fastapi.models import AuthModel


class Tenant(AuthModel, table=True):
    """
    Tenant definition for Multi-tenant RBAC.
    Description: Represents an isolated organization or tenant.
    """
    __tablename__ = "tenants"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    schema_name: str | None = Field(default=None, description="DB Schema name if applicable")
    db_url: str | None = Field(default=None, description="External DB URL if applicable")
    is_active: bool = Field(default=True)
