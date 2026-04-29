"""
Route Management Router

Endpoints for managing routes.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from tools2fast_fastapi import APIResponse

from rbac2fast_core.schemas.route_schema import (
    RouteCreate,
    RouteRead,
)
from ..services import route_service
from oauth2fast_fastapi.dependencies import get_auth_session

from ..dependencies import has_permission
from ..schemas.response_schemas import (
    RouteCreatedResponse,
    RouteListResponse,
    RouteResponse,
    RouteErrorResponse,
)

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
    dependencies=[Depends(has_permission())],
)


@router.post(
    "/",
    response_model=RouteCreatedResponse,
    responses={400: {"model": RouteErrorResponse}},
)
async def create_route(
    route_data: RouteCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | RouteCreatedResponse:
    """Create a new route."""
    try:
        route = await route_service.create_route(route_data, session)
        return RouteCreatedResponse(
            route=RouteResponse(
                id=route.id,
                name=route.name,
                is_active=route.is_active,
            )
        )
    except ValueError as e:
        error_resp, http_status = APIResponse.fail(
            message=str(e),
            status_code=400,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())


@router.get(
    "/",
    response_model=RouteListResponse,
)
async def list_routes(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
) -> RouteListResponse:
    """List all routes."""
    routes = await route_service.list_routes(session, skip, limit)
    return RouteListResponse(
        routes=[
            RouteResponse(
                id=r.id,
                name=r.name,
                is_active=r.is_active,
            )
            for r in routes
        ],
        count=len(routes),
    )
