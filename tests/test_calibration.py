"""Exemplos sintéticos conhecidos para calibração e políticas."""

import json
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from credit_risk.modeling.calibration import (
    Policy,
    calibration_report,
    evaluate_policy,
    select_policy,
)


def select(**changes):
    arguments = dict(
        calibration_y=[0, 1, 0, 1],
        calibration_probability=[0.1, 0.8, 0.3, 0.6],
        selection_y=[0, 0, 1, 1],
        selection_probability=[0.1, 0.6, 0.4, 0.9],
        calibration_clients=['a', 'b', 'c', 'd'],
        selection_clients=['e', 'f', 'g', 'h'],
        thresholds=[0.3, 0.5, 0.8],
        false_negative_cost=10,
        false_positive_cost=2,
        min_approval_rate=0.25,
        min_default_recall=0.5,
        minimum_brier_gain=1,
        development_version='synthetic-v1',
    )
    arguments.update(changes)
    return select_policy(**arguments)


def test_known_confusion_cost_and_boundary():
    policy = Policy(0.5, 10, 2, 0, 0)
    result = evaluate_policy(policy, [0, 0, 1, 1], [0.1, 0.5, 0.4, 0.9])
    assert result['confusion_matrix'] == [[1, 1], [1, 1]]
    assert result['total_cost'] == 12
    assert result['mean_cost'] == 3
    assert result['approval_rate'] == result['approved_default_rate'] == 0.5
    assert result['default_recall'] == 0.5
    with pytest.raises(FrozenInstanceError):
        policy.threshold = 0.8


def test_brier_curve_endpoints_and_empty_bins():
    report = calibration_report([0, 1, 0, 1], [0, 1, 0.5, 0.5], bins=2)
    assert report['brier_score'] == pytest.approx(0.125)
    assert [row['count'] for row in report['curve']] == [3, 1]
    assert report['curve'][0]['default_rate'] == pytest.approx(1 / 3)
    assert report['curve'][0]['mean_probability'] == pytest.approx(1 / 3)
    sparse = calibration_report([0, 1], [0, 1])
    assert len(sparse['curve']) == 2


def test_selection_constraints_and_reproducibility():
    policy, report = select()
    assert policy.threshold == 0.3
    assert policy.calibration_method == 'identity'
    assert report['selected']['confusion_matrix'] == [[1, 1], [0, 2]]
    assert report['selected']['total_cost'] == 2
    again, repeated = select()
    assert again == policy
    assert repeated == report
    json.dumps(report, allow_nan=False)
    assert json.loads(policy.report_json())['threshold'] == 0.3
    with pytest.raises(ValueError, match='Nenhum limiar'):
        select(min_approval_rate=1)


def test_no_approved_and_tie_break():
    result = evaluate_policy(Policy(0, 1, 1, 0, 0), [0, 1], [0, 1])
    assert result['approved_default_rate'] is None
    assert result['approved'] == 0
    policy, _ = select(thresholds=[0.35, 0.3], false_positive_cost=0)
    assert policy.threshold == 0.3


def test_sigmoid_is_used_only_with_selection_gain():
    labels = [0, 1] * 30
    probabilities = [0.9, 0.1] * 30
    policy, report = select(
        calibration_y=labels,
        calibration_probability=probabilities,
        selection_y=labels,
        selection_probability=probabilities,
        calibration_clients=[f'cal-{i}' for i in range(60)],
        selection_clients=[f'sel-{i}' for i in range(60)],
        thresholds=[0.5],
        minimum_brier_gain=0.01,
    )
    assert policy.calibration_method == 'sigmoid'
    assert report['observed_brier_gain'] > 0.01
    assert report['selected']['confusion_matrix'] == [[30, 0], [0, 30]]
    before = policy.report_json()
    evaluate_policy(policy, [0, 1], [0.2, 0.8])
    assert policy.report_json() == before
    np.testing.assert_allclose(policy.probabilities([0, 1]), policy.probabilities([0, 1]))


@pytest.mark.parametrize('probability', [[np.nan, 0.5], [0, 2], [[0, 1]], [True, False]])
def test_invalid_probabilities(probability):
    with pytest.raises(ValueError):
        calibration_report([0, 1], probability)


def test_invalid_targets_overlap_and_parameters():
    with pytest.raises(ValueError, match='Ambas as classes'):
        calibration_report([0, 0], [0.1, 0.2])
    with pytest.raises(ValueError, match='disjuntos'):
        select(selection_clients=['a', 'f', 'g', 'h'])
    with pytest.raises(ValueError):
        select(false_negative_cost=-1)
    with pytest.raises(ValueError):
        select(thresholds=[])
    with pytest.raises(ValueError):
        select(minimum_brier_gain=float('nan'))
