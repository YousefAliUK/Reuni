"""Add description check constraint to items table

This migration applies the CHECK constraint on items.description length to
the live database. The constraint was defined in the original 0001_initial
migration but was incorrectly placed as a positional argument to sa.Column()
rather than as a table-level constraint — SQLAlchemy silently ignored it,
meaning the constraint was never actually created in the database.

The Python-level validation in items.py (max 2000 chars) already prevents
over-length descriptions from being submitted. This migration adds a DB-level
belt-and-suspenders guard for any direct SQL inserts.

Revision ID: e1a2b3c4d5e6
Revises: b1134cd8e355
Create Date: 2026-06-20 12:52:00.000000
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'b1134cd8e355'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for SQLite compatibility (local dev environment).
    # On PostgreSQL (Railway production) this creates the constraint directly.
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_items_description_length',
            'length(description) <= 2000'
        )


def downgrade():
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_constraint('ck_items_description_length', type_='check')
