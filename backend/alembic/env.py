import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import the models registry for its side effect: every feature's models
# module is imported there, populating Base.metadata. Without this,
# autogenerate silently produces empty migrations (conventions invariant 6).
from app.core import models_registry
from app.core.config import get_settings
from app.core.database import pgbouncer_connect_args

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL comes from app Settings (DATABASE_URL), never from alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = models_registry.Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync.

    The engine reuses ``pgbouncer_connect_args``: under PgBouncer transaction
    pooling the asyncpg statement caches must be disabled here too, otherwise
    alembic's prepared statements collide with pooled server connections that
    already hold the same ``__asyncpg_stmt_N__`` names
    (``DuplicatePreparedStatementError`` — seen in production on redeploys).
    """
    settings = get_settings()
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
        connect_args=pgbouncer_connect_args(settings),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
