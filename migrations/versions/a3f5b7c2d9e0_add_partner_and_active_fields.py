"""Add partner and active fields

Revision ID: a3f5b7c2d9e0
Revises: feddbe5c7f51
Create Date: 2026-06-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a3f5b7c2d9e0'
down_revision = 'feddbe5c7f51'
branch_labels = None
depends_on = None


def upgrade():
    # User model alterations
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=20), nullable=False, server_default=sa.text('student')))
        batch_op.add_column(sa.Column('partner_university', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
        batch_op.alter_column('phone_number',
               existing_type=sa.String(length=20),
               nullable=True)

    # Item model alterations
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('university_domain', sa.String(length=100), nullable=True))

    # Data migration: copy university_domain from users to items.
    # The WHERE guard prevents NULLs if seller_id is missing or references a deleted user.
    op.execute("""
        UPDATE items
        SET university_domain = (
            SELECT university_domain FROM users WHERE users.id = items.seller_id
        )
        WHERE seller_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM users WHERE users.id = items.seller_id)
    """)


def downgrade():
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_column('university_domain')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('phone_number',
               existing_type=sa.String(length=20),
               nullable=False)
        batch_op.drop_column('is_active')
        batch_op.drop_column('partner_university')
        batch_op.drop_column('role')
