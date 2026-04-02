"""
Permission Service

Business logic for managing permissions, categories, and user-specific assignments.
"""

from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from ..models.permission_model import Permission
from ..models.permission_category_model import PermissionCategory
from ..models.permission_assignment_model import PermissionAssignment
from ..models.permission_route_model import PermissionRoute
from ..models.route_model import Route
from ..schemas.permission_schema import PermissionCreate, PermissionUpdate
from ..schemas.permission_category_schema import PermissionCategoryCreate

# Categories

async def create_category(
    category_data: PermissionCategoryCreate, session: AsyncSession
) -> PermissionCategory:
    """Create a new permission category."""
    category = PermissionCategory(**category_data.model_dump())
    session.add(category)
    try:
        await session.commit()
        await session.refresh(category)
        return category
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Category '{category_data.name}' already exists")

async def list_categories(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[PermissionCategory]:
    """List all categories."""
    result = await session.exec(
        select(PermissionCategory).offset(skip).limit(limit).order_by(PermissionCategory.name)
    )
    return list(result.all())

# Permissions

async def create_permission(
    permission_data: PermissionCreate, session: AsyncSession
) -> Permission:
    """Create a new permission."""
    permission = Permission(**permission_data.model_dump())
    session.add(permission)
    try:
        await session.commit()
        await session.refresh(permission)
        return permission
    except IntegrityError:
        await session.rollback()
        raise ValueError(f"Permission '{permission_data.name}' already exists")


async def get_permission(
    permission_id: int, session: AsyncSession
) -> Permission | None:
    """Get permission by ID."""
    result = await session.exec(
        select(Permission).where(Permission.id == permission_id)
    )
    return result.one_or_none()


async def list_permissions(
    session: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Permission]:
    """List all permissions."""
    result = await session.exec(
        select(Permission).offset(skip).limit(limit).order_by(Permission.name)
    )
    return list(result.all())


async def update_permission(
    permission_id: int, permission_data: PermissionUpdate, session: AsyncSession
) -> Permission | None:
    """Update a permission."""
    permission = await get_permission(permission_id, session)
    if not permission:
        return None

    update_data = permission_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(permission, key, value)

    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    return permission


async def delete_permission(permission_id: int, session: AsyncSession) -> bool:
    """Delete a permission."""
    permission = await get_permission(permission_id, session)
    if not permission:
        return False

    await session.delete(permission)
    await session.commit()
    return True

# Permission Routes

async def add_permission_route(
    permission_id: int, route_id: int, session: AsyncSession
) -> PermissionRoute:
    """Link a permission to a route."""
    existing = await session.exec(
        select(PermissionRoute).where(
            PermissionRoute.permission_id == permission_id,
            PermissionRoute.route_id == route_id
        )
    )
    if existing.one_or_none():
         raise ValueError("Route already assigned to permission")

    perm_route = PermissionRoute(permission_id=permission_id, route_id=route_id)
    session.add(perm_route)
    try:
        await session.commit()
        await session.refresh(perm_route)
        return perm_route
    except IntegrityError:
        await session.rollback()
        raise ValueError("Error linking permission to route")

# User Permissions

async def assign_user_permission(
    user_id: int, permission_id: int, session: AsyncSession
) -> PermissionAssignment:
    """Assign a permission directly to a user."""
    existing = await session.exec(
        select(PermissionAssignment).where(
            PermissionAssignment.permission_id == permission_id,
            PermissionAssignment.entity_type == "User",
            PermissionAssignment.entity_id == user_id,
        )
    )
    if existing.one_or_none():
         raise ValueError("Permission already assigned to user")

    model_has_perm = PermissionAssignment(
        permission_id=permission_id,
        entity_type="User",
        entity_id=user_id,
    )
    session.add(model_has_perm)
    try:
        await session.commit()
        await session.refresh(model_has_perm)
        return model_has_perm
    except IntegrityError:
        await session.rollback()
        raise ValueError("Error assigning permission to user")


async def list_user_permissions(
    user_id: int, session: AsyncSession
) -> list[Permission]:
    """List all direct permissions for a specific user."""
    stmt = (
        select(Permission)
        .join(PermissionAssignment, PermissionAssignment.permission_id == Permission.id)
        .where(
            PermissionAssignment.entity_type == "User",
            PermissionAssignment.entity_id == user_id
        )
    )
    result = await session.exec(stmt)
    return list(result.all())

async def remove_user_permission(
    user_id: int, permission_id: int, session: AsyncSession
) -> bool:
    """Remove a direct permission from a user."""
    stmt = select(PermissionAssignment).where(
        PermissionAssignment.permission_id == permission_id,
        PermissionAssignment.entity_type == "User",
        PermissionAssignment.entity_id == user_id,
    )
    result = await session.exec(stmt)
    link = result.one_or_none()

    if not link:
        return False

    await session.delete(link)
    await session.commit()
    return True
