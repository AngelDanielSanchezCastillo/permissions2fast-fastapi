"""
Role Management Router

Endpoints for managing roles, role permissions, and user-role assignments.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from tools2fast_fastapi import APIResponse

from rbac2fast_core.schemas.role_schema import (
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RolePermissionCreate,
    UserRoleCreate,
)
from rbac2fast_core.schemas.permission_schema import PermissionRead
from ..services import role_service
from oauth2fast_fastapi.dependencies import get_auth_session

from ..dependencies import has_permission
from ..schemas.response_schemas import (
    RoleCreatedResponse,
    RoleListResponse,
    RoleSingleResponse,
    RoleErrorResponse,
    RoleResponse,
    PermissionListResponse,
    PermissionResponse,
    UserRoleCreatedResponse,
    UserRoleErrorResponse,
    UserRoleResponse,
    RolePermissionSuccessResponse,
    RolePermissionErrorResponse,
    DeleteSuccessResponse,
    DeleteErrorResponse,
)

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
    dependencies=[Depends(has_permission())],
)


# Role CRUD


@router.post(
    "/",
    response_model=RoleCreatedResponse,
    responses={400: {"model": RoleErrorResponse}},
)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | RoleCreatedResponse:
    """Create a new role."""
    try:
        role = await role_service.create_role(role_data, session)
        return RoleCreatedResponse(
            role=RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
                created_at=role.created_at,
                updated_at=role.updated_at,
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
    response_model=RoleListResponse,
)
async def list_roles(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
) -> RoleListResponse:
    """List all roles."""
    roles = await role_service.list_roles(session, skip, limit)
    return RoleListResponse(
        roles=[
            RoleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                is_active=r.is_active,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in roles
        ],
        count=len(roles),
    )


@router.get(
    "/{role_id}",
    response_model=RoleSingleResponse,
    responses={404: {"model": RoleErrorResponse}},
)
async def get_role(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | RoleSingleResponse:
    """Get role by ID."""
    role = await role_service.get_role(role_id, session)
    if not role:
        error_resp, http_status = APIResponse.fail(
            message="Role not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return RoleSingleResponse(
        role=RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )
    )


@router.put(
    "/{role_id}",
    response_model=RoleSingleResponse,
    responses={404: {"model": RoleErrorResponse}},
)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | RoleSingleResponse:
    """Update a role."""
    role = await role_service.update_role(role_id, role_data, session)
    if not role:
        error_resp, http_status = APIResponse.fail(
            message="Role not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return RoleSingleResponse(
        role=RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )
    )


@router.delete(
    "/{role_id}",
    response_model=DeleteSuccessResponse,
    responses={404: {"model": DeleteErrorResponse}},
)
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | DeleteSuccessResponse:
    """Delete a role."""
    success = await role_service.delete_role(role_id, session)
    if not success:
        error_resp, http_status = APIResponse.fail(
            message="Role not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return DeleteSuccessResponse()


# Role Permissions


@router.post(
    "/{role_id}/permissions",
    response_model=RolePermissionSuccessResponse,
    responses={400: {"model": RolePermissionErrorResponse}},
)
async def add_role_permission(
    role_id: int,
    perm_data: RolePermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | RolePermissionSuccessResponse:
    """Add a permission to a role."""
    try:
        await role_service.add_role_permission(role_id, perm_data.permission_id, session)
        return RolePermissionSuccessResponse()
    except ValueError as e:
        error_resp, http_status = APIResponse.fail(
            message=str(e),
            status_code=400,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())


@router.get(
    "/{role_id}/permissions",
    response_model=PermissionListResponse,
)
async def list_role_permissions(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> PermissionListResponse:
    """List all permissions for a role."""
    permissions = await role_service.list_role_permissions(role_id, session)
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
    "/{role_id}/permissions/{permission_id}",
    response_model=DeleteSuccessResponse,
    responses={404: {"model": DeleteErrorResponse}},
)
async def delete_role_permission(
    role_id: int,
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | DeleteSuccessResponse:
    """Delete a role permission."""
    success = await role_service.delete_role_permission(role_id, permission_id, session)
    if not success:
        error_resp, http_status = APIResponse.fail(
            message="Permission assignment not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return DeleteSuccessResponse()


# User Roles


@router.post(
    "/assign",
    response_model=UserRoleCreatedResponse,
    responses={400: {"model": UserRoleErrorResponse}},
)
async def assign_user_role(
    assignment_data: UserRoleCreate,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | UserRoleCreatedResponse:
    """Assign a role to a user."""
    try:
        user_role = await role_service.assign_user_role(
            assignment_data.user_id, assignment_data.role_id, session
        )
        return UserRoleCreatedResponse(
            user_role=UserRoleResponse(
                user_id=user_role.user_id,
                role_id=user_role.role_id,
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
    response_model=RoleListResponse,
)
async def list_user_roles(
    user_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> RoleListResponse:
    """List all roles assigned to a user."""
    roles = await role_service.list_user_roles(user_id, session)
    return RoleListResponse(
        roles=[
            RoleResponse(
                id=r.id,
                name=r.name,
                description=r.description,
                is_active=r.is_active,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in roles
        ],
        count=len(roles),
    )


@router.delete(
    "/user/{user_id}/role/{role_id}",
    response_model=DeleteSuccessResponse,
    responses={404: {"model": DeleteErrorResponse}},
)
async def remove_user_role(
    user_id: int,
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
) -> JSONResponse | DeleteSuccessResponse:
    """Remove a role from a user."""
    success = await role_service.remove_user_role(user_id, role_id, session)
    if not success:
        error_resp, http_status = APIResponse.fail(
            message="User role assignment not found",
            status_code=404,
        )
        return JSONResponse(status_code=http_status, content=error_resp.model_dump())
    return DeleteSuccessResponse()
