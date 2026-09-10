"""add user_profiles table

Revision ID: fd40fe73003c
Revises: f8d15ed2bdb0
Create Date: 2026-08-12 21:55:33.565021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd40fe73003c'
down_revision: Union[str, Sequence[str], None] = 'f8d15ed2bdb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_profiles',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('current_step', sa.Integer(), nullable=False),
    sa.Column('answers', sa.JSON(), nullable=False),
    sa.Column('risk_band', sa.String(length=16), nullable=True),
    sa.Column('literacy_level', sa.String(length=16), nullable=True),
    sa.Column('life_stage', sa.String(length=16), nullable=True),
    sa.Column('income_stability', sa.String(length=16), nullable=True),
    sa.Column('investment_experience', sa.String(length=16), nullable=True),
    sa.Column('goals', sa.JSON(), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
