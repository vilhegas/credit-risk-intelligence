"""Conferência SQL/Pandas com amostra sintética em PostgreSQL opcional."""

import os
from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
import pytest
from alembic import command
from alembic.config import Config

from credit_risk.analysis.indicators import describe_run
from credit_risk.ingestion.uci import FEATURES
from credit_risk.persistence import create_database_engine, save_run
from credit_risk.persistence.schema import treated_records


@pytest.fixture
def database(monkeypatch):
    app_url = os.environ.get("TEST_DATABASE_URL")
    owner_url = os.environ.get("TEST_MIGRATION_DATABASE_URL")
    if not app_url or not owner_url:
        pytest.skip("Exige as duas URLs de PostgreSQL exclusivo para testes.")
    monkeypatch.setenv("MIGRATION_DATABASE_URL", owner_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_database_engine(app_url)
    try:
        yield engine
    finally:
        engine.dispose()


def test_run_id_requires_uuid():
    with pytest.raises(ValueError, match="UUID"):
        describe_run(None, "valor inválido")


def assert_number(actual, expected):
    if pd.isna(expected):
        assert actual is None
    else:
        assert float(actual) == pytest.approx(float(expected))


def test_sql_matches_pandas(database):
    limits = [0, 99999, 100000, 299999, 300000, None, None]
    targets = [0, 1, 1, 0, 1, 0, 1]
    payloads = []
    for position, limit in enumerate(limits):
        features = dict.fromkeys(FEATURES, 1)
        features.update(
            LIMIT_BAL=limit,
            BILL_AMT1=[-50, 0, 100, None, 500, 50, 100][position],
            PAY_AMT1=None,
        )
        if position == 6:
            del features["LIMIT_BAL"]
        payloads.append(features)
    frame = pd.DataFrame(payloads, columns=FEATURES)
    frame["defaulted"] = targets
    run_id, other_run = uuid4(), uuid4()
    with database.connect() as connection:
        transaction = connection.begin()
        try:
            save_run(connection, run_id, "synthetic-indicators-v1", {})
            save_run(connection, other_run, "synthetic-other-v1", {})
            records = [
                {
                    "id": uuid4(), "run_id": run_id,
                    "subject_key": f"synthetic:{position}",
                    "reference_date": date(2005, 9, 30),
                    "features": features, "defaulted": targets[position],
                }
                for position, features in enumerate(payloads)
            ]
            # Registro de outra versão não pode participar de nenhum agregado.
            records.append({**records[0], "id": uuid4(), "run_id": other_run})
            connection.execute(treated_records.insert(), records)
            result = describe_run(connection, run_id)
            volume = result["volume"][0]
            assert volume["operations"] == len(frame)
            assert volume["subjects"] == len(frame)
            assert volume["reference_dates"] == 1
            assert volume["defaults"] == frame["defaulted"].sum()
            assert_number(volume["default_rate"], frame["defaulted"].mean())

            for row in result["distribution"]:
                values = frame[row["variable"]].astype(float)
                assert row["observed"] == values.count()
                expected = {
                    "minimum": values.min(), "maximum": values.max(),
                    "mean": values.mean(), "q25": values.quantile(0.25),
                    "median": values.quantile(0.5), "q75": values.quantile(0.75),
                }
                for name, value in expected.items():
                    assert_number(row[name], value)

            assert len(result["missing"]) == len(FEATURES)
            for row in result["missing"]:
                missing = frame[row["variable"]].isna()
                assert row["operations"] == len(frame)
                assert row["missing"] == missing.sum()
                assert_number(row["missing_rate"], missing.mean())

            frame["segment"] = pd.cut(
                frame["LIMIT_BAL"],
                bins=[float("-inf"), 100000, 300000, float("inf")],
                labels=["abaixo_100000", "100000_a_299999", "300000_ou_mais"],
                right=False,
            ).astype("string").fillna("ausente")
            expected = frame.groupby("segment")["defaulted"].agg(["size", "sum", "mean"])
            assert {row["segment"] for row in result["segments"]} == set(expected.index)
            for row in result["segments"]:
                group = expected.loc[row["segment"]]
                assert row["operations"] == group["size"]
                assert row["defaults"] == group["sum"]
                assert_number(row["default_rate"], group["mean"])

            empty = describe_run(connection, uuid4())
            assert empty["volume"] == [{
                "operations": 0, "subjects": 0, "reference_dates": 0,
                "defaults": 0, "default_rate": None,
            }]
            assert empty["segments"] == []
            for row in empty["distribution"]:
                assert row["observed"] == 0
                assert all(value is None for key, value in row.items()
                           if key not in {"variable", "observed"})
            for row in empty["missing"]:
                assert row["operations"] == row["missing"] == 0
                assert row["missing_rate"] is None
        finally:
            transaction.rollback()
