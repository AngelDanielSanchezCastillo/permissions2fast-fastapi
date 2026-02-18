import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.role_permission_model import RolePermission
from permissions2fast_fastapi.models.user_role_model import UserRole
from permissions2fast_fastapi.models.user_permission_model import UserPermission

# User and Role are now imported from conftest.py fixtures


@pytest.mark.asyncio
async def test_create_role(session):
    role = Role(name="Admin", description="Administrator")
    session.add(role)
    await session.commit()
    await session.refresh(role)
    
    assert role.id is not None
    assert role.name == "Admin"


@pytest.mark.asyncio
async def test_assign_role_to_user(session, test_user, test_role):
    user_role = UserRole(user_id=test_user.id, role_id=test_role.id)
    session.add(user_role)
    await session.commit()
    await session.refresh(user_role)
    
    assert user_role.id is not None
    assert user_role.user_id == test_user.id
    assert user_role.role_id == test_role.id


@pytest.mark.asyncio
async def test_role_permission(session, test_role):
    perm = RolePermission(
        role_id=test_role.id,
        route_path="/api/test",
        method="GET",
        is_allowed=True
    )
    session.add(perm)
    await session.commit()
    await session.refresh(perm)
    
    assert perm.id is not None
    assert perm.role_id == test_role.id
    assert perm.route_path == "/api/test"


@pytest.mark.asyncio
async def test_unique_role_permission(session, test_role):
    # Create first permission
    perm1 = RolePermission(
        role_id=test_role.id,
        route_path="/api/unique",
        method="POST",
        is_allowed=True
    )
    session.add(perm1)
    await session.commit()
    
    # Try to create duplicate
    perm2 = RolePermission(
        role_id=test_role.id,
        route_path="/api/unique",
        method="POST",
        is_allowed=False 
    )
    session.add(perm2)
    
    with pytest.raises(IntegrityError):
        await session.commit()
    
    await session.rollback()
