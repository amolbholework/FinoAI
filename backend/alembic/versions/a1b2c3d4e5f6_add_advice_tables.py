"""add advice tables

Revision ID: a1b2c3d4e5f6
Revises: c8a29c8f0aca
Create Date: 2026-08-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c8a29c8f0aca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('advice',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('data_version', sa.String(length=64), nullable=False),
    sa.Column('input_summary', sa.JSON(), nullable=False),
    sa.Column('output', sa.JSON(), nullable=False),
    sa.Column('model_version', sa.String(length=64), nullable=False),
    sa.Column('is_fallback', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advice_data_version'), 'advice', ['data_version'], unique=False)
    op.create_index(op.f('ix_advice_user_id'), 'advice', ['user_id'], unique=False)

    op.create_table('advice_action_states',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('advice_id', sa.String(length=36), nullable=False),
    sa.Column('recommendation_index', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['advice_id'], ['advice.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('advice_id', 'recommendation_index', name='uq_advice_action_state')
    )
    op.create_index(op.f('ix_advice_action_states_advice_id'), 'advice_action_states', ['advice_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_advice_action_states_advice_id'), table_name='advice_action_states')
    op.drop_table('advice_action_states')
    op.drop_index(op.f('ix_advice_user_id'), table_name='advice')
    op.drop_index(op.f('ix_advice_data_version'), table_name='advice')
    op.drop_table('advice')
