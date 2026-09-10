"""
GLOBAL route+link seeder (permissions2fast-fastapi).

RBAC standardization D2: the GLOBAL route / permission_routes / roles inserter
lives here so a client (app) manifest of guarded routes can be seeded into the
auth DB idempotently, instead of the app hand-rolling its own inserter.

GLOBAL rules:
- Route natural key is `name` (e.g. ``"POST /register-user"``).
- explicit config roles only — there is **no OWNER role** at the global plane.
  A global route without roles gets no role assignment and must be reviewed.
- every role declared on a route with a ``permission`` gets a
  ``PermissionAssignment`` grant (``entity_type="Role"``, UQ-protected).
- profile-aware: dev-only routes are excluded when running ``prod``.
- idempotent via the shared ``pgsqlasync2fast.insert_if_missing`` primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pgsqlasync2fast_fastapi.seeder import insert_if_missing

from permissions2fast_fastapi.models.permission_assignment_model import (
    PermissionAssignment,
)
from permissions2fast_fastapi.models.permission_model import Permission
from permissions2fast_fastapi.models.permission_route_model import PermissionRoute
from permissions2fast_fastapi.models.role_model import Role
from permissions2fast_fastapi.models.route_model import Route

# The default permission category id used when a route declares a permission
# but the app did not pre-create it. Safe because permissions are unique by
# name; the category row is a lightweight grouping bucket.
_DEFAULT_PERMISSION_CATEGORY_ID = 1


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """Declares ONE guarded GLOBAL route for seeding."""

    method: str
    path: str
    permission: str | None = None
    roles: list[str] = field(default_factory=list)
    profile: set[str] = field(default_factory=lambda: {"dev", "prod"})


async def seed_global_routes(
    session,
    manifest: list[RouteSpec],
    profile: str = "prod",
) -> dict[str, int]:
    """
    Seed GLOBAL routes, permission_routes and roles idempotently.

    Args:
        session: SQLModel AsyncSession bound to the auth DB.
        manifest: list of RouteSpec to consider.
        profile: active profile; specs whose ``profile`` does not contain it
            are skipped.

    Returns:
        A summary dict: ``{"routes", "links", "roles", "grants", "errors"}``
        counts.
    """
    summary: dict[str, int] = {
        "routes": 0,
        "links": 0,
        "roles": 0,
        "grants": 0,
        "errors": 0,
    }

    for spec in manifest:
        if profile not in spec.profile:
            continue
        try:
            grants = await _seed_global_route(session, spec)
            summary["routes"] += 1
            if spec.permission:
                summary["links"] += 1
            summary["roles"] += len(spec.roles)
            summary["grants"] += grants
        except Exception:
            summary["errors"] += 1

    return summary


async def _seed_global_route(session, spec: RouteSpec) -> int:
    """Insert/update one GLOBAL route (route + permission link + roles + grants).

    Returns the number of role→permission grants created for this route.
    """
    route_name = f"{spec.method} {spec.path}"
    route = await insert_if_missing(
        session, Route, lookup={"name": route_name}, defaults={"is_active": True}
    )

    grants = 0
    if spec.permission:
        permission = await insert_if_missing(
            session,
            Permission,
            lookup={"name": spec.permission},
            defaults={
                "permission_category_id": _DEFAULT_PERMISSION_CATEGORY_ID,
                "is_active": True,
            },
        )
        await insert_if_missing(
            session,
            PermissionRoute,
            lookup={"permission_id": permission.id, "route_id": route.id},
        )

    for role_name in spec.roles:
        role = await insert_if_missing(
            session,
            Role,
            lookup={"name": role_name},
            defaults={"is_active": True},
        )
        if spec.permission:
            await insert_if_missing(
                session,
                PermissionAssignment,
                lookup={
                    "permission_id": permission.id,
                    "entity_type": "Role",
                    "entity_id": role.id,
                },
            )
            grants += 1

    return grants
