"""add fino_messages table

Revision ID: 0445dfff7f85
Revises: fd40fe73003c
Create Date: 2026-08-12 23:11:26.763671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0445dfff7f85'
down_revision: Union[str, Sequence[str], None] = 'fd40fe73003c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('fino_messages',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('role', sa.String(length=16), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fino_messages_created_at'), 'fino_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_fino_messages_user_id'), 'fino_messages', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_fino_messages_user_id'), table_name='fino_messages')
    op.drop_index(op.f('ix_fino_messages_created_at'), table_name='fino_messages')
    op.drop_table('fino_messages')
