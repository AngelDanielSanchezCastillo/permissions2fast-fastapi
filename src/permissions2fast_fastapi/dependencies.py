"""
FastAPI Dependencies

Dependencies for protecting routes based on roles and permissions.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

# Import from oauth2fast-fastapi directly
from oauth2fast_fastapi.dependencies import get_current_active_user, get_auth_session
from oauth2fast_fastapi.models import User

from .services import access_service, role_service


async def has_role(
    role_name: str,
) -> Annotated[User, Depends]:
    """
    Dependency to require a specific role.
    
    Usage:
        @app.get("/admin")
        def admin_route(user: User = Depends(has_role("admin"))):
            ...
    """
    async def _has_role(
        user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(get_auth_session)],
    ) -> User:
        user_roles = await role_service.list_user_roles(user.id, session)
        
        # We need to fetch the role names. UserRole only has role_id.
        # This is a bit inefficient (N+1), but simple.
        # Ideally role_service.list_user_roles would join with Role.
        
        # Better approach: check if any assigned role matches the name
        # We can do this efficiently in the service but for now let's use what we have
        # or implement a specific check in role_service.
        
        # Let's iterate and fetch logic for now, or assume we know the mapping.
        # Actually, let's optimize this lookup by checking Role table.
        
        from sqlmodel import select
        from .models.role_model import Role
        from .models.user_role_model import UserRole
        
        result = await session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
            .where(Role.name == role_name)
        )
        role = result.scalar_one_or_none()
        
        if not role:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role_name}",
            )
        
        return user

    return _has_role


async def has_permission(
    permission_route: str | None = None,
    method: str | None = None,
) -> Annotated[User, Depends]:
    """
    Dependency to require permission for a route.
    
    If params are None, verifies access to the *current* request path and method.
    
    Usage:
        @app.get("/items")
        def items(user: User = Depends(has_permission())): 
            # Checks if user can GET /items
            ...
            
        @app.get("/items")
        def items(user: User = Depends(has_permission(permission_route="/api/items", method="GET"))):
            ...
    """
    async def _has_permission(
        request: Request,
        user: Annotated[User, Depends(get_current_active_user)],
        session: Annotated[AsyncSession, Depends(get_auth_session)],
    ) -> User:
        # Determine what to check
        route_to_check = permission_route or request.url.path
        method_to_check = method or request.method
        
        is_allowed = await access_service.check_user_access(
            user.id, route_to_check, method_to_check, session
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this resource",
            )
            
        return user

    return _has_permission
