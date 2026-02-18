import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.user_role_model import UserRole
from permissions2fast_fastapi.models.role_permission_model import RolePermission
from permissions2fast_fastapi.models.user_permission_model import UserPermission
from permissions2fast_fastapi.services import access_service
from permissions2fast_fastapi.utils import permission_cache

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
    # Assign Role to User
    user_role = UserRole(user_id=user_with_permission.id, role_id=admin_role.id)
    session.add(user_role)
    
    # Add Permission to Role
    role_perm = RolePermission(
        role_id=admin_role.id,
        route_path="/api/admin",
        method="GET",
        is_allowed=True
    )
    session.add(role_perm)
    
    # Add Direct User Permission
    user_perm = UserPermission(
        user_id=user_with_permission.id,
        route_path="/api/user-specific",
        method="POST",
        is_allowed=True
    )
    session.add(user_perm)
    
    await session.commit()
    
    # Clear cache for this user just in case
    await permission_cache.invalidate_user_cache(user_with_permission.id)
    
    yield
    
    # Cleanup cache
    await permission_cache.invalidate_user_cache(user_with_permission.id)


@pytest.mark.asyncio
async def test_check_user_access_role_based(session, user_with_permission, admin_role, setup_permissions):
    # Should be allowed via AdminRole
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/admin", "GET", session
    )
    assert is_allowed is True
    
    # Check cache population
    cached_perms = await permission_cache.get_user_permissions(user_with_permission.id)
    assert cached_perms is not None
    assert any(p["route_path"] == "/api/admin" for p in cached_perms)


@pytest.mark.asyncio
async def test_check_user_access_direct(session, user_with_permission, setup_permissions):
    # Should be allowed via UserPermission
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/user-specific", "POST", session
    )
    assert is_allowed is True


@pytest.mark.asyncio
async def test_check_user_access_denied(session, user_with_permission, setup_permissions):
    # Should be denied (no permission)
    is_allowed = await access_service.check_user_access(
        user_with_permission.id, "/api/unknown", "GET", session
    )
    assert is_allowed is False


@pytest.mark.asyncio
async def test_api_permissions_router_crud(client: AsyncClient, session, user_with_permission):
    # Create Permission via API
    # Note: Requires auth. Since we mocked get_auth_session, we need to ensure 
    # the endpoint dependencies (get_current_active_user) are also handled if we test protected routes.
    # Our conftest only overrides get_auth_session. 
    # permissions_router endpoints depend on get_auth_session mostly, BUT they might require auth?
    # Checking permissions_router.py... it uses `Depends(get_auth_session)`.
    # It does NOT seems to enforce `get_current_user` in the snippets I saw!
    # Wait, let me check the file content again.
    # Step 25: `async def create_permission(..., session: AsyncSession = Depends(get_auth_session))`
    # It does NOT seem to look for `get_current_user`. This might be a security hole if not protected by a global dependency or router dependency.
    # The user manual says "Use the provided dependencies to restrict access".
    # But the management endpoints themselves should probably be protected?
    # Assuming they are public for now or protected at app level.
    
    response = await client.post(
        "/permissions/",
        json={
            "user_id": user_with_permission.id,
            "route_path": "/api/new-perm",
            "method": "DELETE",
            "is_allowed": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["route_path"] == "/api/new-perm"
    assert data["method"] == "DELETE"
    
    perm_id = data["id"]
    
    # Get Permission
    response = await client.get(f"/permissions/{perm_id}")
    assert response.status_code == 200
    assert response.json()["id"] == perm_id

