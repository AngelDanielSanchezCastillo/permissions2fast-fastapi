from sqlmodel import SQLModel

class RouteBase(SQLModel):
    name: str
    is_active: bool = True

class RouteCreate(RouteBase):
    pass

class RouteRead(RouteBase):
    id: int
