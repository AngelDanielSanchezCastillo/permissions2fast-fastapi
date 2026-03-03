from sqlmodel import Field, SQLModel
from typing import Optional
from oauth2fast_fastapi.models import AuthModel

class Route(AuthModel, table=True):
    """
    Route definition for RBAC.
    Description: Represents an API endpoint or accessible resource path.
    """
    __tablename__ = "routes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True) # The path
    is_active: bool = Field(default=True)
