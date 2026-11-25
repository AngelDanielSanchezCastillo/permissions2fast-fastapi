"""
permissions2fast-fastapi

Complete RBAC (Role-Based Access Control) system for FastAPI applications.
Provides role management, permission checking, and user-role assignments.
"""

# Import seeder components from pgsqlasync2fast-fastapi
from pgsqlasync2fast_fastapi import SeederConfig, register_seeder

from .__version__ import __version__
from .models.permission_assignment_model import PermissionAssignment
from .models.permission_category_model import PermissionCategory
from .models.permission_model import Permission
from .models.permission_route_model import PermissionRoute
from .models.role_model import Role
from .models.role_user_model import RoleUser
from .models.route_model import Route

# GLOBAL route+link seeding (RBAC standardization D2)
from .services.route_manifest import load_route_manifest, validate_route_manifest
from .services.route_seeder import RouteSpec, seed_global_routes


def get_seeder_config() -> "PackageSeederConfig":
    """
    Return this package's seeder configuration.

    The package ships its own boot seeders (categories, roles, permissions)
    and registers them with pgsqlasync2fast so any consuming app gets them
    automatically when ``RUN_SEEDERS=true``.
    """
    # Path relative to this file: seeders/manifest.json
    import os

    from pgsqlasync2fast_fastapi import PackageSeederConfig

    current_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(current_dir, "seeders", "manifest.json")

    return PackageSeederConfig(
        package_name="permissions2fast-fastapi",
        manifest_path=manifest_path,
        model_registry={
            "categories": PermissionCategory,
            "roles": Role,
            "permissions": Permission,
        },
        connection="auth",
        priority=60,
    )


# Import seeder components from pgsqlasync2fast-fastapi
from pgsqlasync2fast_fastapi import PackageSeederConfig, register_package_seeders

# Register this package's seeders at import time.
register_package_seeders(get_seeder_config())

# One-off migration helper (uniformize existing DB ids to uuid7 literals).
from .seeders_migration import adopt_explicit_seed_ids, build_seeder_engine  # noqa: E402

# Register the permissions-global Alembic chain under the "auth" lane at
# import time (mirrors the register_seeder idiom; alembic-2fast change).
from . import migrations as _migrations  # noqa: F401

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
    # GLOBAL route+link seeding (RBAC standardization D2)
    "RouteSpec",
    "seed_global_routes",
    "load_route_manifest",
    "validate_route_manifest",
    # Seeder system
    "get_seeder_config",
    # Seed-data migrations (uuid7 uniformization)
    "adopt_explicit_seed_ids",
    "build_seeder_engine",
]