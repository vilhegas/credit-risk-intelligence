"""Integração opcional com PostgreSQL exclusivo, previamente provisionado."""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError, ProgrammingError

from credit_risk.persistence import create_database_engine, get_run, save_run
from credit_risk.persistence.schema import predictions, treated_records


def test_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        create_database_engine()


@pytest.fixture(scope="module")
def database():
    app_url = os.environ.get("TEST_DATABASE_URL")
    owner_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")
    if not app_url or not owner_url:
        pytest.skip("Defina as duas URLs de um PostgreSQL exclusivo para integração.")
    previous = os.environ.get("MIGRATION_DATABASE_URL")
    os.environ["MIGRATION_DATABASE_URL"] = owner_url
    try:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(config, "head")
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
        else:
            os.environ["MIGRATION_DATABASE_URL"] = previous
    engine = create_database_engine(app_url)
    try:
        yield engine
    finally:
        engine.dispose()


def test_connection_persistence_and_permissions(database):
    run_id, record_id = uuid4(), uuid4()
    version = "public-source'; SELECT 1; --"
    with database.begin() as connection:
        assert connection.scalar(sa.text("SELECT current_user")) == "credit_app"
        save_run(connection, run_id, version, {"seed": 42})
        connection.execute(treated_records.insert().values(
            id=record_id, run_id=run_id, subject_key=str(uuid4()),
            reference_date=date(2025, 1, 31), features={"balance": 100}, defaulted=0,
        ))
        connection.execute(predictions.insert().values(
            id=uuid4(), run_id=run_id, record_id=record_id,
            model_version="baseline-v1", probability=Decimal("0.25"),
        ))
    with database.connect() as connection:
        assert get_run(connection, run_id)["dataset_version"] == version
        assert connection.scalar(
            sa.select(predictions.c.probability).where(predictions.c.record_id == record_id)
        ) == Decimal("0.25")
    for statement in (
        "CREATE TABLE credit.forbidden (id integer)",
        "DELETE FROM credit.execution_runs WHERE false",
        "UPDATE credit.execution_runs SET dataset_version = 'x' WHERE false",
        "SELECT * FROM public.alembic_version",
    ):
        with pytest.raises(ProgrammingError), database.begin() as connection:
            connection.execute(sa.text(statement))


def test_constraints(database):
    with database.connect() as connection:
        transaction = connection.begin()
        try:
            run_id, record_id = uuid4(), uuid4()
            save_run(connection, run_id, "synthetic-v1", {})
            record = dict(
                id=record_id, run_id=run_id, subject_key=str(uuid4()),
                reference_date=date(2025, 1, 31), features={}, defaulted=1,
            )
            connection.execute(treated_records.insert().values(**record))
            invalid_statements = [
                treated_records.insert().values(**{**record, "id": uuid4()}),
                treated_records.insert().values(**{**record, "id": uuid4(), "defaulted": 2}),
                treated_records.insert().values(**{**record, "id": uuid4(), "run_id": uuid4()}),
                predictions.insert().values(
                    id=uuid4(), run_id=run_id, record_id=record_id,
                    model_version="test", probability=Decimal("1.01"),
                ),
                predictions.insert().values(
                    id=uuid4(), run_id=run_id, record_id=uuid4(),
                    model_version="test", probability=Decimal("0.5"),
                ),
                predictions.insert().values(
                    id=uuid4(), run_id=run_id, record_id=record_id,
                    model_version="test", probability=None,
                ),
            ]
            for statement in invalid_statements:
                with pytest.raises(IntegrityError), connection.begin_nested():
                    connection.execute(statement)
        finally:
            transaction.rollback()
