"""add users, refresh_tokens, user_id scoping

Revision ID: f8d15ed2bdb0
Revises: 621332ebd388
Create Date: 2026-08-10 18:44:28.251499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f8d15ed2bdb0'
down_revision: Union[str, Sequence[str], None] = '621332ebd388'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Lets batch mode address the pre-existing anonymous UNIQUE constraints on
# categories.name and budgets.category_id on SQLite, which reflects them
# with name=None (so they're otherwise undroppable by name) and requires
# batch mode's recreate-table strategy for any ALTER at all.
naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


def _unique_constraint_name(bind, table_name: str, column_name: str) -> str:
    """On Postgres the anonymous UniqueConstraint('category_id')/('name')
    from the base migration got a *real*, reflectable auto-generated name
    (Postgres's own `<table>_<column>_key` convention) rather than staying
    nameless the way SQLite leaves it — so unlike SQLite, we don't need to
    synthesize a name here, just look up the one Postgres already gave it.
    Discovered the hard way: hardcoding the SQLite-side synthesized name
    (`uq_budgets_category_id`) here made this migration crash in production
    with "constraint ... does not exist" the first time it ever ran against
    a real Postgres database."""
    for uc in inspect(bind).get_unique_constraints(table_name):
        if uc["column_names"] == [column_name]:
            return uc["name"]
    raise RuntimeError(f"No unique constraint found on {table_name}.{column_name}")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    budgets_uq = "uq_budgets_category_id" if is_sqlite else _unique_constraint_name(bind, "budgets", "category_id")
    categories_uq = "uq_categories_name" if is_sqlite else _unique_constraint_name(bind, "categories", "name")
    op.create_table('users',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('google_sub', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('picture_url', sa.String(length=512), nullable=True),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)

    op.create_table('refresh_tokens',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.String(length=36), nullable=False),
    sa.Column('jti', sa.String(length=36), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_jti'), 'refresh_tokens', ['jti'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)

    # user_id columns are nullable at the DB level: there's no user to
    # backfill onto at migration time (auth didn't exist yet). The very
    # first Google sign-in claims every orphaned row in application code
    # (app/routers/auth.py::_claim_orphaned_data). The ORM model still
    # declares nullable=False as the going-forward invariant for new rows.
    with op.batch_alter_table('budgets', naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.drop_constraint(budgets_uq, type_='unique')
        batch_op.create_index(op.f('ix_budgets_user_id'), ['user_id'], unique=False)
        batch_op.create_unique_constraint('uq_budgets_user_category', ['user_id', 'category_id'])
        batch_op.create_foreign_key('fk_budgets_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('categories', naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.drop_constraint(categories_uq, type_='unique')
        batch_op.create_index(op.f('ix_categories_user_id'), ['user_id'], unique=False)
        batch_op.create_unique_constraint('uq_categories_user_name', ['user_id', 'name'])
        batch_op.create_foreign_key('fk_categories_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('forecasts') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index(op.f('ix_forecasts_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_forecasts_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('goals') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index(op.f('ix_goals_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_goals_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('recommendations') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.create_index(op.f('ix_recommendations_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_recommendations_user_id_users', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('transactions') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
        batch_op.drop_index('ix_transactions_dedup')
        batch_op.create_index(
            'ix_transactions_dedup', ['user_id', 'date', 'amount_minor', 'raw_description'], unique=False
        )
        batch_op.create_index(op.f('ix_transactions_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_transactions_user_id_users', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.drop_constraint('fk_transactions_user_id_users', type_='foreignkey')
        batch_op.drop_index(op.f('ix_transactions_user_id'))
        batch_op.drop_index('ix_transactions_dedup')
        batch_op.create_index(
            'ix_transactions_dedup', ['date', 'amount_minor', 'raw_description'], unique=False
        )
        batch_op.drop_column('user_id')

    with op.batch_alter_table('recommendations') as batch_op:
        batch_op.drop_constraint('fk_recommendations_user_id_users', type_='foreignkey')
        batch_op.drop_index(op.f('ix_recommendations_user_id'))
        batch_op.drop_column('user_id')

    with op.batch_alter_table('goals') as batch_op:
        batch_op.drop_constraint('fk_goals_user_id_users', type_='foreignkey')
        batch_op.drop_index(op.f('ix_goals_user_id'))
        batch_op.drop_column('user_id')

    with op.batch_alter_table('forecasts') as batch_op:
        batch_op.drop_constraint('fk_forecasts_user_id_users', type_='foreignkey')
        batch_op.drop_index(op.f('ix_forecasts_user_id'))
        batch_op.drop_column('user_id')

    with op.batch_alter_table('categories') as batch_op:
        batch_op.drop_constraint('fk_categories_user_id_users', type_='foreignkey')
        batch_op.drop_constraint('uq_categories_user_name', type_='unique')
        batch_op.drop_index(op.f('ix_categories_user_id'))
        batch_op.create_unique_constraint('uq_categories_name', ['name'])
        batch_op.drop_column('user_id')

    with op.batch_alter_table('budgets') as batch_op:
        batch_op.drop_constraint('fk_budgets_user_id_users', type_='foreignkey')
        batch_op.drop_constraint('uq_budgets_user_category', type_='unique')
        batch_op.drop_index(op.f('ix_budgets_user_id'))
        batch_op.create_unique_constraint('uq_budgets_category_id', ['category_id'])
        batch_op.drop_column('user_id')

    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_jti'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
