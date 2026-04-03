"""
Permission Management Router

Endpoints for managing permissions, categories, and assignments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from ..schemas.permission_schema import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    UserPermissionCreate,
    UserPermissionRead,
    PermissionRouteCreate
)
from ..schemas.permission_category_schema import (
    PermissionCategoryCreate,
    PermissionCategoryRead
)
from ..services import permission_service
from oauth2fast_fastapi.dependencies import get_auth_session

from ..dependencies import has_permission

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    dependencies=[Depends(has_permission())],
)


# Categories


@router.post("/categories", response_model=PermissionCategoryRead)
async def create_category(
    category_data: PermissionCategoryCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Create a new permission category."""
    try:
        category = await permission_service.create_category(category_data, session)
        return PermissionCategoryRead.model_validate(category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories", response_model=list[PermissionCategoryRead])
async def list_categories(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
):
    """List all categories."""
    categories = await permission_service.list_categories(session, skip, limit)
    return [PermissionCategoryRead.model_validate(c) for c in categories]


# Permissions CRUD


@router.post("/", response_model=PermissionRead)
async def create_permission(
    permission_data: PermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Create a new permission."""
    try:
        permission = await permission_service.create_permission(
            permission_data, session
        )
        return PermissionRead.model_validate(permission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[PermissionRead])
async def list_permissions(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
):
    """List all permissions."""
    permissions = await permission_service.list_permissions(session, skip, limit)
    return [PermissionRead.model_validate(p) for p in permissions]


@router.get("/{permission_id}", response_model=PermissionRead)
async def get_permission(
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Get permission by ID."""
    permission = await permission_service.get_permission(permission_id, session)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return PermissionRead.model_validate(permission)


@router.put("/{permission_id}", response_model=PermissionRead)
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Update a permission."""
    permission = await permission_service.update_permission(
        permission_id, permission_data, session
    )
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return PermissionRead.model_validate(permission)


@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Delete a permission."""
    success = await permission_service.delete_permission(permission_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deleted successfully"}


# Permission Routes (Link)


@router.post("/{permission_id}/routes")
async def add_permission_route(
    permission_id: int,
    route_data: PermissionRouteCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Link a permission to a route."""
    # Ensure permission_id matches URL
    if route_data.permission_id != permission_id:
         route_data.permission_id = permission_id
    
    try:
        await permission_service.add_permission_route(
            permission_id, route_data.route_id, session
        )
        return {"message": "Route linked to permission successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# User Permissions (Direct Assignment)


@router.post("/assign", response_model=UserPermissionRead)
async def assign_user_permission(
    assignment_data: UserPermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Assign a permission directly to a user."""
    try:
        user_perm = await permission_service.assign_user_permission(
            assignment_data.user_id, assignment_data.permission_id, session
        )
        return UserPermissionRead(
            permission_id=user_perm.permission_id,
            entity_type=user_perm.entity_type,
            entity_id=user_perm.entity_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=list[PermissionRead])
async def list_user_permissions(
    user_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """List all permissions assigned directly to a user."""
    permissions = await permission_service.list_user_permissions(user_id, session)
    return [PermissionRead.model_validate(p) for p in permissions]


@router.delete("/user/{user_id}/permission/{permission_id}")
async def remove_user_permission(
    user_id: int,
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Remove a direct permission from a user."""
    success = await permission_service.remove_user_permission(user_id, permission_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="User permission assignment not found")
    return {"message": "Permission removed from user successfully"}
