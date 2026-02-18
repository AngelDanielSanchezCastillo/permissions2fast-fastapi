"""
Role Management Router

Endpoints for managing roles, role permissions, and user-role assignments.
Note: Tenant-scoped functionality will be added by tenant2fast_fastapi module.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.role_schema import (
    RoleCreate,
    RolePermissionCreate,
    RolePermissionRead,
    RoleRead,
    RoleUpdate,
    UserRoleCreate,
    UserRoleRead,
)
from ..services import role_service
from oauth2fast_fastapi.dependencies import get_auth_session

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


# Role CRUD


@router.post("/", response_model=RoleRead)
async def create_role(
    role_data: RoleCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Create a new role."""
    try:
        role = await role_service.create_role(role_data, session)
        return RoleRead.model_validate(role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[RoleRead])
async def list_roles(
    session: AsyncSession = Depends(get_auth_session),
    skip: int = 0,
    limit: int = 100,
):
    """List all roles."""
    roles = await role_service.list_roles(session, skip, limit)
    return [RoleRead.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Get role by ID."""
    role = await role_service.get_role(role_id, session)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleRead.model_validate(role)


@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Update a role."""
    role = await role_service.update_role(role_id, role_data, session)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleRead.model_validate(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Delete a role."""
    success = await role_service.delete_role(role_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}


# Role Permissions


@router.post("/{role_id}/permissions", response_model=RolePermissionRead)
async def add_role_permission(
    role_id: int,
    perm_data: RolePermissionCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Add a permission to a role."""
    # Ensure role_id matches
    perm_data.role_id = role_id

    try:
        permission = await role_service.add_role_permission(perm_data, session)
        return RolePermissionRead.model_validate(permission)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{role_id}/permissions", response_model=list[RolePermissionRead])
async def list_role_permissions(
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """List all permissions for a role."""
    permissions = await role_service.list_role_permissions(role_id, session)
    return [RolePermissionRead.model_validate(p) for p in permissions]


@router.delete("/{role_id}/permissions/{permission_id}")
async def delete_role_permission(
    role_id: int,
    permission_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Delete a role permission."""
    success = await role_service.delete_role_permission(permission_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="Permission not found")
    return {"message": "Permission deleted successfully"}


# User Roles


@router.post("/assign", response_model=UserRoleRead)
async def assign_user_role(
    assignment_data: UserRoleCreate,
    session: AsyncSession = Depends(get_auth_session),
):
    """Assign a role to a user."""
    try:
        user_role = await role_service.assign_user_role(assignment_data, session)
        return UserRoleRead.model_validate(user_role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=list[UserRoleRead])
async def list_user_roles(
    user_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """List all roles assigned to a user."""
    user_roles = await role_service.list_user_roles(user_id, session)
    return [UserRoleRead.model_validate(ur) for ur in user_roles]


@router.delete("/user/{user_id}/role/{role_id}")
async def remove_user_role(
    user_id: int,
    role_id: int,
    session: AsyncSession = Depends(get_auth_session),
):
    """Remove a role from a user."""
    success = await role_service.remove_user_role(user_id, role_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="User role assignment not found")
    return {"message": "Role removed from user successfully"}
