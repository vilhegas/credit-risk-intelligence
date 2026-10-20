"""Avaliação final com exemplos exclusivamente sintéticos."""

import json

import pytest

from credit_risk.modeling.final_evaluation import evaluate_once


def arguments(tmp_path):
    return {
        'y': [0, 0, 1, 1],
        'probability': [0.1, 0.5, 0.4, 0.9],
        'baseline_probability': [0.5] * 4,
        'threshold': 0.5,
        'frozen_manifest': {
            'dataset_sha256': 'a' * 64,
            'partition_sha256': 'b' * 64,
            'model_sha256': 'c' * 64,
            'policy_sha256': 'd' * 64,
            'code_revision': 'revisao-sintetica',
            'environment': 'ambiente-sintetico',
            'frozen_at_utc': '2026-01-01T00:00:00Z',
        },
        'output_directory': tmp_path / 'evaluation',
        'resamples': 100,
    }


def test_known_metrics_intervals_and_no_overwrite(tmp_path):
    kwargs = arguments(tmp_path)
    report = evaluate_once(**kwargs)
    metrics = report['metrics']
    assert metrics['confusion_matrix'] == [[1, 1], [1, 1]]
    assert metrics['precision'] == metrics['recall'] == metrics['f1'] == 0.5
    assert metrics['approved_default_rate'] == 0.5
    assert metrics['brier_score'] == pytest.approx(0.1575)
    assert metrics['baseline_average_precision'] == 0.5
    assert sum(row['count'] for row in report['calibration_curve']) == 4
    interval = report['uncertainty']['intervals']['average_precision_difference']
    assert interval['lower'] <= interval['upper']
    path = kwargs['output_directory'] / 'report.json'
    original = path.read_bytes()
    assert json.loads(original) == report
    with pytest.raises(FileExistsError):
        evaluate_once(**kwargs)
    assert path.read_bytes() == original
    kwargs['output_directory'] = tmp_path / 'reproduction'
    assert evaluate_once(**kwargs) == report


def test_no_approved_and_negative_result(tmp_path):
    kwargs = arguments(tmp_path)
    kwargs.update(threshold=0, probability=[0.9, 0.8, 0.2, 0.1])
    report = evaluate_once(**kwargs)
    assert report['metrics']['approved_default_rate'] is None
    assert report['metrics']['average_precision_difference'] < 0
    assert not report['above_baseline_descriptive']
    assert report['uncertainty']['intervals']['approved_default_rate']['lower'] is None


@pytest.mark.parametrize('changes', [
    {'y': [0, 0, 0, 0]},
    {'probability': [0.1, float('nan'), 0.4, 0.9]},
    {'baseline_probability': [0.5]},
    {'threshold': True},
    {'resamples': 0},
    {'frozen_manifest': {}},
])
def test_invalid_inputs_do_not_reserve_output(tmp_path, changes):
    kwargs = arguments(tmp_path)
    kwargs.update(changes)
    with pytest.raises(ValueError):
        evaluate_once(**kwargs)
    assert not kwargs['output_directory'].exists()
