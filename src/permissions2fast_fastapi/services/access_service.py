"""
Access Service

Handles high-level access control logic and permission checking.
"""

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, union

from ..models.permission_assignment_model import PermissionAssignment
from ..models.user_role_model import UserRole
from ..models.permission_route_model import PermissionRoute
from ..models.route_model import Route

from ..utils.redis_client import get_cached_permissions, set_cached_permissions


async def check_user_access(
    user_id: int, route_path: str, method: str, session: AsyncSession
) -> bool:
    """
    Check if a user has access to a specific route.

    Args:
        user_id: The ID of the user.
        route_path: The request path.
        method: The HTTP method.
        session: DB session.

    Returns:
        bool: True if allowed.
    """

    # 1. Check if route exists and is tracked
    route_result = await session.exec(
        select(Route).where(Route.name == route_path)
    )
    route = route_result.one_or_none()

    if not route:
        return False

    if not route.is_active:
        return True

    # 2. Redis Cache Check
    if route.name:
        cached_routes = await get_cached_permissions(user_id)
        if cached_routes is not None:
            return route.name in cached_routes

    # 3. Database Check (Cache Miss)
    direct_perms = (
        select(PermissionAssignment.permission_id)
        .where(
            PermissionAssignment.entity_type == "User",
            PermissionAssignment.entity_id == user_id,
        )
    )
    role_perms = (
        select(PermissionAssignment.permission_id)
        .join(
            UserRole,
            (UserRole.role_id == PermissionAssignment.entity_id)
            & (PermissionAssignment.entity_type == "Role"),
        )
        .where(UserRole.user_id == user_id)
    )
    user_perm_ids_query = union(direct_perms, role_perms).subquery()

    # Get allowed routes for these permissions
    stmt = (
        select(Route.name)
        .join(PermissionRoute, PermissionRoute.route_id == Route.id)
        .where(PermissionRoute.permission_id.in_(select(user_perm_ids_query)))
    )
    result = await session.exec(stmt)
    allowed_route_names = list(result.all())

    # 4. Cache the result for future requests
    await set_cached_permissions(user_id, allowed_route_names)

    return route.name in allowed_route_names
