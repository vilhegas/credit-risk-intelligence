"""Cálculos e extremos com dados exclusivamente sintéticos."""

import json

import numpy as np
import pandas as pd
import pytest

from credit_risk.simulation.policies import Scenario, report_json, simulate_policies


def simulate(**changes):
    arguments = dict(
        y=[0, 1, 0, 1],
        probability=[0, 0.25, 0.5, 1],
        exposure=[100, 200, 300, 400],
        thresholds=[0, 0.5, 1],
        scenarios=[Scenario('base', 1, 0.5, 0.1)],
        dataset_version='synthetic-v1',
        model_version='fixed-v1',
        currency='NT$',
        horizon='um mês',
        exposure_assumption='Exposições sintéticas explicitamente fornecidas.',
    )
    arguments.update(changes)
    return simulate_policies(**arguments)


def test_known_formulas_and_strict_boundary():
    result = simulate()
    zero, middle, last = result['rows']
    assert zero['approved'] == 0
    assert zero['approved_default_rate'] is None
    assert zero['expected_loss'] == zero['expected_revenue'] == 0
    assert zero['default_recall'] == 1
    assert middle['approved'] == 2
    assert middle['approved_exposure'] == 300
    assert middle['approved_default_rate'] == 0.5
    assert middle['rejected_defaults'] == 1
    assert middle['default_recall'] == 0.5
    assert middle['expected_loss'] == pytest.approx(25)
    assert middle['expected_revenue'] == pytest.approx(25)
    assert middle['expected_margin_before_costs'] == pytest.approx(0)
    assert middle['historical_scenario_loss'] == 100
    assert middle['historical_scenario_revenue'] == 10
    assert middle['historical_scenario_margin_before_costs'] == -90
    assert last['approved'] == 3  # p=1 continua recusada no limiar 1.
    assert last['expected_loss'] == pytest.approx(100)
    assert json.loads(report_json(result)) == result
    assert simulate() == result


def test_all_approved_zero_exposure_and_zero_revenue():
    result = simulate(probability=[0, 0.25, 0.5, 0.9])
    assert result['rows'][-1]['approved'] == 4
    assert result['rows'][-1]['rejected_defaults'] == 0
    result = simulate(exposure=[0] * 4)
    assert all(row['expected_loss'] == row['expected_revenue'] == 0 for row in result['rows'])
    result = simulate(scenarios=[Scenario('sem_receita', 1, 1, 0)])
    assert result['rows'][1]['expected_loss'] == 50
    assert result['rows'][1]['expected_revenue'] == 0
    assert result['rows'][1]['expected_margin_before_costs'] == -50


def test_scenario_scaling_and_zero_lgd():
    result = simulate(scenarios=[
        Scenario('base', 1, 0.5, 0.1),
        Scenario('dobro', 2, 0.5, 0.1),
        Scenario('sem_perda', 1, 0, 0.1),
        Scenario('sem_exposicao', 0, 1, 1),
    ])
    base, doubled, no_loss, no_exposure = [result['rows'][i] for i in (1, 4, 7, 10)]
    assert doubled['expected_loss'] == 2 * base['expected_loss']
    assert doubled['expected_revenue'] == 2 * base['expected_revenue']
    assert no_loss['expected_loss'] == no_loss['historical_scenario_loss'] == 0
    assert no_exposure['approved_exposure'] == 0
    assert {row['approved'] for row in (base, doubled, no_loss, no_exposure)} == {2}


@pytest.mark.parametrize('changes', [
    {'y': []},
    {'y': [0, 0, 0, 0]},
    {'y': [0, 1, 0, 0.5]},
    {'probability': [0, np.nan, 0.5, 1]},
    {'probability': [0, 0.2, 0.5, 1.1]},
    {'probability': [True, 0.2, 0.5, 1]},
    {'exposure': [-1, 200, 300, 400]},
    {'exposure': [100]},
    {'exposure': [[100, 200, 300, 400]]},
    {'thresholds': [0, 0.5, 0.5]},
    {'thresholds': [0, 0.5, np.inf]},
    {'scenarios': []},
    {'scenarios': [Scenario('erro', 1, 1.1, 0)]},
    {'scenarios': [Scenario('erro', -1, 0.5, 0)]},
    {'scenarios': [Scenario('erro', 1, 0.5, np.nan)]},
    {'scenarios': [Scenario('igual', 1, 0, 0), Scenario('igual', 2, 1, 1)]},
    {'currency': ''},
    {'exposure_assumption': ' '},
    {'exposure': [1e308] * 4},
])
def test_invalid_contract(changes):
    with pytest.raises(ValueError):
        simulate(**changes)


def test_alignment_and_input_preservation():
    labels = pd.Series([0, 1, 0, 1], index=[4, 3, 2, 1])
    probabilities = pd.Series([0, 0.25, 0.5, 1], index=labels.index)
    exposures = pd.Series([100, 200, 300, 400], index=labels.index)
    originals = [value.copy(deep=True) for value in (labels, probabilities, exposures)]
    simulate(y=labels, probability=probabilities, exposure=exposures)
    for value, original in zip((labels, probabilities, exposures), originals, strict=True):
        pd.testing.assert_series_equal(value, original)
    with pytest.raises(ValueError, match='Índices'):
        simulate(y=labels, probability=probabilities.reset_index(drop=True), exposure=exposures)
