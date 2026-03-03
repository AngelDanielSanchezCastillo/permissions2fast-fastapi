import pytest
from httpx import AsyncClient

from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.user_role_model import UserRole
from permissions2fast_fastapi.models.permission_category_model import PermissionCategory
from permissions2fast_fastapi.models.permission_model import Permission
from permissions2fast_fastapi.models.route_model import Route
from permissions2fast_fastapi.models.permission_route_model import PermissionRoute
from permissions2fast_fastapi.models.permission_assignment_model import PermissionAssignment
from permissions2fast_fastapi.services import access_service

# We reuse test_user and test_role from conftest.py

@pytest.fixture
async def user_with_permission(test_user):
    # Reuse the common test_user
    return test_user

@pytest.fixture
async def admin_role(session):
    role = Role(name="AdminRole", description="Admin Role")
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role

@pytest.fixture
async def setup_permissions(session, user_with_permission, admin_role):
    # 1. Setup Models
    category = PermissionCategory(name="Integration Test")
    session.add(category)
    await session.commit()
    
    # Permission 1: Linked to AdminRole
    perm_admin = Permission(name="admin_access", permission_category_id=category.id)
    session.add(perm_admin)
    
    # Permission 2: Linked to User directly
    perm_user = Permission(name="user_access", permission_category_id=category.id)
    session.add(perm_user)
    
    # Routes
    route_admin = Route(name="/api/admin", validate=True)
    session.add(route_admin)
    route_user = Route(name="/api/user", validate=True)
    session.add(route_user)
    route_public = Route(name="/api/public", is_active=False)
    session.add(route_public)
    
    await session.commit()
    await session.refresh(perm_admin)
    await session.refresh(perm_user)
    await session.refresh(route_admin)
    await session.refresh(route_user)
    
    # Link Permissions -> Routes
    session.add(PermissionRoute(permission_id=perm_admin.id, route_id=route_admin.id))
    session.add(PermissionRoute(permission_id=perm_user.id, route_id=route_user.id))
    
    # Assign Role -> User
    session.add(UserRole(role_id=admin_role.id, user_id=user_with_permission.id))
    
    # Assign Permission -> Role
    session.add(PermissionAssignment(permission_id=perm_admin.id, entity_type="Role", entity_id=admin_role.id))
    
    # Assign Permission -> User
    session.add(PermissionAssignment(permission_id=perm_user.id, entity_type="User", entity_id=user_with_permission.id))
    
    await session.commit()
    
    yield
    
    # Cleanup implied by session rollback/function scope usually, but if needed add here


@pytest.mark.asyncio
async def test_check_user_access_role_based(session, user_with_permission, setup_permissions):
    # Should be allowed via AdminRole -> admin_access -> /api/admin
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/admin", "GET", session
    )
    assert is_allowed is True


@pytest.mark.asyncio
async def test_check_user_access_direct(session, user_with_permission, setup_permissions):
    # Should be allowed via UserPermission -> user_access -> /api/user
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/user", "POST", session
    )
    assert is_allowed is True


@pytest.mark.asyncio
async def test_check_user_access_public(session, user_with_permission, setup_permissions):
    # Should be allowed because validate=False
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/public", "GET", session
    )
    assert is_allowed is True


@pytest.mark.asyncio
async def test_check_user_access_denied(session, user_with_permission, setup_permissions):
    # Should be denied (no permission)
    # We need a route that is validated but user has no permission
    route_secure = Route(name="/api/secure", validate=True)
    session.add(route_secure)
    await session.commit()
    
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/secure", "GET", session
    )
    assert is_allowed is False
    
    # Also undefined route
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/undefined", "GET", session
    )
    assert is_allowed is False


@pytest.mark.asyncio
async def test_api_permissions_flow(client: AsyncClient, session, user_with_permission):
    # 1. Create Category
    resp = await client.post("/permissions/categories", json={"name": "API Test"})
    assert resp.status_code == 200
    cat_id = resp.json()["id"]
    
    # 2. Create Permission
    resp = await client.post("/permissions/", json={"name": "api_test_perm", "permission_category_id": cat_id})
    assert resp.status_code == 200
    perm_id = resp.json()["id"]
    
    # 3. Create Route
    resp = await client.post("/routes/", json={"name": "/api/test-flow", "validate": True})
    assert resp.status_code == 200
    route_id = resp.json()["id"]
    
    # 4. Link Permission to Route
    resp = await client.post(f"/permissions/{perm_id}/routes", json={"permission_id": perm_id, "route_id": route_id})
    assert resp.status_code == 200
    
    # 5. Assign Permission to User
    resp = await client.post("/permissions/assign", json={"user_id": user_with_permission.id, "permission_id": perm_id})
    assert resp.status_code == 200
    
    # 6. Verify Access Service check
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/test-flow", "GET", session
    )
    assert is_allowed is True
