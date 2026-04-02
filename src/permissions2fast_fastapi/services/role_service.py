"""
Role Service

Business logic for role management including CRUD operations,
permission assignment, and user-role management.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete

from ..models.role_model import Role
from ..models.user_role_model import UserRole
from ..models.permission_assignment_model import PermissionAssignment
from ..models.permission_model import Permission
from ..utils.redis_client import invalidate_user_cache
from ..schemas.role_schema import (
    RoleCreate,
    RoleUpdate,
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
        raise ValueError(f"Role '{role_data.name}' already exists")


async def get_role(role_id: int, session: AsyncSession) -> Role | None:
    """Get role by ID."""
    result = await session.exec(select(Role).where(Role.id == role_id))
    return result.one_or_none()


async def list_roles(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Role]:
    """List all roles."""
    result = await session.exec(
        select(Role).offset(skip).limit(limit).order_by(Role.name)
    )
    return list(result.all())


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
    existing = await session.exec(
        select(PermissionAssignment).where(
            PermissionAssignment.permission_id == permission_id,
            PermissionAssignment.entity_type == "Role",
            PermissionAssignment.entity_id == role_id,
        )
    )
    if existing.one_or_none():
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
    except IntegrityError:
        await session.rollback()
        raise ValueError("Error assigning permission to role")


async def list_role_permissions(
    role_id: int, session: AsyncSession
) -> list[Permission]:
    """List all permissions for a role."""
    stmt = (
        select(Permission)
        .join(PermissionAssignment, PermissionAssignment.permission_id == Permission.id)
        .where(
            PermissionAssignment.entity_type == "Role",
            PermissionAssignment.entity_id == role_id,
        )
    )
    result = await session.exec(stmt)
    return list(result.all())


async def delete_role_permission(
    role_id: int, permission_id: int, session: AsyncSession
) -> bool:
    """Delete a role permission."""
    stmt = select(PermissionAssignment).where(
        PermissionAssignment.permission_id == permission_id,
        PermissionAssignment.entity_type == "Role",
        PermissionAssignment.entity_id == role_id,
    )
    result = await session.exec(stmt)
    link = result.one_or_none()

    if not link:
        return False

    await session.delete(link)
    await session.commit()
    return True


# User Roles


async def assign_user_role(
    user_id: int, role_id: int, session: AsyncSession
) -> UserRole:
    """Assign a role to a user."""
    existing = await session.exec(
        select(UserRole).where(
            UserRole.role_id == role_id,
            UserRole.user_id == user_id,
        )
    )
    if existing.one_or_none():
        raise ValueError("User already has this role")

    user_role = UserRole(
        role_id=role_id,
        user_id=user_id,
    )

    session.add(user_role)
    try:
        await session.commit()
        await session.refresh(user_role)
        await invalidate_user_cache(user_id)
        return user_role
    except IntegrityError:
        await session.rollback()
        raise ValueError("Error assigning role to user")


async def list_user_roles(user_id: int, session: AsyncSession) -> list[Role]:
    """List all roles assigned to a user."""
    stmt = (
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
    )
    result = await session.exec(stmt)
    return list(result.all())


async def remove_user_role(user_id: int, role_id: int, session: AsyncSession) -> bool:
    """Remove a role from a user."""
    stmt = select(UserRole).where(
        UserRole.role_id == role_id,
        UserRole.user_id == user_id,
    )
    result = await session.exec(stmt)
    link = result.one_or_none()

    if not link:
        return False

    await session.delete(link)
    await session.commit()
    await invalidate_user_cache(user_id)
    return True
