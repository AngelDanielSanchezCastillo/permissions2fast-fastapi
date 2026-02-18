"""
permissions2fast-fastapi

Complete RBAC (Role-Based Access Control) system for FastAPI applications.
Provides role management, permission checking, and user-role assignments.
"""

__version__ = "0.1.0"

from .models.role_level_model import RoleLevel
from .models.role_model import Role
from .models.user_role_model import UserRole
from .models.role_permission_model import RolePermission
from .models.user_permission_model import UserPermission

__all__ = [
    "RoleLevel",
    "Role",
    "UserRole",
    "RolePermission",
    "UserPermission",
]
