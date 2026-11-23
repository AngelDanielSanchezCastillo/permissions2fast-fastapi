"""uuid_soft_delete

Revision ID: b2c3d4e5f6g7
Revises: 0001
Create Date: 2026-11-23 12:00:00.000000

Migrate all permissions2fast tables from BigInteger to UUID v7.
Add soft-delete columns (deleted_at, deleted_by) to all tables.
Remove is_active columns from roles and routes.

Two-phase, FK-safe (pgsqlasync2fast 0.6.2 helpers):
1. prepare PKs/FKs while old integer columns still exist (join-backfill via
   parent.id_uuid / old integer id) — no fragile ROW_NUMBER mapping.
2. finalize: drop child FKs → swap PKs → swap FKs → recreate constraints.

Special cases:
- role_users.user_id → users.id belongs to the auth/oauth DB (already UUID):
  converted with no local backfill.
- permission_assignments.entity_id is polymorphic: 'Role' backfills from the
  local roles table; 'User' refers to the external auth users (no backfill).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from pgsqlasync2fast_fastapi.migration_helpers import (
    add_soft_delete_columns_alembic,
    finalize_uuid_alembic,
    prepare_fk_uuid_alembic,
    prepare_pk_uuid_alembic,
)


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that carry is_active (replaced by soft-delete).
_IS_ACTIVE_TABLES = ("roles", "routes")

# All permissions2fast tables, parents before children.
_ALL_TABLES = (
    "permission_categories",
    "roles",
    "routes",
    "permissions",
    "role_users",
    "permission_routes",
    "permission_assignments",
)

# Internal (same-DB) FK relations: (child, fk_column, parent).
_INTERNAL_FKS = (
    ("permissions", "permission_category_id", "permission_categories"),
    ("role_users", "role_id", "roles"),
    ("permission_routes", "permission_id", "permissions"),
    ("permission_routes", "route_id", "routes"),
    ("permission_assignments", "permission_id", "permissions"),
)


def upgrade() -> None:
    """Upgrade schema: bigint → UUID + soft-delete (two-phase, FK-safe)."""
    # --- Soft-delete columns + drop is_active -----------------------------
    for table in _ALL_TABLES:
        add_soft_delete_columns_alembic(op, table)
    for table in _IS_ACTIVE_TABLES:
        op.drop_column(table, 'is_active')

    # --- Phase 1: prepare PKs and internal FKs (old int columns kept) -----
    for table in _ALL_TABLES:
        prepare_pk_uuid_alembic(op, table)

    prepare_fk_uuid_alembic(
        op, "permissions", "permission_category_id", "permission_categories",
        nullable=False,
    )
    for child, fk_column, parent in _INTERNAL_FKS:
        if child == "permissions" and fk_column == "permission_category_id":
            continue  # already prepared above
        prepare_fk_uuid_alembic(op, child, fk_column, parent, nullable=False)

    # role_users.user_id → auth users.id (external, already UUID): no backfill.
    op.add_column('role_users', sa.Column('user_id_uuid', sa.Uuid(), nullable=True))

    # permission_assignments.entity_id (polymorphic): backfill only Roles.
    op.add_column(
        'permission_assignments',
        sa.Column('entity_id_uuid', sa.Uuid(), nullable=True),
    )
    op.execute(
        """
        UPDATE permission_assignments AS pa
        SET entity_id_uuid = roles.id_uuid
        FROM roles
        WHERE pa.entity_type = 'Role' AND roles.id = pa.entity_id
          AND pa.entity_id_uuid IS NULL
        """
    )

    # --- Phase 2: finalize (drop child FKs → swap PKs → swap FKs) ---------
    finalize_uuid_alembic(
        op,
        pk_tables=_ALL_TABLES,
        fk_relations=[
            *_INTERNAL_FKS,
            ("role_users", "user_id", "users"),
        ],
        unique_constraints=[
            ("role_users", "uq_user_role", ("user_id", "role_id")),
        ],
    )

    # --- entity_id is not an FK: swap it manually after the PK/FK pass ----
    op.drop_index(op.f('ix_permission_assignments_entity_id'), table_name='permission_assignments')
    op.drop_column('permission_assignments', 'entity_id')
    op.alter_column('permission_assignments', 'entity_id_uuid', new_column_name='entity_id')
    op.create_index(
        op.f('ix_permission_assignments_entity_id'),
        'permission_assignments',
        ['entity_id'],
        unique=False,
    )
    # Recreate the polymorphic unique constraint dropped with the old column.
    op.create_unique_constraint(
        'uq_permission_assignment',
        'permission_assignments',
        ['permission_id', 'entity_type', 'entity_id'],
    )


def downgrade() -> None:
    """Reverse migration: UUID back to BigInteger.

    WARNING: Destructive. UUID→integer mapping uses row numbering.
    In practice, prefer a full database rebuild over downgrading.
    """
    raise NotImplementedError(
        "Downgrade from UUID to BigInteger is not supported. "
        "Please perform a full database rebuild instead."
    )
