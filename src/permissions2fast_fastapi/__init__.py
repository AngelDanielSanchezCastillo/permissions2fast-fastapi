"""
permissions2fast-fastapi

Complete RBAC (Role-Based Access Control) system for FastAPI applications.
Provides role management, permission checking, and user-role assignments.
"""

__version__ = "0.1.0"

from .models.role_model import Role
from .models.permission_model import Permission
from .models.permission_category_model import PermissionCategory
from .models.route_model import Route
from .models.user_role_model import UserRole
from .models.permission_assignment_model import PermissionAssignment
from .models.permission_route_model import PermissionRoute

__all__ = [
    "Role",
    "Permission",
    "PermissionCategory",
    "Route",
    "UserRole",
    "PermissionAssignment",
    "PermissionRoute",
]
