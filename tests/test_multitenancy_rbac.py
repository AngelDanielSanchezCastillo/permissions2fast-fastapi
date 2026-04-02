import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import FastAPI, Depends, Request, APIRouter
from httpx import AsyncClient, ASGITransport

from permissions2fast_fastapi.models.tenant_model import Tenant
from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.services import role_service
from permissions2fast_fastapi.dependencies import has_role, get_tenant_id


# Dummy FastAPI app for this specific file testing
app = FastAPI()
router = APIRouter()

@router.get("/global-admin")
async def global_admin_route(user = Depends(has_role("admin"))):
    return {"message": "Hello Global Admin"}

@router.get("/tenant-admin")
async def tenant_admin_route(user = Depends(has_role("tenant_admin"))):
    return {"message": "Hello Tenant Admin"}

app.include_router(router)


@pytest.fixture
async def tenant(session: AsyncSession) -> Tenant:
    t = Tenant(name="Test Tenant", schema_name="tenant1", is_active=True)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return t


@pytest.fixture
async def admin_role(session: AsyncSession) -> Role:
    r = Role(name="admin", description="Global Admin")
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


@pytest.fixture
async def tenant_admin_role(session: AsyncSession) -> Role:
    r = Role(name="tenant_admin", description="Admin for a specific tenant")
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


@pytest.mark.asyncio
async def test_global_rbac_fallback(session: AsyncSession, test_user, admin_role):
    """
    Test that when ENABLE_TENANCY=False (default in tests), assigning a global role works and permits access.
    """
    from permissions2fast_fastapi.settings import settings
    # Ensure Tenancy is OFF
    settings.enable_tenancy = False
    
    # Assign global role
    await role_service.assign_user_role(test_user.id, admin_role.id, session)
    
    # Mock auth session and active user for this test app
    from oauth2fast_fastapi.dependencies import get_auth_session, get_current_verified_user
    app.dependency_overrides[get_auth_session] = lambda: session
    app.dependency_overrides[get_current_verified_user] = lambda: test_user
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Request should succeed because user has the global admin role
        response = await ac.get("/global-admin")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello Global Admin"}
        
        # User doesn't have tenant_admin globally
        response2 = await ac.get("/tenant-admin")
        assert response2.status_code == 403
        
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_tenant_rbac_isolation(session: AsyncSession, test_user, tenant, tenant_admin_role):
    """
    Test that when ENABLE_TENANCY=True, assigning a role in a tenant grants access to that tenant specifically.
    """
    from permissions2fast_fastapi.settings import settings
    # Enable Tenancy Simulation
    settings.enable_tenancy = True
    
    # Assign role in specific tenant
    await role_service.assign_user_role(test_user.id, tenant_admin_role.id, session, tenant_id=tenant.id)
    
    from oauth2fast_fastapi.dependencies import get_auth_session, get_current_verified_user
    app.dependency_overrides[get_auth_session] = lambda: session
    app.dependency_overrides[get_current_verified_user] = lambda: test_user
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        
        # 1. Provide NO tenant header. Should fail since role is scoped to a tenant.
        response_no_tenant = await ac.get("/tenant-admin")
        assert response_no_tenant.status_code == 403

        # 2. Provide the CORRECT tenant header. Should succeed.
        response_correct_tenant = await ac.get(
            "/tenant-admin",
            headers={"X-Tenant-ID": str(tenant.id)}
        )
        assert response_correct_tenant.status_code == 200
        
        # 3. Provide an INCORRECT tenant header. Should fail (isolation).
        response_wrong_tenant = await ac.get(
            "/tenant-admin",
            headers={"X-Tenant-ID": "999"}
        )
        assert response_wrong_tenant.status_code == 403
        
    app.dependency_overrides.clear()
    
    # Cleanup setting
    settings.enable_tenancy = False
