"""Add indexes and explicit RESTRICT FK constraints to cancellation_records

Findings addressed:
  - #8: Add indexes on FK columns (item_id, cancelled_by_id, other_party_id)
        to prevent full-table scans on audit-log queries.
  - #5: Declare explicit ON DELETE RESTRICT on all three FK constraints.

Design rationale — why RESTRICT and not CASCADE or SET NULL:
  Users are anonymised in-place (never hard-deleted) so the RESTRICT on user
  FKs never fires during legitimate GDPR deletion. Item rows for unsold
  listings are cleaned up in Python (CancellationRecord.query.filter_by(
  item_id=item.id).delete()) before the item row is deleted, so RESTRICT
  on item_id never fires during GDPR deletion either.

  RESTRICT serves purely as a database-level guard rail: any future code
  that attempts a hard-delete without first handling the audit log will be
  stopped by the DB rather than silently wiping records. This preserves the
  audit log for partner reporting and dispute resolution while keeping the
  system GDPR-compliant (anonymised user rows retain university_domain and
  role data needed for aggregate reporting without exposing PII).

Revision ID: f8a9b0c1d2e3
Revises: e1a2b3c4d5e6
Create Date: 2026-06-20 14:00:00.000000
"""
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'f8a9b0c1d2e3'
down_revision = 'e1a2b3c4d5e6'
branch_labels = None
depends_on = None

# Define naming convention to map and resolve anonymous constraints on SQLite
naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade():
    # Inspect existing indexes to avoid OperationalError on dev DBs where they may already exist
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('cancellation_records')]

    # ── Indexes on FK columns ─────────────────────────────────────────────
    if 'ix_cancellation_records_item_id' not in existing_indexes:
        op.create_index(
            op.f('ix_cancellation_records_item_id'),
            'cancellation_records', ['item_id'], unique=False
        )
    if 'ix_cancellation_records_cancelled_by_id' not in existing_indexes:
        op.create_index(
            op.f('ix_cancellation_records_cancelled_by_id'),
            'cancellation_records', ['cancelled_by_id'], unique=False
        )
    if 'ix_cancellation_records_other_party_id' not in existing_indexes:
        op.create_index(
            op.f('ix_cancellation_records_other_party_id'),
            'cancellation_records', ['other_party_id'], unique=False
        )

    # ── Re-declare FK constraints with explicit ON DELETE RESTRICT ────────
    with op.batch_alter_table('cancellation_records', schema=None, naming_convention=naming_convention) as batch_op:
        # Drop existing anonymous FK constraints using names derived from naming_convention.
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_item_id_items'),
            type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_cancelled_by_id_users'),
            type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_other_party_id_users'),
            type_='foreignkey'
        )
        # Re-create with explicit RESTRICT.
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_item_id_items'),
            'items', ['item_id'], ['id'],
            ondelete='RESTRICT'
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_cancelled_by_id_users'),
            'users', ['cancelled_by_id'], ['id'],
            ondelete='RESTRICT'
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_other_party_id_users'),
            'users', ['other_party_id'], ['id'],
            ondelete='RESTRICT'
        )


def downgrade():
    # Restore FK constraints without ON DELETE clause and drop indexes.
    with op.batch_alter_table('cancellation_records', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_other_party_id_users'),
            type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_cancelled_by_id_users'),
            type_='foreignkey'
        )
        batch_op.drop_constraint(
            batch_op.f('fk_cancellation_records_item_id_items'),
            type_='foreignkey'
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_item_id_items'),
            'items', ['item_id'], ['id']
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_cancelled_by_id_users'),
            'users', ['cancelled_by_id'], ['id']
        )
        batch_op.create_foreign_key(
            batch_op.f('fk_cancellation_records_other_party_id_users'),
            'users', ['other_party_id'], ['id']
        )

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('cancellation_records')]

    if 'ix_cancellation_records_other_party_id' in existing_indexes:
        op.drop_index(op.f('ix_cancellation_records_other_party_id'), table_name='cancellation_records')
    if 'ix_cancellation_records_cancelled_by_id' in existing_indexes:
        op.drop_index(op.f('ix_cancellation_records_cancelled_by_id'), table_name='cancellation_records')
    if 'ix_cancellation_records_item_id' in existing_indexes:
        op.drop_index(op.f('ix_cancellation_records_item_id'), table_name='cancellation_records')
