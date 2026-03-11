from sqlmodel import Field, SQLModel
from oauth2fast_fastapi.models import AuthModel


class UserTenantRole(AuthModel, table=True):
    """
    Tenant-specific Role mapping for RBAC.
    Description: Maps users to roles within a specific tenant context.
    """
    __tablename__ = "user_tenant_roles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="users.id")
    tenant_id: int = Field(foreign_key="tenants.id", index=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
