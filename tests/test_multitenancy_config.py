import pytest

# Example configuration showing the required keys in .env
EXAMPLE_DOTENV = """
# RBAC Tenant & Caching Settings
PERMISSIONS_ENABLE_TENANCY=True
PERMISSIONS_REDIS_RBAC_ENABLED=True

# Redis connection details
PERMISSIONS_REDIS__HOST=localhost
PERMISSIONS_REDIS__PORT=6379
PERMISSIONS_REDIS__DB=0
# PERMISSIONS_REDIS__PASSWORD=your_secure_password
"""

@pytest.mark.asyncio
async def test_env_parsing_shows_redis_and_tenancy_flags():
    """
    Dummy test just to illustrate where the new config surface area lives.
    """
    from permissions2fast_fastapi.settings import PermissionsSettings
    import os
    
    os.environ["PERMISSIONS_ENABLE_TENANCY"] = "True"
    os.environ["PERMISSIONS_REDIS_RBAC_ENABLED"] = "False"
    
    settings = PermissionsSettings()
    
    assert settings.enable_tenancy is True
    assert settings.redis_rbac_enabled is False
    
    # Cleanup
    del os.environ["PERMISSIONS_ENABLE_TENANCY"]
    del os.environ["PERMISSIONS_REDIS_RBAC_ENABLED"]
