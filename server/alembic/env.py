from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from lhmm.db.base import Base
from lhmm.db import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option('sqlalchemy.url'),
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        # Ensure SQLite is configured as desired for this database file and this connection
        try:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
            connection.exec_driver_sql("PRAGMA foreign_keys=ON;")
        except Exception:
            pass

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
