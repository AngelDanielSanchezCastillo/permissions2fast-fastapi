"""
Route Service

Business logic for managing routes.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from ..models.route_model import Route
from rbac2fast_core.schemas.route_schema import RouteCreate

async def create_route(
    route_data: RouteCreate, session: AsyncSession
) -> Route:
    """Create a new route."""
    route = Route(**route_data.model_dump())
    session.add(route)
    try:
        await session.commit()
        await session.refresh(route)
        return route
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Route '{route_data.name}' already exists")

async def list_routes(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Route]:
    """List all routes."""
    result = await session.exec(
        select(Route).offset(skip).limit(limit).order_by(Route.name)
    )
    return list(result.all())

async def get_route_by_path(
    path: str, session: AsyncSession
) -> Route | None:
    """Get route by path name."""
    result = await session.exec(
        select(Route).where(Route.name == path)
    )
    return result.one_or_none()
