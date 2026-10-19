"""Isolamento e prevenção de vazamento com dados sintéticos."""

import json

import pandas as pd
import pytest

from credit_risk.ingestion.uci import FEATURES, TARGET
from credit_risk.modeling.splitting import split_data


def sample(count=100):
    frame = pd.DataFrame({name: [1] * count for name in FEATURES})
    frame["ID"] = range(1, count + 1)
    frame[TARGET] = [i % 2 for i in range(count)]
    frame["AGE"] = 30
    frame["future_default_amount"] = 999
    return frame


def temporal():
    frame = sample(60)
    frame["reference_date"] = [
        f"2020-{month:02d}-01" for month in range(1, 7) for _ in range(10)
    ]
    reference = pd.to_datetime(frame["reference_date"])
    frame["label_end_date"] = reference + pd.Timedelta(days=20)
    frame["available_at"] = reference
    return frame


def split_temporal(frame):
    return split_data(
        frame, "synthetic-v1",
        availability_columns=dict.fromkeys(FEATURES, "available_at"),
    )


def test_stratification_isolation_and_reproducibility():
    frame = pd.concat([sample(), sample()], ignore_index=True)
    frame.index = [7] * len(frame)
    original = frame.copy(deep=True)
    first = split_data(frame, "synthetic-v1")
    second = split_data(frame, "synthetic-v1")
    pd.testing.assert_frame_equal(frame, original)
    sets = []
    for name in ("train", "validation", "test"):
        part = getattr(first, name)
        assert part.positions == getattr(second, name).positions
        assert tuple(part.X.columns) == FEATURES
        assert set(part.y) == {0, 1}
        assert not {TARGET, "ID", "AGE", "future_default_amount"} & set(part.X)
        sets.append(set(frame.iloc[list(part.positions)]["ID"]))
    assert not sets[0] & sets[1]
    assert not sets[0] & sets[2]
    assert not sets[1] & sets[2]
    assert sum(len(getattr(first, n).positions) for n in ("train", "validation", "test")) == 200
    assert first.metadata["method"] == "stratified_client"
    assert "generalização temporal" in first.metadata["limitations"][0]
    json.dumps(first.metadata, allow_nan=False)


def test_common_reference_uses_documented_fallback():
    frame = sample()
    frame["reference_date"] = "2005-09-30"
    assert split_data(frame, "uci-synthetic").metadata["method"] == "stratified_client"


def test_temporal_order_client_expurgo_and_horizon():
    frame = temporal()
    # Cliente atravessa treino/validação; ambas as linhas são removidas.
    frame.loc[30, "ID"] = frame.loc[0, "ID"]
    # Alvo ainda indisponível no início da validação.
    frame.loc[1, "label_end_date"] = "2020-04-01"
    result = split_temporal(frame)
    assert result.metadata["method"] == "temporal"
    assert result.metadata["excluded_rows"] == 3
    used = set().union(result.train.positions, result.validation.positions, result.test.positions)
    assert not {0, 1, 30} & used
    dates = pd.to_datetime(frame["reference_date"])
    assert dates.iloc[list(result.train.positions)].max() < dates.iloc[
        list(result.validation.positions)
    ].min()
    assert dates.iloc[list(result.validation.positions)].max() < dates.iloc[
        list(result.test.positions)
    ].min()
    for part, next_part in ((result.train, result.validation), (result.validation, result.test)):
        assert pd.to_datetime(frame.iloc[list(part.positions)]["label_end_date"]).max() < (
            dates.iloc[list(next_part.positions)].min()
        )


def test_post_decision_feature_is_rejected():
    frame = temporal()
    frame.loc[0, "available_at"] = "2020-01-02"
    with pytest.raises(ValueError, match="posterior à decisão"):
        split_temporal(frame)


@pytest.mark.parametrize("problem", ["availability", "horizon", "invalid_date", "two_dates"])
def test_invalid_temporal_input_never_falls_back(problem):
    frame = temporal()
    if problem == "availability":
        frame = frame.drop(columns="available_at")
    elif problem == "horizon":
        frame = frame.drop(columns="label_end_date")
    elif problem == "invalid_date":
        frame.loc[0, "reference_date"] = "inválida"
    else:
        frame["reference_date"] = ["2020-01-01"] * 30 + ["2020-02-01"] * 30
        frame["available_at"] = frame["reference_date"]
        frame["label_end_date"] = pd.to_datetime(frame["reference_date"]) + pd.Timedelta(days=20)
    with pytest.raises(ValueError):
        split_temporal(frame)


def test_insufficient_classes_conflicting_clients_and_parameters():
    frame = sample()
    frame[TARGET] = 0
    with pytest.raises(ValueError):
        split_data(frame, "single")
    frame = sample()
    frame.loc[1, "ID"] = frame.loc[0, "ID"]
    with pytest.raises(ValueError, match="consistente"):
        split_data(frame, "conflict")
    for options in ({"train_fraction": float("nan")}, {"validation_fraction": 0.5}, {"seed": -1}):
        with pytest.raises(ValueError):
            split_data(sample(), "invalid", **options)


def test_temporal_single_class_partition_is_rejected():
    frame = temporal()
    frame.loc[40:, TARGET] = 0
    with pytest.raises(ValueError, match="Ambas as classes"):
        split_temporal(frame)
