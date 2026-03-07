"""
Alembic env.py
- Locally  : reads URL from alembic.ini  (postgresql+pg8000://...)
- On Render: reads DATABASE_URL env var  (postgresql://... → converted to pg8000)
"""
import os
import re
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from alembic import context

# Register all ORM models so Alembic can detect schema changes
from app.database import Base
from app.models import *  # noqa: F401, F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    """
    Prefer DATABASE_URL from the environment (set by Render).
    Falls back to alembic.ini for local development.
    Converts any postgresql:// or postgresql+asyncpg:// → postgresql+pg8000://
    """
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    # Normalise driver to pg8000 (pure-Python, no compilation needed)
    url = re.sub(r"^postgresql(\+\w+)?://", "postgresql+pg8000://", url)
    return url


def run_migrations_offline() -> None:
    """Generate SQL script without a live DB connection."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB using pg8000 (sync, pure-Python)."""
    connectable = create_engine(_get_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
