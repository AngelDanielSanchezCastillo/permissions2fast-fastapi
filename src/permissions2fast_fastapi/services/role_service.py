"""
Role Service

Business logic for role management including CRUD operations,
permission assignment, and user-role management.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.role_model import Role
from ..models.role_permission_model import RolePermission
from ..models.user_role_model import UserRole
from ..schemas.role_schema import (
    RoleCreate,
    RolePermissionCreate,
    RoleUpdate,
    UserRoleCreate,
)


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
        raise ValueError(f"Role '{role_data.name}' already exists for this tenant")


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


# Role Permissions


async def add_role_permission(
    perm_data: RolePermissionCreate, session: AsyncSession
) -> RolePermission:
    """Add a permission to a role."""
    permission = RolePermission(**perm_data.model_dump())
    session.add(permission)
    try:
        await session.commit()
        await session.refresh(permission)
        return permission
    except IntegrityError:
        await session.rollback()
        raise ValueError("This permission already exists for this role")


async def list_role_permissions(
    role_id: int, session: AsyncSession
) -> list[RolePermission]:
    """List all permissions for a role."""
    result = await session.execute(
        select(RolePermission).where(RolePermission.role_id == role_id)
    )
    return list(result.scalars().all())


async def delete_role_permission(permission_id: int, session: AsyncSession) -> bool:
    """Delete a role permission."""
    result = await session.execute(
        select(RolePermission).where(RolePermission.id == permission_id)
    )
    permission = result.scalar_one_or_none()

    if not permission:
        return False

    await session.delete(permission)
    await session.commit()
    return True


# User Roles


async def assign_user_role(
    assignment_data: UserRoleCreate, session: AsyncSession
) -> UserRole:
    """Assign a role to a user."""
    user_role = UserRole(**assignment_data.model_dump())
    session.add(user_role)
    try:
        await session.commit()
        await session.refresh(user_role)

        # Note: Permission cache invalidation would be handled by app if needed
        # from app.utils.permission_cache import invalidate_user_cache
        # await invalidate_user_cache(assignment_data.user_id)

        return user_role
    except IntegrityError:
        await session.rollback()
        raise ValueError("User already has this role")


async def list_user_roles(user_id: int, session: AsyncSession) -> list[UserRole]:
    """List all roles assigned to a user."""
    result = await session.execute(select(UserRole).where(UserRole.user_id == user_id))
    return list(result.scalars().all())


async def remove_user_role(user_id: int, role_id: int, session: AsyncSession) -> bool:
    """Remove a role from a user."""
    result = await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    user_role = result.scalar_one_or_none()

    if not user_role:
        return False

    await session.delete(user_role)
    await session.commit()

    # Note: Permission cache invalidation would be handled by app if needed
    # from app.utils.permission_cache import invalidate_user_cache
    # await invalidate_user_cache(user_id)

    return True


# Seed Data


async def create_default_roles(session: AsyncSession) -> dict[str, Role]:
    """
    Create default roles.
    Returns dict with role names as keys.
    Note: tenant_id will be added by tenant2fast_fastapi module.
    """
    roles = {}

    # Admin role - full access
    admin = await create_role(
        RoleCreate(
            name="Admin",
            description="Full system access",
        ),
        session,
    )
    roles["admin"] = admin

    # Add admin permissions
    await add_role_permission(
        RolePermissionCreate(
            role_id=admin.id, route_path="/api/v1/*", method="*", is_allowed=True
        ),
        session,
    )

    # Editor role - read and write
    editor = await create_role(
        RoleCreate(
            name="Editor",
            description="Can read and modify data",
        ),
        session,
    )
    roles["editor"] = editor

    # Add editor permissions
    for method in ["GET", "POST", "PUT"]:
        await add_role_permission(
            RolePermissionCreate(
                role_id=editor.id,
                route_path="/api/v1/*",
                method=method,
                is_allowed=True,
            ),
            session,
        )

    # Viewer role - read only
    viewer = await create_role(
        RoleCreate(
            name="Viewer",
            description="Read-only access",
        ),
        session,
    )
    roles["viewer"] = viewer

    # Add viewer permissions
    await add_role_permission(
        RolePermissionCreate(
            role_id=viewer.id, route_path="/api/v1/*", method="GET", is_allowed=True
        ),
        session,
    )

    return roles
