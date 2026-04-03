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
from .models.user_role_model import UserRole
from .models.permission_assignment_model import PermissionAssignment
from .models.permission_route_model import PermissionRoute
from .seeder import seed_rbac_from_json, DEFAULT_SEED_DATA

__all__ = [
    "__version__",
    "Role",
    "Permission",
    "PermissionCategory",
    "Route",
    "UserRole",
    "PermissionAssignment",
    "PermissionRoute",
    "seed_rbac_from_json",
    "DEFAULT_SEED_DATA",
]
