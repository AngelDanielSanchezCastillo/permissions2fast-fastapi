"""
Permission Management Router

Endpoints for managing user-specific permissions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.permission_schema import (
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
)
from ..services import permission_service
from oauth2fast_fastapi.dependencies import get_auth_session

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post("/", response_model=PermissionRead)
async def create_permission(
    permission_data: PermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Create a new user permission."""
    try:
        permission = await permission_service.create_permission(
            permission_data, session
        )
        return PermissionRead.model_validate(permission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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


@router.get("/user/{user_id}", response_model=list[PermissionRead])
async def list_user_permissions(
    user_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """List all permissions for a specific user."""
    permissions = await permission_service.list_user_permissions(user_id, session)
    return [PermissionRead.model_validate(p) for p in permissions]


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
