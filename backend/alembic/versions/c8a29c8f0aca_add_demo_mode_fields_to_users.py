"""add demo mode fields to users

Revision ID: c8a29c8f0aca
Revises: 0445dfff7f85
Create Date: 2026-08-12 23:29:55.344036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8a29c8f0aca'
down_revision: Union[str, Sequence[str], None] = '0445dfff7f85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('demo_shadow_user_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('test_mode_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_foreign_key('fk_users_demo_shadow_user_id', 'users', ['demo_shadow_user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('fk_users_demo_shadow_user_id', type_='foreignkey')
        batch_op.drop_column('test_mode_enabled')
        batch_op.drop_column('demo_shadow_user_id')
        batch_op.drop_column('is_demo')
