"""
Route Management Router

Endpoints for managing routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.route_schema import (
    RouteCreate,
    RouteRead,
)
from ..services import route_service
from oauth2fast_fastapi.dependencies import get_auth_session

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
)


@router.post("/", response_model=RouteRead)
async def create_route(
    route_data: RouteCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Create a new route."""
    try:
        route = await route_service.create_route(route_data, session)
        return RouteRead.model_validate(route)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[RouteRead])
async def list_routes(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
):
    """List all routes."""
    routes = await route_service.list_routes(session, skip, limit)
    return [RouteRead.model_validate(r) for r in routes]
