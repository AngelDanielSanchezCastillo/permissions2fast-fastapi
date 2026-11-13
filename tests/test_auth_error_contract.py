"""
Auth error contract for permission dependencies (0.11.0).

Both ``has_role`` and ``has_permission`` must raise ``AuthError`` with a stable
``error.type`` so the frontend can react to a 403 without logging the user out:

- missing role    → 403 ``RoleMissing``
- missing perm    → 403 ``PermissionDenied``
- allowed         → 200

No ``WWW-Authenticate`` header belongs on a 403.
"""

from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from oauth2fast_fastapi.dependencies import (
    get_auth_session,
    get_current_verified_user,
)
from tools2fast_fastapi import install_auth_error_handler

from permissions2fast_fastapi.dependencies import has_permission, has_role
from permissions2fast_fastapi.models.role_model import Role


@pytest.fixture
def error_app(test_user, session):
    app = FastAPI()
    install_auth_error_handler(app)

    app.dependency_overrides[get_current_verified_user] = lambda: test_user
    app.dependency_overrides[get_auth_session] = lambda: session

    @app.get("/role-protected")
    async def role_protected(
        user=Depends(has_role("AdminRole")),
    ) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/perm-protected")
    async def perm_protected(
        user=Depends(has_permission(permission_route="/perm-protected", method="GET")),
    ) -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture
async def error_client(error_app):
    async with AsyncClient(
        transport=ASGITransport(app=error_app), base_url="http://test"
    ) as client:
        yield client


async def test_missing_role_returns_403_role_missing(error_client):
    with patch(
        "permissions2fast_fastapi.dependencies.role_service.list_user_roles",
        return_value=[],
    ):
        response = await error_client.get("/role-protected")

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "RoleMissing"
    assert response.headers.get("www-authenticate") is None


async def test_missing_permission_returns_403_permission_denied(error_client):
    with patch(
        "permissions2fast_fastapi.dependencies.access_service.check_user_access",
        return_value=False,
    ):
        response = await error_client.get("/perm-protected")

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["type"] == "PermissionDenied"
    assert response.headers.get("www-authenticate") is None


async def test_granted_role_returns_200(error_client):
    with patch(
        "permissions2fast_fastapi.dependencies.role_service.list_user_roles",
        return_value=[Role(name="AdminRole")],
    ):
        response = await error_client.get("/role-protected")

    assert response.status_code == 200


async def test_granted_permission_returns_200(error_client):
    with patch(
        "permissions2fast_fastapi.dependencies.access_service.check_user_access",
        return_value=True,
    ):
        response = await error_client.get("/perm-protected")

    assert response.status_code == 200
