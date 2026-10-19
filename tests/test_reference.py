"""Treinamento e prevenção de vazamento com dados sintéticos."""

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from credit_risk.ingestion.uci import FEATURES, PAY, TARGET
from credit_risk.modeling.reference import default_probability, train_reference
from credit_risk.modeling.splitting import split_data


def sample():
    count = 200
    frame = pd.DataFrame({name: np.arange(count) % 7 for name in FEATURES})
    frame["ID"] = np.arange(count) + 1
    frame[TARGET] = np.arange(count) % 2
    for name in PAY:
        frame[name] = pd.Series(np.arange(count) % 3, dtype="string")
    frame["LIMIT_BAL"] = pd.Series(np.arange(count) * 1000, dtype="Int64")
    frame.loc[::9, "LIMIT_BAL"] = pd.NA
    frame.loc[::11, "PAY_0"] = pd.NA
    frame["BILL_AMT6"] = pd.Series([pd.NA] * count, dtype="Int64")
    return split_data(frame, "synthetic-reference-v1")


def test_train_only_unknown_categories_and_valid_probabilities():
    split = sample()
    original = split.train.X.copy(deep=True)
    split.validation.X.loc[:, "LIMIT_BAL"] = 10**12
    split.validation.X.loc[:, "PAY_0"] = "categoria_exclusiva_validacao"
    result = train_reference(split)
    pd.testing.assert_frame_equal(split.train.X, original)
    columns = result.logistic.named_steps["columns"]
    numeric = columns.named_transformers_["numeric"]
    assert numeric.named_steps["impute"].statistics_[0] == pytest.approx(
        float(split.train.X["LIMIT_BAL"].median())
    )
    categories = columns.named_transformers_["categorical"].named_steps["encode"].categories_
    assert "categoria_exclusiva_validacao" not in categories[0]
    for model in (result.logistic, result.dummy):
        probability = default_probability(model, split.validation.X)
        assert np.isfinite(probability).all()
        assert ((probability >= 0) & (probability <= 1)).all()
    dummy_probability = default_probability(result.dummy, split.validation.X)
    np.testing.assert_allclose(dummy_probability, float(split.train.y.mean()))
    report = json.loads(result.report_json())
    assert report["validation"]["scores"]["dummy"]["average_precision"] == pytest.approx(
        float(split.validation.y.mean())
    )
    assert report["features"] == list(FEATURES)


def test_reproducibility_and_test_is_never_accessed():
    split = sample()

    class WithoutTest:
        train = split.train
        validation = split.validation
        metadata = split.metadata

        @property
        def test(self):
            raise AssertionError("Teste reservado à avaliação final.")

    first = train_reference(WithoutTest())
    second = train_reference(WithoutTest())
    assert first.report_json() == second.report_json()
    np.testing.assert_array_equal(
        default_probability(first.logistic, split.validation.X),
        default_probability(second.logistic, split.validation.X),
    )


def test_invalid_targets_overlap_and_nonfinite_features():
    split = sample()
    split.validation.y.iloc[:] = 0
    with pytest.raises(ValueError, match="Ambas as classes"):
        train_reference(split)
    split = sample()
    overlapping = SimpleNamespace(
        train=split.train, validation=split.train, metadata=split.metadata,
    )
    with pytest.raises(ValueError, match="disjuntas"):
        train_reference(overlapping)
    split = sample()
    split.train.X["PAY_AMT1"] = np.inf
    with pytest.raises(ValueError, match="monetários"):
        train_reference(split)
