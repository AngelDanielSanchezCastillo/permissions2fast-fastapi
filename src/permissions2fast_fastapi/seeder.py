import json
import logging
import os
from typing import Dict, Any, Optional

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from .models.role_model import Role
from .models.permission_category_model import PermissionCategory
from .models.permission_model import Permission
from .models.route_model import Route
from .models.permission_route_model import PermissionRoute
from .models.permission_assignment_model import PermissionAssignment

logger = logging.getLogger(__name__)

def load_default_seed_data() -> Dict[str, Any]:
    """Load default seed data from the JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "seeders", "seed_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

DEFAULT_SEED_DATA = load_default_seed_data()


async def seed_rbac_from_json(
    session: AsyncSession,
    seed_data: Optional[Dict[str, Any]] = None,
    route_prefix: str = ""
) -> None:
    """
    Seed initial RBAC configuration (Role, Category, Permissions, Routes).
    
    Args:
        session: Database session.
        seed_data: Optional JSON-like dictionary with the seed data. If not provided,
                   uses the DEFAULT_SEED_DATA which contains the package's internal routes.
        route_prefix: Optional prefix to prepend to all created routes (e.g. "/api/v1").
    """
    if seed_data is None:
        seed_data = DEFAULT_SEED_DATA

    role_data = seed_data.get("role")
    category_data = seed_data.get("category")
    permissions_data = seed_data.get("permissions", [])

    if not role_data or not category_data:
        raise ValueError("Seed data must include 'role' and 'category'.")

    # 1. Ensure Role exists
    result = await session.exec(select(Role).where(Role.name == role_data["name"]))
    admin_role = result.one_or_none()
    if not admin_role:
        admin_role = Role(**role_data)
        session.add(admin_role)
        await session.commit()
        await session.refresh(admin_role)
        logger.info(f"Created role: {admin_role.name}")
    else:
        logger.info(f"Role already exists: {admin_role.name}")

    # 2. Ensure Category exists
    result = await session.exec(select(PermissionCategory).where(PermissionCategory.name == category_data["name"]))
    admin_category = result.one_or_none()
    if not admin_category:
        admin_category = PermissionCategory(**category_data)
        session.add(admin_category)
        await session.commit()
        await session.refresh(admin_category)
        logger.info(f"Created category: {admin_category.name}")
    else:
        logger.info(f"Category already exists: {admin_category.name}")

    # 3. Create permissions and link to routes
    for perm_info in permissions_data:
        # Check if permission exists
        result = await session.exec(select(Permission).where(Permission.name == perm_info["name"]))
        perm = result.one_or_none()
        if not perm:
            perm = Permission(
                name=perm_info["name"],
                permission_category_id=admin_category.id
            )
            session.add(perm)
            await session.commit()
            await session.refresh(perm)
            logger.info(f"Created permission: {perm.name}")
        
        # Assign permission to Admin Role if not already assigned
        result = await session.exec(
            select(PermissionAssignment).where(
                PermissionAssignment.permission_id == perm.id,
                PermissionAssignment.entity_type == "Role",
                PermissionAssignment.entity_id == admin_role.id
            )
        )
        if not result.one_or_none():
            assignment = PermissionAssignment(
                permission_id=perm.id,
                entity_type="Role",
                entity_id=admin_role.id
            )
            session.add(assignment)
            await session.commit()
            logger.info(f"Assigned permission {perm.name} to role {admin_role.name}")

        # Ensure routes exist and are linked to permission
        for raw_route in perm_info.get("routes", []):
            route_path = f"{route_prefix}{raw_route}"
            
            result = await session.exec(select(Route).where(Route.name == route_path))
            route = result.one_or_none()
            
            if not route:
                route = Route(name=route_path)
                session.add(route)
                await session.commit()
                await session.refresh(route)
                logger.info(f"Created route: {route.name}")
            
            # Link route to permission if not linked
            result = await session.exec(
                select(PermissionRoute).where(
                    PermissionRoute.permission_id == perm.id,
                    PermissionRoute.route_id == route.id
                )
            )
            if not result.one_or_none():
                perm_route = PermissionRoute(
                    permission_id=perm.id,
                    route_id=route.id
                )
                session.add(perm_route)
                await session.commit()
                logger.info(f"Linked route {route.name} to permission {perm.name}")
