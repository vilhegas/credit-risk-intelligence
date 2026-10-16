"""Dados sintéticos; testes locais e integração PostgreSQL opcional."""

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pandas as pd
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from credit_risk.ingestion.uci import (
    COLUMNS,
    FEATURES,
    MAX_BYTES,
    MEMBER,
    TARGET,
    IngestionError,
    Provenance,
    ingest_uci,
    read_archive,
    validate_frame,
)
from credit_risk.persistence import create_database_engine
from credit_risk.persistence.schema import execution_runs, treated_records


@pytest.fixture
def frame():
    rows = [{name: 1 for name in COLUMNS} for _ in range(2)]
    rows[1]["ID"] = 2
    rows[1][TARGET] = 0
    rows[0]["BILL_AMT1"] = -10
    return pd.DataFrame(rows, columns=COLUMNS)


@pytest.fixture
def archive(tmp_path, monkeypatch, frame):
    path = tmp_path / "source.zip"
    with ZipFile(path, "w") as output:
        output.writestr(MEMBER, b"synthetic-xls")
    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: frame.copy())
    return path


def provenance():
    return Provenance(
        version="synthetic-test-v1",
        obtained_at=datetime(2025, 1, 1, tzinfo=UTC),
        license_confirmed=True,
        temporal_order_confirmed=True,
        evidence="Fixture sintética; não constitui conferência da fonte pública.",
    )


def test_valid_archive_and_checksums(archive):
    frame, metadata = read_archive(archive)
    assert len(frame) == 2
    assert frame.loc[0, "BILL_AMT1"] == -10
    assert metadata["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert metadata["member_sha256"] == hashlib.sha256(b"synthetic-xls").hexdigest()
    assert metadata["quality"]["missing_values"] == 0
    assert len(FEATURES) == 19
    assert not set(FEATURES) & {"ID", TARGET, "SEX", "AGE", "EDUCATION", "MARRIAGE"}


@pytest.mark.parametrize("problem", ["header", "missing", "target", "duplicate", "type"])
def test_invalid_schema(frame, problem):
    if problem == "header":
        frame = frame.drop(columns="AGE")
    elif problem == "missing":
        frame.loc[0, "AGE"] = float("nan")
    elif problem == "target":
        frame.loc[0, TARGET] = 2
    elif problem == "duplicate":
        frame.loc[1, "ID"] = 1
    else:
        frame["AGE"] = "inválido"
    with pytest.raises(IngestionError):
        validate_frame(frame)


def test_invalid_archive(tmp_path):
    path = tmp_path / "invalid.zip"
    path.write_bytes(b"not a zip")
    with pytest.raises(IngestionError):
        read_archive(path)
    with ZipFile(path, "w") as output:
        output.writestr("../unexpected.xls", b"x")
    with pytest.raises(IngestionError):
        read_archive(path)


def test_archive_size_limit(tmp_path):
    path = tmp_path / "large.zip"
    with path.open("wb") as output:
        output.truncate(MAX_BYTES + 1)
    with pytest.raises(IngestionError, match="tamanho"):
        read_archive(path)


def test_provenance_required():
    with pytest.raises(IngestionError, match="licença"):
        Provenance("v1", datetime(2025, 1, 1, tzinfo=UTC), False, True, "teste").validate()


@pytest.fixture
def database(monkeypatch):
    app_url = os.environ.get("TEST_DATABASE_URL")
    owner_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")
    if not app_url or not owner_url:
        pytest.skip("Integração exige as duas URLs de PostgreSQL exclusivo para testes.")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", owner_url)
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    engine = create_database_engine(app_url)
    try:
        yield engine
    finally:
        engine.dispose()


def test_import_and_reexecution_without_duplicates(archive, monkeypatch, database, frame):
    # Conteúdo distinto por teste; não depende de limpeza destrutiva do banco.
    with ZipFile(archive, "w") as output:
        output.writestr(MEMBER, str(uuid4()).encode())
    first = ingest_uci(archive, database, provenance())
    second = ingest_uci(archive, database, provenance())
    assert not first.reused
    assert second.reused
    assert first.run_id == second.run_id
    with database.connect() as connection:
        assert connection.scalar(
            sa.select(sa.func.count()).select_from(treated_records).where(
                treated_records.c.run_id == first.run_id
            )
        ) == 2
        stored = connection.scalar(
            sa.select(execution_runs.c.configuration).where(execution_runs.c.id == first.run_id)
        )
        assert stored["source_version"] == "synthetic-test-v1"
        assert stored["contract_version"] == "uci-350-v1"
    invalid = frame.copy()
    invalid.loc[0, TARGET] = 3
    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: invalid)
    with pytest.raises(IngestionError):
        ingest_uci(archive, database, provenance())
    with database.connect() as connection:
        assert connection.scalar(
            sa.select(sa.func.count()).select_from(treated_records).where(
                treated_records.c.run_id == first.run_id
            )
        ) == 2
