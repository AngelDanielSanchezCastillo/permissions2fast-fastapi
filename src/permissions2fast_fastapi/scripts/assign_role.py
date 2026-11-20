"""
Bootstrap script to assign a role to a user.

Creates the role if it doesn't exist. The user must already exist
(created via oauth2fast's create_admin or register endpoint).

Usage::

    python -m permissions2fast_fastapi.scripts.assign_role \\
        --email admin@example.com \\
        --role admin
"""

import argparse
import asyncio
import sys

from oauth2fast_fastapi.database import get_db_engine, shutdown_database, startup_database
from oauth2fast_fastapi.models.user_model import User
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.role_model import Role
from ..services.role_service import assign_user_role, create_role
from rbac2fast_core.schemas.role_schema import RoleCreate


async def assign_role_to_user(
    session: AsyncSession,
    *,
    email: str,
    role_name: str,
) -> dict:
    """
    Assign a role to a user, creating the role if it doesn't exist.

    Args:
        session: AsyncSession for database operations.
        email: User email address.
        role_name: Role name to assign (case-sensitive, lowercase recommended).

    Returns:
        Dict with user_email, role_name, role_created, and user_id.

    Raises:
        ValueError: If user not found.
    """
    # Find user by email
    result = await session.exec(select(User).where(User.email == email))
    user = result.one_or_none()

    if not user:
        raise ValueError(f"User with email '{email}' not found")

    # Find or create role
    result = await session.exec(select(Role).where(Role.name == role_name))
    role = result.one_or_none()

    role_created = False
    if not role:
        role_data = RoleCreate(
            name=role_name,
            description=f"Role: {role_name}",
        )
        role = await create_role(role_data, session)
        role_created = True

    # Assign role to user
    await assign_user_role(user.id, role.id, session)

    return {
        "user_email": email,
        "user_id": user.id,
        "role_name": role_name,
        "role_id": role.id,
        "role_created": role_created,
    }


async def _main_async(args: argparse.Namespace) -> None:
    """Async entry point for the CLI."""
    await startup_database()

    engine = get_db_engine("auth")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            result = await assign_role_to_user(
                session,
                email=args.email,
                role_name=args.role,
            )

            print("Role assigned successfully:")
            print(f"  User: {result['user_email']} (ID: {result['user_id']})")
            print(f"  Role: {result['role_name']} (ID: {result['role_id']})")
            if result["role_created"]:
                print("  Note: Role was created (did not exist previously)")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            if "already has this role" in str(e):
                print(f"User {args.email} already has role '{args.role}'")
            else:
                print(f"Error assigning role: {e}", file=sys.stderr)
                sys.exit(1)

    await shutdown_database()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Assign a role to a user (creates role if it doesn't exist).",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the user",
    )
    parser.add_argument(
        "--role",
        required=True,
        help="Role name to assign (e.g., admin, user, manager)",
    )
    args = parser.parse_args()

    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
