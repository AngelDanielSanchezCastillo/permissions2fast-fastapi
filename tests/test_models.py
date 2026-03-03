import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.user_role_model import UserRole
from permissions2fast_fastapi.models.permission_category_model import PermissionCategory
from permissions2fast_fastapi.models.permission_model import Permission
from permissions2fast_fastapi.models.route_model import Route
from permissions2fast_fastapi.models.permission_route_model import PermissionRoute
from permissions2fast_fastapi.models.permission_assignment_model import PermissionAssignment

# User and Role are now imported from conftest.py fixtures or created here if using specific models

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
    user_role = UserRole(
        user_id=test_user.id,
        role_id=test_role.id
    )
    session.add(user_role)
    await session.commit()
    await session.refresh(user_role)
    
    assert user_role.role_id == test_role.id
    assert user_role.user_id == test_user.id


@pytest.mark.asyncio
async def test_create_permission_structure(session):
    # 1. Create Category
    category = PermissionCategory(name="User Management")
    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    # 2. Create Permission
    permission = Permission(
        name="create_user",
        permission_category_id=category.id
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    
    # 3. Create Route
    route = Route(name="/api/users", is_active=True)
    session.add(route)
    await session.commit()
    await session.refresh(route)
    
    # 4. Link Permission and Route
    perm_route = PermissionRoute(
        permission_id=permission.id,
        route_id=route.id
    )
    session.add(perm_route)
    await session.commit()
    await session.refresh(perm_route)
    
    assert perm_route.id is not None
    assert perm_route.permission_id == permission.id
    assert perm_route.route_id == route.id


@pytest.mark.asyncio
async def test_assign_permission_to_role(session, test_role):
    # Assume permission exists (mocking or creating minimal)
    # Create required dependencies
    category = PermissionCategory(name="Role Test Cat")
    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    permission = Permission(name="role_permission", permission_category_id=category.id)
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    
    # Assign to Role
    role_perm = PermissionAssignment(
        permission_id=permission.id,
        entity_type="Role",
        entity_id=test_role.id
    )
    session.add(role_perm)
    await session.commit()
    await session.refresh(role_perm)
    
    assert role_perm.permission_id == permission.id
    assert role_perm.entity_type == "Role"
    assert role_perm.entity_id == test_role.id

@pytest.mark.asyncio
async def test_assign_permission_to_user(session, test_user):
    # Create required dependencies
    category = PermissionCategory(name="User Test Cat")
    session.add(category)
    await session.commit()
    await session.refresh(category)
    
    permission = Permission(name="user_permission", permission_category_id=category.id)
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    
    # Assign to User
    user_perm = PermissionAssignment(
        permission_id=permission.id,
        entity_type="User",
        entity_id=test_user.id
    )
    session.add(user_perm)
    await session.commit()
    await session.refresh(user_perm)
    
    assert user_perm.permission_id == permission.id
    assert user_perm.entity_type == "User"
    assert user_perm.entity_id == test_user.id
