# Route Seeding (Global Manifest)

`permissions2fast-fastapi` supports seeding **routes, permission_routes,
roles, and role→permission grants** rows on the auth database for
application-level (GLOBAL) routes.
This complements the base seeder (`categories`/`roles`/`permissions`) with a
manifest-driven route grant layer.

The seeding is driven by an **app-owned manifest** and is **idempotent**
(insert-if-missing by route natural key `name`), so re-running it never
duplicates rows.

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
2. **Insert-if-missing by natural key** — existing route rows
   (keyed by `name` = `"METHOD path"`), permission_routes, roles and grants are
   left untouched; only missing rows are inserted (via the shared
   `pgsqlasync2fast.insert_if_missing` primitive).
3. **Grants** — when a route declares a `permission`, every role in its
   `roles` list receives a `PermissionAssignment` row with
   `entity_type="Role"` and `entity_id=<role id>`. The existing
   `uq_permission_assignment` unique constraint makes grant seeding
   idempotent: re-running the seeder never duplicates a grant. Routes without
   a permission create no grants.
4. **No OWNER default** — a global route with no explicit `roles` gets no role
   assignment and must be reviewed.

## Example

```python
from permissions2fast_fastapi import RouteSpec, seed_global_routes

manifest = [
    RouteSpec(
        method="GET",
        path="/tenants/control",
        permission="tenants_control",
        roles=["Admin"],
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

summary = await seed_global_routes(session, manifest, profile="prod")
```

After seeding with `profile="prod"`, the `DELETE /debug/cache` dev-only row is
**not** present (excluded by the profile filter). `summary` returns
`{"routes", "links", "roles", "grants", "errors"}` counts — `grants` is one
per role→permission pair created for seeded routes.

## Integration

- Run after migrations and the base `seed_all(profile)` at app startup.
- Use the pgsqlasync2fast override primitive (`register_seeder(mode=...)`) when
  an app needs to extend base tables without replacing them.
