import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from permissions2fast_fastapi.seeder import seed_rbac_from_json, DEFAULT_SEED_DATA
from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.permission_category_model import PermissionCategory
from permissions2fast_fastapi.models.permission_model import Permission
from permissions2fast_fastapi.models.route_model import Route
from permissions2fast_fastapi.models.permission_route_model import PermissionRoute
from permissions2fast_fastapi.models.permission_assignment_model import PermissionAssignment


@pytest.mark.asyncio
async def test_seed_rbac_creates_all_entities(session: AsyncSession):
    """Test that the seeder creates the default role, category, permissions, and routes."""
    # Seed the DB
    await seed_rbac_from_json(session)

    # 1. Check Role
    role = await session.exec(select(Role).where(Role.name == DEFAULT_SEED_DATA["role"]["name"]))
    role = role.one_or_none()
    assert role is not None
    assert role.description == DEFAULT_SEED_DATA["role"]["description"]

    # 2. Check Category
    category = await session.exec(select(PermissionCategory).where(PermissionCategory.name == DEFAULT_SEED_DATA["category"]["name"]))
    category = category.one_or_none()
    assert category is not None

    # 3. Check Permissions and Routes
    for expected_perm in DEFAULT_SEED_DATA["permissions"]:
        # Verify Permission
        perm = await session.exec(select(Permission).where(Permission.name == expected_perm["name"]))
        perm = perm.one_or_none()
        assert perm is not None
        assert perm.permission_category_id == category.id

        # Verify Assignment to Admin role
        assignment = await session.exec(
            select(PermissionAssignment).where(
                PermissionAssignment.permission_id == perm.id,
                PermissionAssignment.entity_type == "Role",
                PermissionAssignment.entity_id == role.id
            )
        )
        assert assignment.one_or_none() is not None

        # Verify Routes
        for raw_route in expected_perm["routes"]:
            # Route should exist
            route = await session.exec(select(Route).where(Route.name == raw_route))
            route = route.one_or_none()
            assert route is not None

            # Route should be linked to permission
            perm_route = await session.exec(
                select(PermissionRoute).where(
                    PermissionRoute.permission_id == perm.id,
                    PermissionRoute.route_id == route.id
                )
            )
            assert perm_route.one_or_none() is not None


@pytest.mark.asyncio
async def test_seed_rbac_is_idempotent(session: AsyncSession):
    """Test that running the seeder multiple times doesn't blow up or duplicate data."""
    # First run
    await seed_rbac_from_json(session)
    # Second run
    await seed_rbac_from_json(session)

    # Count roles
    roles = await session.exec(select(Role))
    assert len(list(roles.all())) == 1

    # Count categories
    categories = await session.exec(select(PermissionCategory))
    assert len(list(categories.all())) == 1

    # Count permissions
    permissions = await session.exec(select(Permission))
    assert len(list(permissions.all())) == len(DEFAULT_SEED_DATA["permissions"])


@pytest.mark.asyncio
async def test_seed_rbac_with_custom_prefix(session: AsyncSession):
    """Test that the seeder prefixes routes correctly when asked."""
    prefix = "/api/v1"
    await seed_rbac_from_json(session, route_prefix=prefix)

    expected_routes = []
    for p in DEFAULT_SEED_DATA["permissions"]:
        expected_routes.extend(p["routes"])
    
    # Verify that paths include prefix
    all_routes = await session.exec(select(Route))
    db_routes = [r.name for r in all_routes.all()]
    
    for expected_r in expected_routes:
        assert f"{prefix}{expected_r}" in db_routes
