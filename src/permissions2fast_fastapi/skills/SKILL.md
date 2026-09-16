---
name: permissions2fast-fastapi
description: "Trigger: working on or with permissions2fast-fastapi. App-level RBAC on the auth DB for oauth2fast-fastapi: Role/Permission/Route models, has_permission deps, seeders. Prevails over the 2fast-handbook base skill for this package."
license: MIT
metadata:
  author: AngelDanielSanchezCastillo
  version: "2.1"
---

## Purpose

App-level role-based access control over the **auth database**, on top of
`oauth2fast_fastapi` and `rbac2fast-core` schemas. NOT per-tenant (unlike
tenants2fast's separate `tenant_metadata` registry).

## Import quirk

- Dist `permissions2fast-fastapi` → import `permissions2fast_fastapi` (dash→underscore only).
- **Routers are not top-level**: `from permissions2fast_fastapi.routers import permissions_router, roles_router, routes_router` (README says otherwise).
- Importing the package auto-registers a seeder as a side effect.

## Public API

- `has_permission(permission_route=None, method=None)` — first arg is a **route path**, never a permission name; no arg auto-detects via `request.scope["route"].path` (template such as `/roles/user/{user_id}`).
- `has_role(role_name)`; both chain `get_current_verified_user` + `get_auth_session` (403 in Spanish when denied).
- Routers (`/permissions`, `/roles`, `/routes`) are ALL gated with `Depends(has_permission())` — a fresh DB returns 403 until routes, permissions, and grants are seeded.
- Services are module functions: `access_service.check_user_access(user_id, route_path, method, session)`, `role_service`, `permission_service`, `route_service`.

## Architecture

- ALL models (`Role`, `Permission`, `PermissionCategory`, `Route`, `RoleUser`, `PermissionAssignment`, `PermissionRoute`) extend `AuthModel` → land on the shared auth metadata; create tables with `AuthModel.metadata.create_all`. No separate registry.
- Joins: `role_users` (role↔user), `permission_routes` (M2M link), polymorphic `permission_assignments` (`entity_type` ∈ {"User","Role"}).
- `Role` has NO relationship to `User` — hand-join via `RoleUser`.
- `tools2fast_fastapi` (`APIResponse`, `ErrorDetail`) is required by routers/schemas but **not declared in pyproject** — undeclared trap.

## Wiring

```python
app.include_router(permissions_router)
app.include_router(roles_router)
app.include_router(routes_router)
```

No middleware. Requires the oauth2fast deps and the `auth` connection registered
in the pgsqlasync2fast manager.

## Access semantics (default deny, 2 traps)

1. Route not found → **deny**. But `Route.is_active=False` → **allow (bypass)** — deactivating makes a route public.
2. Direct-user + role permissions are **UNIONed** — no deny-wins, no negative permissions (differs from tenants2fast).
- HTTP `method` is **ignored** in the `check_user_access` DB path; it only matters in `permission_cache.check_route_access`, which is NOT wired in.
- Redis key `rbac:{user_id}:global`, TTL 300, active only when `PERMISSIONS_REDIS_RBAC_ENABLED=true`. Two Redis modules (`redis_client` vs `permission_cache`) use different keys/clients — footgun.
- Cache invalidates on assignment ops only, NOT on role/permission/route writes — invalidate manually.

## Settings

`PermissionsSettings`, prefix `PERMISSIONS_`, nested `__`: `REDIS__HOST/PORT/DB/PASSWORD`,
`REDIS_RBAC_ENABLED` (default False), `CACHE_TTL_SECONDS` (300). Reads `./.env` from CWD.

## Seeders

`get_seeder_config()` → SeederConfig(connection `"auth"`, **not** tenant seeder,
priority 60, manifest `categories`/`roles`/`permissions`, idempotent by `id`).
`seed_rbac_from_json()` does **NOT** exist. Route seeding creates the
role→permission grants (`PermissionAssignment`, `entity_type="Role"`).

## Route seeding (global manifest)

A global **route manifest** can seed `routes`, `permission_routes`, `roles`,
and role→permission **grants** on the auth DB for app-level (GLOBAL) routes.
This is the RBAC standardization D2 home of the GLOBAL route+link inserter —
the app slims to a declarative manifest and calls the package seeder instead
of re-implementing.

- `RouteSpec(method, path, permission=None, roles=[], profile={"dev","prod"})`
  and `seed_global_routes(session, manifest, profile="prod")` are exported from
  the top-level package. Route natural key is `name` = `"METHOD path"`.
- Every global route declares its explicit config roles
  (Admin/SuperAdmin/Manager/User) — there is **no OWNER default** at the global
  plane (OWNER exists only in the tenant plane of tenants2fast). A global route
  without roles gets no role assignment and must be reviewed.
- **Grants**: when a route declares a `permission`, every role in its `roles`
  list receives a `PermissionAssignment` row with `entity_type="Role"` and
  `entity_id=<role id>`, protected by the existing
  `uq_permission_assignment` unique constraint — re-running the seeder never
  duplicates grants. Routes without a permission create no grants.
- Profile-aware: dev-only routes are excluded when running `prod`.
- Idempotent via the shared `pgsqlasync2fast.insert_if_missing` primitive
  (insert-if-missing by `name`, never duplicated on re-run), NOT the package's
  `register_seeder` orchestrator (that base seeder only covers
  categories/roles/permissions).
- `summary` returns `{"routes", "links", "roles", "grants", "errors"}` counts.
- See `docs/route-seeding.md` for the manifest contract and example.

## Conventions

- Spanish response messages; envelope `{success, error_type, message, ...}` from tools2fast `APIResponse`.
- No Alembic: schema via `AuthModel.metadata.create_all`.

## Golden rule (inherited)

Follow the 2fast-handbook base skill for layout/versioning/naming/README/commits/release.
Local edits are fine; NEVER bump/publish on your own — prepare the exact command and hand it to the developer.