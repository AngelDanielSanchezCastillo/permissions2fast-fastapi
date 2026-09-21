"""
permissions2fast_fastapi.migrations - package-owned Alembic chain.

The ``auth`` lane is ordered oauth -> permissions-global -> tenant2fast-auth
(FK-proven, design D6 of the Metal ERP change ``alembic-2fast``): the
permissions chain owns the seven RBAC tables that reference ``users`` and
the oauth tables, so it must run AFTER the oauth chain on the same database.

This package's models inherit ``oauth2fast_fastapi.models.AuthModel``, so
their tables live in oauth2fast's shared ``MetaData`` (design D9): the
``ChainSpec`` passes that shared metadata and the ownership filter keeps
autogenerate and upgrades scoped to this chain's own tables.

Registration mirrors the ``register_seeder`` idiom: importing this module
(which the top-level ``permissions2fast_fastapi/__init__.py`` does)
registers the chain spec under the ``"auth"`` lane.
"""

from oauth2fast_fastapi.models.bases import metadata
from pgsqlasync2fast_fastapi import ChainSpec, register_chain

#: Tables this chain owns (design D9 ownership filter).
PERMISSIONS_OWNED_TABLES = frozenset(
    {
        "roles",
        "permissions",
        "permission_categories",
        "routes",
        "role_users",
        "permission_assignments",
        "permission_routes",
    }
)

permissions_chain = ChainSpec(
    package="permissions2fast_fastapi",
    script_path="migrations/permissions-global",
    version_table="alembic_version_permissions",
    target_metadata=metadata,
    owned_tables=PERMISSIONS_OWNED_TABLES,
)

register_chain("auth", permissions_chain)

__all__ = ["PERMISSIONS_OWNED_TABLES", "permissions_chain"]