"""
Access Service

Handles high-level access control logic, caching, and permission aggregation.
"""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.role_permission_model import RolePermission
from ..models.user_permission_model import UserPermission
from ..models.user_role_model import UserRole
from ..utils import permission_cache


async def get_all_user_permissions(
    user_id: int, session: AsyncSession
) -> list[dict]:
    """
    Fetch all effective permissions for a user from the database.
    Aggregates:
    1. Direct user permissions (UserPermission) - Highest priority
    2. Permissions from assigned roles (RolePermission)
    """
    permissions = []
    
    # 1. Fetch direct user permissions
    user_perms_result = await session.execute(
        select(UserPermission).where(UserPermission.user_id == user_id)
    )
    user_perms = user_perms_result.scalars().all()
    
    for perm in user_perms:
        permissions.append({
            "route_path": perm.route_path,
            "method": perm.method,
            "is_allowed": perm.is_allowed,
            "expires_at": perm.expires_at.isoformat() if perm.expires_at else None,
            "source": "user",  # Metadata
        })

    # 2. Fetch permissions from user's roles
    # Join UserRole -> RolePermission
    role_perms_result = await session.execute(
        select(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    )
    role_perms = role_perms_result.scalars().all()

    for perm in role_perms:
        # Avoid duplicates if overridden by user permission? 
        # For now, we add all. The checker needs to handle priority if conflicts exist.
        # But a simple list check might find the first match. 
        # To handle priority properly, we should probably deduplicate or sort.
        # User permissions should come first in the list if the checker stops at first match.
        permissions.append({
            "route_path": perm.route_path,
            "method": perm.method,
            "is_allowed": perm.is_allowed,
            "expires_at": perm.expires_at.isoformat() if perm.expires_at else None,
            "source": "role",
        })

    return permissions


async def check_user_access(
    user_id: int, route_path: str, method: str, session: AsyncSession
) -> bool:
    """
    Check if a user has access to a specific route and method.
    Uses caching for performance.
    
    Logic:
    1. Check Redis cache.
    2. If not cached, fetch from DB.
    3. Cache the result.
    4. Perform the check.
    
    Returns:
        bool: True if allowed, False otherwise.
    """
    # 1. Try cache
    is_allowed = await permission_cache.check_route_access(user_id, route_path, method)
    
    if is_allowed is not None:
        return is_allowed

    # 2. Cache miss - Fetch from DB
    permissions = await get_all_user_permissions(user_id, session)
    
    # 3. Populate cache
    await permission_cache.cache_user_permissions(user_id, permissions)
    
    # 4. Check again (using the logic in permission_cache.check_route_access but locally)
    # We can just call the cache check again since it's now populated, 
    # OR replicate the logic to save a round trip if we just wrote it.
    # But for consistency, let's look at the fetched permissions directly.
    
    for perm in permissions:
        if perm["route_path"] == route_path:
            if perm["method"] in (method, "*"):
                 # Check expiration
                if perm["expires_at"]:
                    try:
                        expires = datetime.fromisoformat(perm["expires_at"])
                        if datetime.utcnow() > expires:
                            continue
                    except ValueError:
                        continue
                
                return perm["is_allowed"]

    # Default deny if no permission explicitly matches
    return False
