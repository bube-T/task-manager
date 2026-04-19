# alembic/env.py — Alembic migration environment configuration.
#
# This file is run by Alembic every time you execute a migration command:
#   alembic revision --autogenerate -m "..."   → generates a new migration script
#   alembic upgrade head                        → applies all pending migrations
#   alembic downgrade -1                        → rolls back the last migration
#
# It tells Alembic three things:
#   1. Which database URL to connect to
#   2. Which models to scan when auto-generating migrations (via Base.metadata)
#   3. How to run migrations (offline vs online mode)

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Import all ORM models so their table definitions are registered on Base.metadata.
# If a model is not imported here, Alembic will not detect its table during
# --autogenerate and will not generate a CREATE TABLE for it.
from app.models import User, Task

# Import Base — its .metadata attribute holds all the table definitions
# that Alembic compares against the current database state.
from app.database import Base

from alembic import context

# The Alembic Config object gives access to values in alembic.ini.
config = context.config

# --- Database URL ---
# Read the DATABASE_URL from the .env file at runtime.
# This avoids hard-coding credentials in alembic.ini, which might be committed to git.
# We override sqlalchemy.url programmatically so Alembic uses the same URL as the app.
import os
from dotenv import load_dotenv
load_dotenv()   # Loads backend/.env into os.environ
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# --- Logging ---
# Configure Python's logging using the [loggers] section in alembic.ini.
# This makes Alembic print progress messages (e.g. "Running upgrade -> abc123")
# during migration commands.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata tells Alembic what the schema SHOULD look like.
# During --autogenerate, Alembic compares this metadata against the actual
# database and generates the SQL needed to make them match.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Offline mode generates SQL migration scripts without connecting to the
    database. This is useful when you want to review the SQL before applying it,
    or when running in an environment without direct DB access.

    Run with: alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,               # Render literal values instead of bind params
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode (the default).

    Online mode connects to the database directly and applies migrations
    immediately. This is what runs when you do:
        alembic upgrade head

    NullPool is used instead of the normal connection pool because Alembic
    runs as a short-lived CLI process — keeping a pool open would be wasteful.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,   # No connection pool — open one, use it, close it
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# --- Entry point ---
# Alembic calls this file as a script. Depending on whether --sql was passed
# (offline) or not (online), it runs the appropriate function.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
