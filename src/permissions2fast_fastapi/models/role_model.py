from sqlmodel import Field
from oauth2fast_fastapi.models import AuthModel


class Role(AuthModel, table=True):
    """
    Role definition for RBAC.
    Description: Role model
    """

    __tablename__ = "roles"

    name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)

    # Nota: la relación Many-to-Many con User se hace a través de UserRole,
    # pero NO se puede declarar Relationship aquí porque oauth2fast_fastapi.User
    # es un modelo externo sin back_populates="roles". Para consultar usuarios
    # de un rol usa: select(User).join(UserRole).where(UserRole.role_id == role.id)
