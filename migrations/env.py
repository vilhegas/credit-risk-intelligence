"""Migrações com credenciais fornecidas exclusivamente pelo ambiente."""

import os

from alembic import context
from sqlalchemy import create_engine, pool

from credit_risk.persistence.schema import metadata


def run_migrations() -> None:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        raise RuntimeError("Defina MIGRATION_DATABASE_URL para executar migrações.")
    if context.is_offline_mode():
        context.configure(url=url, target_metadata=metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url, poolclass=pool.NullPool, hide_parameters=True)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
