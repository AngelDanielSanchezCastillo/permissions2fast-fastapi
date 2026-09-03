# Route Seeding (Global Manifest)

`permissions2fast-fastapi` supports seeding **routes, permission_routes, and
role_users** rows on the auth database for application-level (GLOBAL) routes.
This complements the base seeder (`categories`/`roles`/`permissions`) with a
manifest-driven route grant layer.

The seeding is driven by an **app-owned manifest** and is **idempotent**
(insert-if-missing by route `id`), so re-running it never duplicates rows.

## Scope

- **GLOBAL plane** (this package): routes are configuration-level and follow
  the auth DB RBAC. Roles here are `Admin`, `SuperAdmin`, `Manager`, `User`.
- The TENANT plane (per-tenant RBAC) is owned by `tenants2fast-fastapi`; tenant
  routes without explicit roles default to the tenant `OWNER` role.

> There is **no OWNER role** at the global plane. Every global route MUST
> declare its explicit config roles. A global route without roles gets no
> default and must be reviewed before it is considered secure.

## Manifest Contract

The app declares guarded routes as a list of route specs. Each spec carries the
HTTP method, path pattern, optional permission, the explicit roles allowed, and
a profile set (`dev`/`prod`):

```
RouteSpec(method, path, permission, roles: list[str], profile: set[str])
```

Seed rules:

1. **Profile filter** — only rows whose `profile` set contains the active
   profile are seeded; dev-only roles are excluded when running `prod`.
2. **Insert-if-missing by id** — existing route/permission_route/role_user rows
   are left untouched; only missing e rows are inserted.
3. **Override extends base** — app-level registration extends the base tables
   (roles/permissions from the package) instead of replacing them, preserving
   the package's auto-registered seed data.

## Example

```python
from backend.app.rbac_route_manifest import RouteSpec, seed_routes_links

manifest = [
    RouteSpec(
        method="GET",
        path="/users",
        permission=None,
        roles=["Admin", "Manager"],
        profile={"dev", "prod"},
    ),
    # dev-only route
    RouteSpec(
        method="DELETE",
        path="/debug/cache",
        permission=None,
        roles=["Admin"],
        profile={"dev"},
    ),
]

summary = await seed_routes_links(conn, session, manifest, profile="prod")
```

After seeding with `profile="prod"`, the `DELETE /debug/cache` dev-only row is
**not** present (excluded by the profile filter).

## Integration

- Run after migrations and the base `seed_all(profile)` at app startup.
- Use the pgsqlasync2fast override primitive (`register_seeder(mode=...)`) when
  an app needs to extend base tables without replacing them.
