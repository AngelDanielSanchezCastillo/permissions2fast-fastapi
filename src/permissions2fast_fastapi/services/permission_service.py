"""
Permission Service

Business logic for managing user-specific permissions.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.user_permission_model import UserPermission
from ..schemas.permission_schema import PermissionCreate, PermissionUpdate


async def create_permission(
    permission_data: PermissionCreate, session: AsyncSession
) -> UserPermission:
    """Create a new user permission."""
    permission = UserPermission(**permission_data.model_dump())
    session.add(permission)
    try:
        await session.commit()
        await session.refresh(permission)

        # Note: Permission cache invalidation would be handled by app if needed
        # from app.utils.permission_cache import invalidate_user_cache
        # await invalidate_user_cache(permission.user_id)

        return permission
    except IntegrityError:
        await session.rollback()
        raise ValueError("Permission already exists for this user/route/method")


async def get_permission(
    permission_id: int, session: AsyncSession
) -> UserPermission | None:
    """Get permission by ID."""
    result = await session.execute(
        select(UserPermission).where(UserPermission.id == permission_id)
    )
    return result.scalar_one_or_none()


async def list_user_permissions(
    user_id: int, session: AsyncSession
) -> list[UserPermission]:
    """List all permissions for a specific user."""
    result = await session.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
    )
    return list(result.scalars().all())


async def update_permission(
    permission_id: int, permission_data: PermissionUpdate, session: AsyncSession
) -> UserPermission | None:
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

    # Note: Permission cache invalidation would be handled by app if needed
    # from app.utils.permission_cache import invalidate_user_cache
    # await invalidate_user_cache(permission.user_id)

    return permission


async def delete_permission(permission_id: int, session: AsyncSession) -> bool:
    """Delete a permission."""
    permission = await get_permission(permission_id, session)
    if not permission:
        return False

    user_id = permission.user_id
    await session.delete(permission)
    await session.commit()

    # Note: Permission cache invalidation would be handled by app if needed
    # from app.utils.permission_cache import invalidate_user_cache
    # await invalidate_user_cache(user_id)

    return True
