"""Persistência PostgreSQL sem conexões durante a importação."""

import os
from collections.abc import Mapping
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine, make_url

from credit_risk.persistence.schema import execution_runs


def create_database_engine(url: str | None = None) -> Engine:
    value = url or os.environ.get("DATABASE_URL")
    if not value:
        raise ValueError("Defina DATABASE_URL.")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg":
        raise ValueError("Utilize PostgreSQL com o driver postgresql+psycopg.")
    return sa.create_engine(parsed, pool_pre_ping=True, hide_parameters=True)


def save_run(
    connection: Connection,
    run_id: UUID,
    dataset_version: str,
    configuration: Mapping[str, Any],
) -> None:
    """Insere metadados; a transação pertence ao chamador."""
    connection.execute(
        execution_runs.insert().values(
            id=run_id,
            dataset_version=dataset_version,
            configuration=dict(configuration),
        )
    )


def get_run(connection: Connection, run_id: UUID) -> Mapping[str, Any] | None:
    """Consulta por parâmetro vinculado, sem interpolação de SQL."""
    return connection.execute(
        sa.select(execution_runs).where(execution_runs.c.id == run_id)
    ).mappings().one_or_none()
