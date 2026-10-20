"""Comparação limitada com dados sintéticos e isolamento do teste final."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score

from credit_risk.ingestion.uci import FEATURES, PAY, TARGET
from credit_risk.modeling.comparison import compare_models
from credit_risk.modeling.reference import default_probability
from credit_risk.modeling.splitting import split_data


def sample():
    count = 200
    rng = np.random.default_rng(17)
    frame = pd.DataFrame({name: rng.integers(0, 20, count) for name in FEATURES})
    frame["ID"] = np.arange(count) + 1
    frame[TARGET] = np.arange(count) % 2
    for name in PAY:
        frame[name] = frame[name].astype("string")
    return split_data(frame, "synthetic-comparison-v1")


def test_reproducibility_metrics_and_reserved_test():
    split = sample()
    original = split.train.X.copy(deep=True)

    class ReservedTest:
        train = split.train
        validation = split.validation
        metadata = split.metadata

        @property
        def test(self):
            raise AssertionError("Teste final não pode ser consultado.")

    first = compare_models(ReservedTest())
    second = compare_models(ReservedTest())
    assert first.report_json() == second.report_json()
    pd.testing.assert_frame_equal(split.train.X, original)
    assert len(first.report["table"]) == 7
    assert first.report["budget"]["total_fits_including_dummy"] == 7
    assert first.selected is first.models[first.report["selected_candidate"]]
    for row in first.report["table"]:
        probability = default_probability(first.models[row["candidate"]], split.validation.X)
        prediction = probability >= 0.5
        assert row["average_precision"] == pytest.approx(
            average_precision_score(split.validation.y, probability)
        )
        assert row["roc_auc"] == pytest.approx(roc_auc_score(split.validation.y, probability))
        assert row["precision"] == pytest.approx(
            precision_score(split.validation.y, prediction, zero_division=0)
        )
        assert row["recall"] == pytest.approx(
            recall_score(split.validation.y, prediction, zero_division=0)
        )
    maximum = max(row["average_precision"] for row in first.report["table"])
    chosen = next(row for row in first.report["table"]
                  if row["candidate"] == first.report["selected_candidate"])
    assert chosen["average_precision"] == maximum


def test_preprocessing_is_independent_and_learned_only_from_training():
    split = sample()
    split.validation.X["LIMIT_BAL"] = 10**12
    split.validation.X["PAY_0"] = "exclusiva_validacao"
    result = compare_models(split)
    preprocessors = []
    for model in result.models.values():
        columns = model.named_steps["columns"]
        preprocessors.append(columns)
        numeric = columns.named_transformers_["numeric"]
        assert numeric.named_steps["impute"].statistics_[0] == pytest.approx(
            float(split.train.X["LIMIT_BAL"].median())
        )
        categories = columns.named_transformers_["categorical"].named_steps["encode"].categories_
        assert "exclusiva_validacao" not in categories[0]
    assert len({id(item) for item in preprocessors}) == 7


def test_exact_ties_keep_reference_without_claiming_improvement():
    split = sample()
    for name in FEATURES:
        value = "1" if name in PAY else 1
        split.train.X[name] = value
        split.validation.X[name] = value
    result = compare_models(split)
    assert result.report["selected_candidate"] == "logistic_c1"
    assert not result.report["selected_above_reference"]
    assert not result.report["selected_above_dummy"]


def test_invalid_method_seed_and_single_class():
    split = sample()
    invalid = SimpleNamespace(
        train=split.train, validation=split.validation, metadata={"method": "unknown"}
    )
    with pytest.raises(ValueError, match="partições"):
        compare_models(invalid)
    with pytest.raises(ValueError, match="Semente"):
        compare_models(split, seed=-1)
    split.validation.y.iloc[:] = 0
    with pytest.raises(ValueError, match="Ambas as classes"):
        compare_models(split)
