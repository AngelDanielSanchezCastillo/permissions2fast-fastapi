"""
Permission Management Router

Endpoints for managing permissions, categories, and assignments.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from tools2fast_fastapi import APIResponse

from rbac2fast_core.schemas.permission_schema import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    UserPermissionCreate,
    PermissionRouteCreate
)
from rbac2fast_core.schemas.permission_category_schema import (
    PermissionCategoryCreate,
    PermissionCategoryRead
)
from ..services import permission_service
from oauth2fast_fastapi.dependencies import get_auth_session
from ..dependencies import has_permission
from ..schemas.response_schemas import (
    PermissionCreatedResponse,
    PermissionListResponse,
    PermissionSingleResponse,
    PermissionErrorResponse,
    PermissionCategoryCreatedResponse,
    PermissionCategoryListResponse,
    PermissionCategoryErrorResponse,
    PermissionResponse,
    PermissionCategoryResponse,
    UserPermissionCreatedResponse,
    UserPermissionErrorResponse,
    UserPermissionResponse,
    PermissionRouteSuccessResponse,
    PermissionRouteErrorResponse,
    DeleteSuccessResponse,
    DeleteErrorResponse,
)

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    dependencies=[Depends(has_permission())],
)


# Categories


@router.post(
    "/categories",
    response_model=PermissionCategoryCreatedResponse,
    responses={400: {"model": PermissionCategoryErrorResponse}},
)
async def create_category(
    category_data: PermissionCategoryCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | PermissionCategoryCreatedResponse:
    """Create a new permission category."""
    try:
        category = await permission_service.create_category(category_data, session)
        return PermissionCategoryCreatedResponse(
            category=PermissionCategoryResponse(
                id=category.id,
                name=category.name,
            )
        )
    except ValueError as e:
        error_resp, http_status = APIResponse.fail(
            message=str(e),
            status_code=400,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())


@router.get(
    "/categories",
    response_model=PermissionCategoryListResponse,
)
async def list_categories(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
) -> PermissionCategoryListResponse:
    """List all categories."""
    categories = await permission_service.list_categories(session, skip, limit)
    return PermissionCategoryListResponse(
        categories=[
            PermissionCategoryResponse(id=c.id, name=c.name) for c in categories
        ],
        count=len(categories),
    )


# Permissions CRUD


@router.post(
    "/",
    response_model=PermissionCreatedResponse,
    responses={400: {"model": PermissionErrorResponse}},
)
async def create_permission(
    permission_data: PermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | PermissionCreatedResponse:
    """Create a new permission."""
    try:
        permission = await permission_service.create_permission(
            permission_data, session
        )
        return PermissionCreatedResponse(
            permission=PermissionResponse(
                id=permission.id,
                name=permission.name,
                permission_category_id=permission.permission_category_id,
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
    response_model=PermissionListResponse,
)
async def list_permissions(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
) -> PermissionListResponse:
    """List all permissions."""
    permissions = await permission_service.list_permissions(session, skip, limit)
    return PermissionListResponse(
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                permission_category_id=p.permission_category_id,
            )
            for p in permissions
        ],
        count=len(permissions),
    )


@router.get(
    "/{permission_id}",
    response_model=PermissionSingleResponse,
    responses={404: {"model": PermissionErrorResponse}},
)
async def get_permission(
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | PermissionSingleResponse:
    """Get permission by ID."""
    permission = await permission_service.get_permission(permission_id, session)
    if not permission:
        error_resp, http_status = APIResponse.fail(
            message="Permission not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return PermissionSingleResponse(
        permission=PermissionResponse(
            id=permission.id,
            name=permission.name,
            permission_category_id=permission.permission_category_id,
        )
    )


@router.put(
    "/{permission_id}",
    response_model=PermissionSingleResponse,
    responses={404: {"model": PermissionErrorResponse}},
)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | PermissionSingleResponse:
    """Update a permission."""
    permission = await permission_service.update_permission(
        permission_id, permission_data, session
    )
    if not permission:
        error_resp, http_status = APIResponse.fail(
            message="Permission not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return PermissionSingleResponse(
        permission=PermissionResponse(
            id=permission.id,
            name=permission.name,
            permission_category_id=permission.permission_category_id,
        )
    )


@router.delete(
    "/{permission_id}",
    response_model=DeleteSuccessResponse,
    responses={404: {"model": DeleteErrorResponse}},
)
async def delete_permission(
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | DeleteSuccessResponse:
    """Delete a permission."""
    success = await permission_service.delete_permission(permission_id, session)
    if not success:
        error_resp, http_status = APIResponse.fail(
            message="Permission not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return DeleteSuccessResponse()


# Permission Routes (Link)


@router.post(
    "/{permission_id}/routes",
    response_model=PermissionRouteSuccessResponse,
    responses={400: {"model": PermissionRouteErrorResponse}},
)
async def add_permission_route(
    permission_id: int,
    route_data: PermissionRouteCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | PermissionRouteSuccessResponse:
    """Link a permission to a route."""
    # Ensure permission_id matches URL
    if route_data.permission_id != permission_id:
         route_data.permission_id = permission_id

    try:
        await permission_service.add_permission_route(
            permission_id, route_data.route_id, session
        )
        return PermissionRouteSuccessResponse()
    except ValueError as e:
        error_resp, http_status = APIResponse.fail(
            message=str(e),
            status_code=400,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())


# User Permissions (Direct Assignment)


@router.post(
    "/assign",
    response_model=UserPermissionCreatedResponse,
    responses={400: {"model": UserPermissionErrorResponse}},
)
async def assign_user_permission(
    assignment_data: UserPermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | UserPermissionCreatedResponse:
    """Assign a permission directly to a user."""
    try:
        user_perm = await permission_service.assign_user_permission(
            assignment_data.user_id, assignment_data.permission_id, session
        )
        return UserPermissionCreatedResponse(
            user_permission=UserPermissionResponse(
                permission_id=user_perm.permission_id,
                entity_type=user_perm.entity_type,
                entity_id=user_perm.entity_id,
            )
        )
    except ValueError as e:
        error_resp, http_status = APIResponse.fail(
            message=str(e),
            status_code=400,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())


@router.get(
    "/user/{user_id}",
    response_model=PermissionListResponse,
)
async def list_user_permissions(
    user_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> PermissionListResponse:
    """List all permissions assigned directly to a user."""
    permissions = await permission_service.list_user_permissions(user_id, session)
    return PermissionListResponse(
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                permission_category_id=p.permission_category_id,
            )
            for p in permissions
        ],
        count=len(permissions),
    )


@router.delete(
    "/user/{user_id}/permission/{permission_id}",
    response_model=DeleteSuccessResponse,
    responses={404: {"model": DeleteErrorResponse}},
)
async def remove_user_permission(
    user_id: int,
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | DeleteSuccessResponse:
    """Remove a direct permission from a user."""
    success = await permission_service.remove_user_permission(user_id, permission_id, session)
    if not success:
        error_resp, http_status = APIResponse.fail(
            message="User permission assignment not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return DeleteSuccessResponse()
