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

from ..settings import settings
from ..utils.redis_client import get_cached_permissions, set_cached_permissions
from ..models.user_tenant_role_model import UserTenantRole

async def check_user_access(
    user_id: int, route_path: str, method: str, session: AsyncSession, tenant_id: int | None = None
) -> bool:
    """
    Check if a user has access to a specific route.
    
    Args:
        user_id: The ID of the user.
        route_path: The request path.
        method: The HTTP method (Ignored in this schema v1 as not in DB).
        session: DB session.
    
    Returns:
        bool: True if allowed.
    """
    
    # 1. Check if route exists and requires validation
    # We strip trailing slash for consistency if needed, but strict match for now
    route_result = await session.exec(
        select(Route).where(Route.name == route_path)
    )
    route = route_result.one_or_none()
    
    # If route doesn't exist in DB, decide default behavior.
    # Usually if it's not registered, we might deny or allow. 
    # Let's assume strict: if not in Routes, Deny (or it's a 404 handled by FastAPI).
    # But often middleware calls this. If unknown route, maybe allow? 
    # Safest is Deny. But if the user didn't populate routes, everything breaks.
    # Let's assume if route is not tracked, we might return False (Deny) 
    # OR we return True if we only secure explicit routes.
    if not route:
        # Default policy: Deny unknown routes? Or Allow?
        # Given "validate" field exists, I assume we only validate tracked routes.
        # If I return False, users can't access anything unless they seed routes.
        # This is safe but annoying.
        # However, for this task, let's return False to be secure.
        return False

    if not route.is_active:
        return True

    # 2. Redis Cache Check
    if route.name:
        cached_routes = await get_cached_permissions(user_id, tenant_id)
        if cached_routes is not None:
            # Cache Hit!
            return route.name in cached_routes

    # 3. Database Check (Cache Miss)
    if settings.enable_tenancy and tenant_id is not None:
        # Tenancy Mode: query via UserTenantRole
        role_perms = (
            select(PermissionAssignment.permission_id)
            .join(UserTenantRole, UserTenantRole.role_id == PermissionAssignment.entity_id)
            .where(
                UserTenantRole.user_id == user_id,
                UserTenantRole.tenant_id == tenant_id,
                PermissionAssignment.entity_type == "Role"
            )
        )
        user_perm_ids_query = role_perms.subquery()
    else:
        # Global Mode: query via UserRole and direct PermissionAssignment
        direct_perms = (
            select(PermissionAssignment.permission_id)
            .where(
                PermissionAssignment.entity_type == "User",
                PermissionAssignment.entity_id == user_id
            )
        )
        role_perms = (
            select(PermissionAssignment.permission_id)
            .join(UserRole, (UserRole.role_id == PermissionAssignment.entity_id) & (PermissionAssignment.entity_type == "Role"))
            .where(
                UserRole.user_id == user_id
            )
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
    await set_cached_permissions(user_id, tenant_id, allowed_route_names)

    return route.name in allowed_route_names
