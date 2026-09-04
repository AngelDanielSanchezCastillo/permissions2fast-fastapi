"""
Tests for the GLOBAL route+link seeder (permissions2fast-fastapi).

RBAC standardization D2: the GLOBAL route/permission_routes/roles inserter
lives HERE (permissions2fast) so a client manifest of guarded routes can be
seeded into the auth DB idempotently (insert-if-missing by natural key; the
Route key is `name`, e.g. "POST /register-user").

GLOBAL rules:
- explicit config roles only (no OWNER default); a route with no roles gets
  no role assignment (must be reviewed).
- profile-aware (dev/prod): PROD must not receive dev-only routes.

Run with:
  cd /Volumes/Desarrollo/Repos/Github/permissions2fast-fastapi \
    && uv run pytest tests/test_route_seeder.py -v
"""

from __future__ import annotations

import pytest
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlmodel.ext.asyncio.session import AsyncSession

from oauth2fast_fastapi.models.bases import AuthModel


@compiles(BigInteger, "sqlite")
def _compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"


DB_URL = "sqlite+aiosqlite:///:memory:"


async def _auth_engine():
    # Force model registration on the shared AuthModel metadata
    from permissions2fast_fastapi.models.route_model import Route  # noqa: F401
    from permissions2fast_fastapi.models.permission_model import Permission  # noqa: F401
    from permissions2fast_fastapi.models.permission_route_model import (  # noqa: F401
        PermissionRoute,
    )
    from permissions2fast_fastapi.models.role_model import Role  # noqa: F401
    from permissions2fast_fastapi.models.permission_category_model import (  # noqa: F401
        PermissionCategory,
    )

    engine = create_async_engine(DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AuthModel.metadata.create_all)
    return engine


def _spec(method, path, permission, roles, profile):
    from permissions2fast_fastapi.services.route_seeder import RouteSpec

    return RouteSpec(
        method=method,
        path=path,
        permission=permission,
        roles=roles,
        profile=profile,
    )


@pytest.mark.asyncio
async def test_seed_global_routes_inserts_route_permission_role():
    """Global scope inserts route + permission + role into auth DB idempotently."""
    from sqlalchemy import text

    from permissions2fast_fastapi.services.route_seeder import seed_global_routes
    from permissions2fast_fastapi.models.permission_category_model import (
        PermissionCategory,
    )

    engine = await _auth_engine()
    async with AsyncSession(engine) as session:
        # A category is required by the permission FK.
        session.add(PermissionCategory(name="config"))
        await session.flush()

        manifest = [
            _spec(
                "GET",
                "/tenants/control",
                "tenants_control",
                ["Admin"],
                {"dev", "prod"},
            )
        ]
        summary = await seed_global_routes(session, manifest, "dev")
        await session.commit()

        async with engine.connect() as conn:
            routes = (await conn.execute(text("SELECT name FROM routes"))).all()
            perms = (await conn.execute(text("SELECT name FROM permissions"))).all()
            roles = (await conn.execute(text("SELECT name FROM roles"))).all()

        assert [r[0] for r in routes] == ["GET /tenants/control"]
        assert [p[0] for p in perms] == ["tenants_control"]
        assert [r[0] for r in roles] == ["Admin"]
        assert summary["routes"] == 1

        # --- Idempotency: second call does not duplicate ---
        await seed_global_routes(session, manifest, "dev")
        await session.commit()
        async with engine.connect() as conn:
            n_routes = (await conn.execute(text("SELECT COUNT(*) FROM routes"))).scalar()
            n_perms = (
                await conn.execute(text("SELECT COUNT(*) FROM permissions"))
            ).scalar()
            n_roles = (await conn.execute(text("SELECT COUNT(*) FROM roles"))).scalar()
        assert n_routes == 1
        assert n_perms == 1
        assert n_roles == 1

    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_global_routes_prod_excludes_dev_only_route():
    """prod must not receive dev-only routes (profile-aware)."""
    from sqlalchemy import text

    from permissions2fast_fastapi.services.route_seeder import seed_global_routes

    engine = await _auth_engine()
    async with AsyncSession(engine) as session:
        manifest = [
            _spec("DELETE", "/debug/cache", None, ["Admin"], {"dev"}),
            _spec("GET", "/tenants/control", "tenants_control", ["Admin"], {"dev", "prod"}),
        ]
        summary = await seed_global_routes(session, manifest, "prod")
        await session.commit()

        async with engine.connect() as conn:
            rows = (await conn.execute(text("SELECT name FROM routes"))).all()
        names = {r[0] for r in rows}

        assert "/debug/cache" not in " ".join(names)  # dev-only route excluded
        assert "GET /tenants/control" in names
        assert summary["routes"] == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_global_route_without_roles_gets_no_role():
    """GLOBAL route without roles -> no role assignment (no OWNER default)."""
    from sqlalchemy import text

    from permissions2fast_fastapi.services.route_seeder import seed_global_routes

    engine = await _auth_engine()
    async with AsyncSession(engine) as session:
        manifest = [
            _spec("POST", "/open-to-review", None, [], {"dev", "prod"}),
        ]
        summary = await seed_global_routes(session, manifest, "dev")
        await session.commit()

        async with engine.connect() as conn:
            routes = (await conn.execute(text("SELECT name FROM routes"))).all()
            roles = (await conn.execute(text("SELECT name FROM roles"))).all()

        assert [r[0] for r in routes] == ["POST /open-to-review"]
        # No roles created for a global route without explicit roles
        assert roles == []
        assert summary["roles"] == 0
    await engine.dispose()
