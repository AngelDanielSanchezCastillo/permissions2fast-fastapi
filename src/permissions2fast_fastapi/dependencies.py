"""
FastAPI Dependencies

Dependencies for protecting routes based on roles and permissions.
"""

from typing import Annotated

from fastapi import Depends, Request
from oauth2fast_fastapi import User

# Import from oauth2fast-fastapi directly
from oauth2fast_fastapi.dependencies import get_auth_session, get_current_verified_user
from sqlmodel.ext.asyncio.session import AsyncSession
from tools2fast_fastapi import AuthError

from .services import access_service, role_service


def has_role(
    role_name: str,
):
    """
    Dependency to require a specific role.

    Usage::

        @app.get("/admin")
        def admin_route(user: User = Depends(has_role("admin"))):
            ...
    """

    async def _has_role(
        user: Annotated[User, Depends(get_current_verified_user)],
        session: Annotated[AsyncSession, Depends(get_auth_session)],
    ) -> User:
        user_roles = await role_service.list_user_roles(user.id, session)

        has_required = any(r.name == role_name for r in user_roles)

        if not has_required:
            raise AuthError(
                error_code="RoleMissing",
                message=f"Rol requerido: {role_name}",
                status_code=403,
            )

        return user

    return _has_role


def has_permission(
    permission_route: str | None = None,
    method: str | None = None,
):
    """
    Dependency to require permission for a route.

    If params are None, verifies access to the *current* request path and method.

    Usage::

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
        user: Annotated[User, Depends(get_current_verified_user)],
        session: Annotated[AsyncSession, Depends(get_auth_session)],
    ) -> User:
        # Use the FastAPI route template (e.g. /roles/user/{user_id}) instead of
        # the real URL path (e.g. /roles/user/1) so it matches the stored routes.
        if permission_route is not None:
            route_to_check = permission_route
        else:
            fastapi_route = request.scope.get("route")
            route_to_check = fastapi_route.path if fastapi_route else request.url.path
        method_to_check = method or request.method

        is_allowed = await access_service.check_user_access(
            user.id, route_to_check, method_to_check, session
        )

        if not is_allowed:
            raise AuthError(
                error_code="PermissionDenied",
                message="Permisos insuficientes para acceder a este recurso",
                status_code=403,
            )

        return user

    return _has_permission
