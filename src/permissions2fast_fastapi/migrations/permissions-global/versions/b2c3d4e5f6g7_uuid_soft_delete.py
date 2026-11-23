"""uuid_soft_delete

Revision ID: b2c3d4e5f6g7
Revises: 0001
Create Date: 2026-11-23 12:00:00.000000

Migrate all permissions2fast tables from BigInteger to UUID v7.
Add soft-delete columns (deleted_at, deleted_by) to all tables.
Remove is_active columns from roles and routes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate all permissions tables from BigInteger to UUID.
    
    Order matters due to foreign key dependencies:
    1. permission_categories (no FKs)
    2. roles (no FKs)
    3. routes (no FKs)
    4. permissions (FK to permission_categories)
    5. role_users (FK to roles, FK to users)
    6. permission_routes (FK to permissions, FK to routes)
    7. permission_assignments (FK to permissions)
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 1: permission_categories (no FKs)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('permission_categories', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_categories', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('permission_categories', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE permission_categories SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('permission_categories', 'id_uuid', nullable=False)
    
    op.drop_constraint('permission_categories_pkey', 'permission_categories')
    op.drop_column('permission_categories', 'id')
    op.alter_column('permission_categories', 'id_uuid', new_column_name='id')
    op.create_primary_key('permission_categories_pkey', 'permission_categories', ['id'])
    op.create_index(op.f('ix_permission_categories_id'), 'permission_categories', ['id'], unique=False)
    op.create_index(op.f('ix_permission_categories_deleted_at'), 'permission_categories', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 2: roles (no FKs, remove is_active)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('roles', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('roles', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('roles', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE roles SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('roles', 'id_uuid', nullable=False)
    
    op.drop_constraint('roles_pkey', 'roles')
    op.drop_column('roles', 'is_active')
    op.drop_column('roles', 'id')
    op.alter_column('roles', 'id_uuid', new_column_name='id')
    op.create_primary_key('roles_pkey', 'roles', ['id'])
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_deleted_at'), 'roles', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 3: routes (no FKs, remove is_active)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('routes', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('routes', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('routes', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE routes SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('routes', 'id_uuid', nullable=False)
    
    op.drop_constraint('routes_pkey', 'routes')
    op.drop_column('routes', 'is_active')
    op.drop_column('routes', 'id')
    op.alter_column('routes', 'id_uuid', new_column_name='id')
    op.create_primary_key('routes_pkey', 'routes', ['id'])
    op.create_index(op.f('ix_routes_id'), 'routes', ['id'], unique=False)
    op.create_index(op.f('ix_routes_deleted_at'), 'routes', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 4: permissions (FK to permission_categories)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('permissions', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permissions', sa.Column('permission_category_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permissions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('permissions', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE permissions SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('permissions', 'id_uuid', nullable=False)
    
    # Backfill FK: permission_category_id
    op.execute("""
        UPDATE permissions
        SET permission_category_id_uuid = (
            SELECT pc.id FROM permission_categories pc
            WHERE pc.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM permission_categories
                ) sub
                WHERE sub.rn = permissions.permission_category_id
            )
        )
        WHERE permission_category_id_uuid IS NULL
    """)
    op.alter_column('permissions', 'permission_category_id_uuid', nullable=False)
    
    op.drop_constraint('permissions_permission_category_id_fkey', 'permissions', type_='foreignkey')
    op.drop_constraint('permissions_pkey', 'permissions')
    op.drop_index(op.f('ix_permissions_id'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_permission_category_id'), table_name='permissions')
    
    op.drop_column('permissions', 'id')
    op.drop_column('permissions', 'permission_category_id')
    op.alter_column('permissions', 'id_uuid', new_column_name='id')
    op.alter_column('permissions', 'permission_category_id_uuid', new_column_name='permission_category_id')
    
    op.create_primary_key('permissions_pkey', 'permissions', ['id'])
    op.create_foreign_key('permissions_permission_category_id_fkey', 'permissions', 'permission_categories', ['permission_category_id'], ['id'])
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_permission_category_id'), 'permissions', ['permission_category_id'], unique=False)
    op.create_index(op.f('ix_permissions_deleted_at'), 'permissions', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 5: role_users (FK to roles, FK to users)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('role_users', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('role_users', sa.Column('user_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('role_users', sa.Column('role_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('role_users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('role_users', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE role_users SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('role_users', 'id_uuid', nullable=False)
    
    # Backfill FKs
    op.execute("""
        UPDATE role_users
        SET role_id_uuid = (
            SELECT r.id FROM roles r
            WHERE r.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM roles
                ) sub
                WHERE sub.rn = role_users.role_id
            )
        )
        WHERE role_id_uuid IS NULL
    """)
    op.execute("""
        UPDATE role_users
        SET user_id_uuid = (
            SELECT u.id FROM users u
            WHERE u.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM users
                ) sub
                WHERE sub.rn = role_users.user_id
            )
        )
        WHERE user_id_uuid IS NULL
    """)
    op.alter_column('role_users', 'user_id_uuid', nullable=False)
    op.alter_column('role_users', 'role_id_uuid', nullable=False)
    
    op.drop_constraint('role_users_role_id_fkey', 'role_users', type_='foreignkey')
    op.drop_constraint('role_users_user_id_fkey', 'role_users', type_='foreignkey')
    op.drop_constraint('role_users_pkey', 'role_users')
    op.drop_index(op.f('ix_role_users_id'), table_name='role_users')
    op.drop_index(op.f('ix_role_users_user_id'), table_name='role_users')
    op.drop_index(op.f('ix_role_users_role_id'), table_name='role_users')
    
    op.drop_column('role_users', 'id')
    op.drop_column('role_users', 'user_id')
    op.drop_column('role_users', 'role_id')
    op.alter_column('role_users', 'id_uuid', new_column_name='id')
    op.alter_column('role_users', 'user_id_uuid', new_column_name='user_id')
    op.alter_column('role_users', 'role_id_uuid', new_column_name='role_id')
    
    op.create_primary_key('role_users_pkey', 'role_users', ['id'])
    op.create_foreign_key('role_users_role_id_fkey', 'role_users', 'roles', ['role_id'], ['id'])
    op.create_foreign_key('role_users_user_id_fkey', 'role_users', 'users', ['user_id'], ['id'])
    op.create_index(op.f('ix_role_users_id'), 'role_users', ['id'], unique=False)
    op.create_index(op.f('ix_role_users_user_id'), 'role_users', ['user_id'], unique=False)
    op.create_index(op.f('ix_role_users_role_id'), 'role_users', ['role_id'], unique=False)
    op.create_index(op.f('ix_role_users_deleted_at'), 'role_users', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 6: permission_routes (FK to permissions, FK to routes)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('permission_routes', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_routes', sa.Column('permission_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_routes', sa.Column('route_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_routes', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('permission_routes', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE permission_routes SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('permission_routes', 'id_uuid', nullable=False)
    
    # Backfill FKs
    op.execute("""
        UPDATE permission_routes
        SET permission_id_uuid = (
            SELECT p.id FROM permissions p
            WHERE p.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM permissions
                ) sub
                WHERE sub.rn = permission_routes.permission_id
            )
        )
        WHERE permission_id_uuid IS NULL
    """)
    op.execute("""
        UPDATE permission_routes
        SET route_id_uuid = (
            SELECT r.id FROM routes r
            WHERE r.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM routes
                ) sub
                WHERE sub.rn = permission_routes.route_id
            )
        )
        WHERE route_id_uuid IS NULL
    """)
    op.alter_column('permission_routes', 'permission_id_uuid', nullable=False)
    op.alter_column('permission_routes', 'route_id_uuid', nullable=False)
    
    op.drop_constraint('permission_routes_permission_id_fkey', 'permission_routes', type_='foreignkey')
    op.drop_constraint('permission_routes_route_id_fkey', 'permission_routes', type_='foreignkey')
    op.drop_constraint('permission_routes_pkey', 'permission_routes')
    op.drop_index(op.f('ix_permission_routes_id'), table_name='permission_routes')
    op.drop_index(op.f('ix_permission_routes_permission_id'), table_name='permission_routes')
    op.drop_index(op.f('ix_permission_routes_route_id'), table_name='permission_routes')
    
    op.drop_column('permission_routes', 'id')
    op.drop_column('permission_routes', 'permission_id')
    op.drop_column('permission_routes', 'route_id')
    op.alter_column('permission_routes', 'id_uuid', new_column_name='id')
    op.alter_column('permission_routes', 'permission_id_uuid', new_column_name='permission_id')
    op.alter_column('permission_routes', 'route_id_uuid', new_column_name='route_id')
    
    op.create_primary_key('permission_routes_pkey', 'permission_routes', ['id'])
    op.create_foreign_key('permission_routes_permission_id_fkey', 'permission_routes', 'permissions', ['permission_id'], ['id'])
    op.create_foreign_key('permission_routes_route_id_fkey', 'permission_routes', 'routes', ['route_id'], ['id'])
    op.create_index(op.f('ix_permission_routes_id'), 'permission_routes', ['id'], unique=False)
    op.create_index(op.f('ix_permission_routes_permission_id'), 'permission_routes', ['permission_id'], unique=False)
    op.create_index(op.f('ix_permission_routes_route_id'), 'permission_routes', ['route_id'], unique=False)
    op.create_index(op.f('ix_permission_routes_deleted_at'), 'permission_routes', ['deleted_at'], unique=False)
    
    # ═══════════════════════════════════════════════════════════════════════
    # STEP 7: permission_assignments (FK to permissions)
    # ═══════════════════════════════════════════════════════════════════════
    op.add_column('permission_assignments', sa.Column('id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_assignments', sa.Column('permission_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_assignments', sa.Column('entity_id_uuid', sa.Uuid(), nullable=True))
    op.add_column('permission_assignments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('permission_assignments', sa.Column('deleted_by', sa.Uuid(), nullable=True))
    
    op.execute("UPDATE permission_assignments SET id_uuid = gen_random_uuid() WHERE id_uuid IS NULL")
    op.alter_column('permission_assignments', 'id_uuid', nullable=False)
    
    # Backfill FKs
    op.execute("""
        UPDATE permission_assignments
        SET permission_id_uuid = (
            SELECT p.id FROM permissions p
            WHERE p.id = (
                SELECT id_uuid FROM (
                    SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                    FROM permissions
                ) sub
                WHERE sub.rn = permission_assignments.permission_id
            )
        )
        WHERE permission_id_uuid IS NULL
    """)
    # entity_id is polymorphic - backfill from users or roles depending on entity_type
    op.execute("""
        UPDATE permission_assignments
        SET entity_id_uuid = (
            CASE 
                WHEN entity_type = 'User' THEN (
                    SELECT u.id FROM users u
                    WHERE u.id = (
                        SELECT id_uuid FROM (
                            SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                            FROM users
                        ) sub
                        WHERE sub.rn = permission_assignments.entity_id
                    )
                )
                WHEN entity_type = 'Role' THEN (
                    SELECT r.id FROM roles r
                    WHERE r.id = (
                        SELECT id_uuid FROM (
                            SELECT id_uuid, ROW_NUMBER() OVER (ORDER BY id_uuid) as rn
                            FROM roles
                        ) sub
                        WHERE sub.rn = permission_assignments.entity_id
                    )
                )
                ELSE NULL
            END
        )
        WHERE entity_id_uuid IS NULL
    """)
    op.alter_column('permission_assignments', 'permission_id_uuid', nullable=False)
    op.alter_column('permission_assignments', 'entity_id_uuid', nullable=False)
    
    op.drop_constraint('permission_assignments_permission_id_fkey', 'permission_assignments', type_='foreignkey')
    op.drop_constraint('permission_assignments_pkey', 'permission_assignments')
    op.drop_index(op.f('ix_permission_assignments_id'), table_name='permission_assignments')
    op.drop_index(op.f('ix_permission_assignments_permission_id'), table_name='permission_assignments')
    op.drop_index(op.f('ix_permission_assignments_entity_id'), table_name='permission_assignments')
    
    op.drop_column('permission_assignments', 'id')
    op.drop_column('permission_assignments', 'permission_id')
    op.drop_column('permission_assignments', 'entity_id')
    op.alter_column('permission_assignments', 'id_uuid', new_column_name='id')
    op.alter_column('permission_assignments', 'permission_id_uuid', new_column_name='permission_id')
    op.alter_column('permission_assignments', 'entity_id_uuid', new_column_name='entity_id')
    
    op.create_primary_key('permission_assignments_pkey', 'permission_assignments', ['id'])
    op.create_foreign_key('permission_assignments_permission_id_fkey', 'permission_assignments', 'permissions', ['permission_id'], ['id'])
    op.create_index(op.f('ix_permission_assignments_id'), 'permission_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_permission_assignments_permission_id'), 'permission_assignments', ['permission_id'], unique=False)
    op.create_index(op.f('ix_permission_assignments_entity_id'), 'permission_assignments', ['entity_id'], unique=False)
    op.create_index(op.f('ix_permission_assignments_deleted_at'), 'permission_assignments', ['deleted_at'], unique=False)


def downgrade() -> None:
    """Reverse migration: UUID back to BigInteger.
    
    WARNING: Destructive. UUID→integer mapping uses row numbering.
    In practice, prefer a full database rebuild over downgrading.
    """
    # This is a complex downgrade. For simplicity, we'll just note that
    # downgrading is not fully supported. A full database rebuild is recommended.
    raise NotImplementedError(
        "Downgrade from UUID to BigInteger is not supported. "
        "Please perform a full database rebuild instead."
    )
