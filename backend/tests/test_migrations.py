"""Guards against the class of bug that broke the production deploy: a
migration that only ever ran against SQLite (every local/CI run) silently
assumed a constraint name that SQLite's batch-mode naming_convention
synthesizes but that a real database's own auto-naming never produces —
so `alembic upgrade head` crashed the first time it ever touched a real
Postgres database, in production, months after the migration was written.

This won't catch dialect-specific issues (no Postgres available in CI),
but it does prove the full chain applies and reverses cleanly on SQLite,
which the standard test suite (Base.metadata.create_all(), no Alembic at
all) never exercised.

Note: alembic/env.py resolves its DB URL from app.core.config.get_settings()
unconditionally (ignores Config.set_main_option), so the only way to point
a programmatic alembic run at a throwaway DB is the DATABASE_URL env var —
same as every `DATABASE_URL=... alembic upgrade head` invocation used
manually elsewhere in this project."""
import os
import uuid

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings

ALEMBIC_INI = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")


def test_migrations_upgrade_head_then_downgrade_base_cleanly(tmp_path, monkeypatch):
    db_path = str(tmp_path / f"migration_test_{uuid.uuid4().hex}.db")
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    get_settings.cache_clear()
    try:
        cfg = Config(ALEMBIC_INI)

        command.upgrade(cfg, "head")
        engine = create_engine(db_url)
        tables = set(inspect(engine).get_table_names())
        assert {"users", "budgets", "categories", "advice", "advice_action_states"} <= tables
        engine.dispose()

        command.downgrade(cfg, "base")
        engine = create_engine(db_url)
        tables = set(inspect(engine).get_table_names())
        assert "users" not in tables
        assert "alembic_version" in tables  # stamp table itself persists, just at base
        engine.dispose()
    finally:
        get_settings.cache_clear()
