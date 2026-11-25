"""Rebuild RBAC inbound FKs with ON UPDATE CASCADE (seed-id adoption).

Enables ``adopt_explicit_ids`` to rewrite RBAC primary keys in place; the
database cascades the change to role_user/permission links and any other
child FK.
"""

from alembic import op

revision = "c9d0e1f2a3b4"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None

RBAC_TABLES = ("roles", "permissions", "permission_categories")


def upgrade() -> None:
    from pgsqlasync2fast_fastapi.migrations.fk_cascade import (
        upgrade_fks_to_on_update_cascade,
    )

    upgrade_fks_to_on_update_cascade(op.get_bind(), RBAC_TABLES)


def downgrade() -> None:
    from pgsqlasync2fast_fastapi.migrations.fk_cascade import (
        downgrade_fks_to_no_action,
    )

    downgrade_fks_to_no_action(op.get_bind(), RBAC_TABLES)
