"""
Role Service

Business logic for role management including CRUD operations,
permission assignment, and user-role management.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from ..models.role_model import Role
from ..models.user_role_model import UserRole
from ..models.permission_assignment_model import PermissionAssignment
from ..models.permission_model import Permission
from ..models.user_tenant_role_model import UserTenantRole
from ..settings import settings
from ..utils.redis_client import invalidate_user_cache
from ..schemas.role_schema import (
    RoleCreate,
    RoleUpdate,
    # UserRoleCreate, # We might need to handle this via schema or arguments
)

# We define local types or reuse schemas where appropriate
# For assign_user_role, we can take user_id and role_id directly or use a schema


async def create_role(role_data: RoleCreate, session: AsyncSession) -> Role:
    """Create a new role."""
    role = Role(**role_data.model_dump())
    session.add(role)
    try:
        await session.commit()
        await session.refresh(role)
        return role
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Role '{role_data.name}' already exists")


async def get_role(role_id: int, session: AsyncSession) -> Role | None:
    """Get role by ID."""
    result = await session.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()


async def list_roles(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Role]:
    """List all roles."""
    result = await session.execute(
        select(Role).offset(skip).limit(limit).order_by(Role.name)
    )
    return list(result.scalars().all())


async def update_role(
    role_id: int, role_data: RoleUpdate, session: AsyncSession
) -> Role | None:
    """Update a role."""
    role = await get_role(role_id, session)
    if not role:
        return None

    update_data = role_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)

    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


async def delete_role(role_id: int, session: AsyncSession) -> bool:
    """Delete a role."""
    role = await get_role(role_id, session)
    if not role:
        return False

    await session.delete(role)
    await session.commit()
    return True


# Role Permissions (PermissionAssignment where entity_type='Role')


async def add_role_permission(
    role_id: int, permission_id: int, session: AsyncSession
) -> PermissionAssignment:
    """Add a permission to a role."""
    # Check if exists
    existing = await session.execute(
        select(PermissionAssignment).where(
            PermissionAssignment.permission_id == permission_id,
            PermissionAssignment.entity_type == "Role",
            PermissionAssignment.entity_id == role_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Permission already assigned to this role")

    model_has_permission = PermissionAssignment(
        permission_id=permission_id,
        entity_type="Role",
        entity_id=role_id,
    )
    session.add(model_has_permission)
    try:
        await session.commit()
        await session.refresh(model_has_permission)
        return model_has_permission
    except IntegrityError: # Should be caught by check above usually
        await session.rollback()
        raise ValueError("Error assigning permission to role")


async def list_role_permissions(
    role_id: int, session: AsyncSession
) -> list[Permission]:
    """List all permissions for a role."""
    # Join PermissionAssignment with Permission
    stmt = (
        select(Permission)
        .join(PermissionAssignment, PermissionAssignment.permission_id == Permission.id)
        .where(
            PermissionAssignment.entity_type == "Role",
            PermissionAssignment.entity_id == role_id,
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_role_permission(
    role_id: int, permission_id: int, session: AsyncSession
) -> bool:
    """Delete a role permission."""
    stmt = select(PermissionAssignment).where(
        PermissionAssignment.permission_id == permission_id,
        PermissionAssignment.entity_type == "Role",
        PermissionAssignment.entity_id == role_id,
    )
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()

    if not link:
        return False

    await session.delete(link)
    await session.commit()
    return True


# User Roles (UserRole where entity_type='User')


async def assign_user_role(
    user_id: int, role_id: int, session: AsyncSession, tenant_id: int | None = None
) -> UserRole | UserTenantRole:
    """Assign a role to a user."""
    if settings.enable_tenancy and tenant_id is not None:
        # Check if exists in UserTenantRole
        existing = await session.execute(
            select(UserTenantRole).where(
                UserTenantRole.role_id == role_id,
                UserTenantRole.user_id == user_id,
                UserTenantRole.tenant_id == tenant_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already has this role in the specified tenant")

        user_role = UserTenantRole(
            role_id=role_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
    else:
        # Check if exists in global UserRole
        existing = await session.execute(
            select(UserRole).where(
                UserRole.role_id == role_id,
                UserRole.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already has this global role")

        user_role = UserRole(
            role_id=role_id,
            user_id=user_id,
        )

    session.add(user_role)
    try:
        await session.commit()
        await session.refresh(user_role)
        # Invalidate cache
        await invalidate_user_cache(user_id)
        return user_role
    except IntegrityError:
        await session.rollback()
        raise ValueError("Error assigning role to user")


async def list_user_roles(user_id: int, session: AsyncSession, tenant_id: int | None = None) -> list[Role]:
    """List all roles assigned to a user."""
    if settings.enable_tenancy and tenant_id is not None:
        stmt = (
            select(Role)
            .join(UserTenantRole, UserTenantRole.role_id == Role.id)
            .where(
                UserTenantRole.user_id == user_id,
                UserTenantRole.tenant_id == tenant_id
            )
        )
    else:
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id
            )
        )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def remove_user_role(user_id: int, role_id: int, session: AsyncSession, tenant_id: int | None = None) -> bool:
    """Remove a role from a user."""
    if settings.enable_tenancy and tenant_id is not None:
        stmt = select(UserTenantRole).where(
            UserTenantRole.role_id == role_id,
            UserTenantRole.user_id == user_id,
            UserTenantRole.tenant_id == tenant_id,
        )
    else:
        stmt = select(UserRole).where(
            UserRole.role_id == role_id,
            UserRole.user_id == user_id,
        )
        
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()

    if not link:
        return False

    await session.delete(link)
    await session.commit()
    # Invalidate cache
    await invalidate_user_cache(user_id)
    return True
