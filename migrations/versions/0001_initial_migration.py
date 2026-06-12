"""Initial migration — create users and items tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── users ──────────────────────────────────────────────────────────────
    # Base columns only.  Subsequent migrations add:
    #   68298d73f726 → is_verified, university_domain, email_verification_*
    #   a3f5b7c2d9e0 → role, partner_university, is_active (phone_number → nullable)
    #   b1134cd8e355 → deletion_pending_until, kg_saved_total FLOAT→Numeric
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('kg_saved_total', sa.Float(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number'),
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    # ── items ───────────────────────────────────────────────────────────────
    # Base columns only.  Subsequent migrations add:
    #   a3f5b7c2d9e0 → university_domain
    #   b1134cd8e355 → price/kg_saved FLOAT→Numeric, pin_code VARCHAR(4)→String(256)
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=140), nullable=False),
        sa.Column('description', sa.Text(), sa.CheckConstraint('length(description) <= 2000'), nullable=True),
        sa.Column('category', sa.String(length=60), nullable=False),
        sa.Column('condition', sa.String(length=20), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('is_free', sa.Boolean(), nullable=True),
        sa.Column('image_filename', sa.String(length=255), nullable=True),
        sa.Column('kg_saved', sa.Float(), nullable=True),
        sa.Column('pin_code', sa.String(length=4), nullable=True),
        sa.Column('pin_expires_at', sa.DateTime(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('pin_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_sold', sa.Boolean(), nullable=True),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('items')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))
    op.drop_table('users')
