"""Avaliação por segmentos e permutação com dados exclusivamente sintéticos."""

import json

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from credit_risk.ingestion.uci import FEATURES
from credit_risk.modeling.interpretation import (
    permutation_report,
    report_json,
    segment_report,
)


def evaluate(**changes):
    arguments = dict(
        y=[0, 0, 1, 1, 0, 1],
        probability=[0.1, 0.5, 0.4, 0.9, 0.2, 0.8],
        segments=['a', 'a', 'a', 'a', 'b', 'b'],
        dataset_version='synthetic-v1', threshold=0.5,
        minimum_size=4, minimum_class_count=2, bins=2,
    )
    arguments.update(changes)
    return segment_report(**arguments)


def test_known_errors_calibration_and_suppression():
    result = evaluate()
    first, second = result['segments']
    metrics = first['metrics']
    assert metrics['confusion_matrix'] == [[1, 1], [1, 1]]
    assert metrics['brier_score'] == pytest.approx(0.1575)
    assert metrics['false_positive_rate']['value'] == 0.5
    assert metrics['false_negative_rate']['value'] == 0.5
    assert metrics['approved_default_rate']['value'] == 0.5
    assert metrics['calibration_curve'][0]['count'] == 3
    assert metrics['calibration_curve'][0]['observed']['value'] == pytest.approx(1 / 3)
    lower, upper = metrics['false_positive_rate']['wilson_95']
    assert lower == pytest.approx(0.0945312, abs=1e-6)
    assert upper == pytest.approx(0.9054688, abs=1e-6)
    assert not second['sufficient']
    assert second['metrics'] is None
    assert second['differences_from_overall'] is None
    assert json.loads(report_json(result)) == result
    assert evaluate() == result


def test_single_class_segment_is_insufficient_and_no_approved_is_defined():
    result = evaluate(
        segments=['a', 'a', 'b', 'b', 'a', 'b'],
        minimum_size=2, minimum_class_count=1,
    )
    assert all(not row['sufficient'] for row in result['segments'])
    result = evaluate(threshold=0)
    assert result['overall']['approved_default_rate']['value'] is None
    assert result['overall']['approved_default_rate']['wilson_95'] is None


@pytest.mark.parametrize('changes', [
    {'probability': [np.nan] * 6},
    {'probability': [True] * 6},
    {'y': [0, 0, 0, 0, 0, 0]},
    {'segments': ['a']},
    {'segments': [None] * 6},
    {'minimum_class_count': 0},
    {'minimum_size': True},
    {'threshold': float('inf')},
    {'bins': 101},
])
def test_invalid_contract(changes):
    with pytest.raises(ValueError):
        evaluate(**changes)


def test_rejects_misaligned_series():
    with pytest.raises(ValueError, match='Índices'):
        evaluate(y=pd.Series([0, 0, 1, 1, 0, 1]),
                 segments=pd.Series(['a'] * 6, index=range(1, 7)))


def test_constant_model_has_zero_importance_and_preserves_inputs():
    frame = pd.DataFrame({feature: np.arange(20) for feature in FEATURES})
    labels = pd.Series([0, 1] * 10)
    model = DummyClassifier(strategy='prior').fit(frame, labels)
    original = frame.copy(deep=True)
    first = permutation_report(model, frame, labels, dataset_version='synthetic', repeats=3)
    repeated = permutation_report(model, frame, labels, dataset_version='synthetic', repeats=3)
    assert first == repeated
    assert len(first['factors']) == len(FEATURES)
    assert all(row['mean_ap_decrease'] == 0 for row in first['factors'])
    pd.testing.assert_frame_equal(frame, original)
    json.loads(report_json(first))


def test_predictive_feature_has_positive_permutation_importance():
    class FixedPredictor:
        classes_ = np.array([0, 1])

        def predict_proba(self, frame):
            probability = np.where(frame['LIMIT_BAL'].to_numpy() > 0, 0.9, 0.1)
            return np.column_stack([1 - probability, probability])

    labels = pd.Series([0, 1] * 50)
    frame = pd.DataFrame({feature: np.zeros(100) for feature in FEATURES})
    frame['LIMIT_BAL'] = labels.to_numpy()
    result = permutation_report(
        FixedPredictor(), frame, labels, dataset_version='synthetic', repeats=5,
    )
    assert result['factors'][0]['feature'] == 'LIMIT_BAL'
    assert result['factors'][0]['mean_ap_decrease'] > 0
    assert all(row['mean_ap_decrease'] == 0 for row in result['factors'][1:])
