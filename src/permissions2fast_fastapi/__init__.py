"""
permissions2fast-fastapi

Complete RBAC (Role-Based Access Control) system for FastAPI applications.
Provides role management, permission checking, and user-role assignments.
"""

from .__version__ import __version__

from .models.role_model import Role
from .models.permission_model import Permission
from .models.permission_category_model import PermissionCategory
from .models.route_model import Route
from .models.role_user_model import RoleUser
from .models.permission_assignment_model import PermissionAssignment
from .models.permission_route_model import PermissionRoute

# Import seeder components from pgsqlasync2fast-fastapi
from pgsqlasync2fast_fastapi import SeederConfig, register_seeder

# Import models for seeding (used by the orchestrator via model_classes)
from .models.role_model import Role
from .models.permission_category_model import PermissionCategory
from .models.permission_model import Permission


def get_seeder_config():
    """
    Return the SeederConfig for permissions2fast-fastapi.

    This uses the orchestrator's generic seeding with model_classes and fk_field_mapping.
    No custom seed() function needed - the orchestrator handles all seeding logic.
    """
    # Path relative to this file: seeders/manifest.json
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(current_dir, "seeders", "manifest.json")

    return SeederConfig(
        connection_name="auth",
        manifest_path=manifest_path,
        is_tenant_seeder=False,
        priority=60,
        package_name="permissions2fast-fastapi",
        seed_fn=None,  # Use orchestrator's generic seeding with model_classes
        model_classes={
            "categories": PermissionCategory,
            "roles": Role,
            "permissions": Permission,
        },
        fk_field_mapping={
            "permissions": {"category_id": "permission_category_id"},
        },
    )


# Register this package's seeder with the orchestrator
register_seeder(get_seeder_config())


__all__ = [
    "__version__",
    # Models
    "Role",
    "Permission",
    "PermissionCategory",
    "Route",
    "RoleUser",
    "PermissionAssignment",
    "PermissionRoute",
    # Seeder system
    "get_seeder_config",
]