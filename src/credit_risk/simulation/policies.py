"""Simulação retrospectiva de políticas, sem ajuste ou entrada e saída."""

import json
from dataclasses import dataclass
from numbers import Real

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Scenario:
    """Hipóteses monetárias para um mesmo horizonte e uma mesma moeda."""

    name: str
    exposure_multiplier: float
    lgd: float
    revenue_rate: float


def _number(value, name, *, maximum=None):
    if isinstance(value, bool | np.bool_) or not isinstance(value, Real):
        raise ValueError(f'{name}: informar número real.')
    value = float(value)
    if not np.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f'{name}: valor fora do domínio finito permitido.')
    return value


def _vector(values, name, *, maximum=None):
    raw = np.asarray(values, dtype=object)
    if raw.ndim != 1 or not len(raw):
        raise ValueError(f'{name}: informar vetor não vazio.')
    return np.array([_number(value, name, maximum=maximum) for value in raw], dtype=float)


def _total(values):
    with np.errstate(over='ignore', invalid='ignore'):
        result = float(np.sum(values))
    if not np.isfinite(result):
        raise ValueError('Cálculo monetário excede a representação numérica finita.')
    return result


def simulate_policies(
    y,
    probability,
    exposure,
    *,
    thresholds,
    scenarios,
    dataset_version,
    model_version,
    currency,
    horizon,
    exposure_assumption,
):
    """Compara limiares explícitos sobre entradas posicionais já congeladas.

    Aprovação: probability < threshold. Receita ocorre somente sem default.
    A exposição fornecida é uma hipótese explícita, não inferida do limite.
    """
    metadata = {
        'dataset_version': dataset_version,
        'model_version': model_version,
        'currency': currency,
        'horizon': horizon,
        'exposure_assumption': exposure_assumption,
    }
    if any(not isinstance(value, str) or not value.strip() for value in metadata.values()):
        raise ValueError('Metadados e hipótese de exposição devem ser textos não vazios.')
    series = [value for value in (y, probability, exposure) if isinstance(value, pd.Series)]
    if series and any(not value.index.equals(series[0].index) for value in series[1:]):
        raise ValueError('Índices das séries devem ser idênticos e alinhados.')
    labels = _vector(y, 'Alvo', maximum=1)
    if not np.isin(labels, [0, 1]).all() or set(labels) != {0, 1}:
        raise ValueError('Ambas as classes binárias são necessárias.')
    probabilities = _vector(probability, 'Probabilidade', maximum=1)
    exposures = _vector(exposure, 'Exposição')
    if len(labels) != len(probabilities) or len(labels) != len(exposures):
        raise ValueError('Entradas devem ter o mesmo comprimento.')
    limits = sorted(set(_vector(thresholds, 'Limiar', maximum=1).tolist()))
    if len(limits) < 3:
        raise ValueError('Informar pelo menos três limiares distintos.')
    configurations = list(scenarios)
    if not configurations or any(not isinstance(item, Scenario) for item in configurations):
        raise ValueError('Informar cenários Scenario explícitos.')
    names = set()
    validated = []
    for item in configurations:
        if not isinstance(item.name, str) or not item.name.strip() or item.name in names:
            raise ValueError('Cada cenário deve ter nome não vazio e exclusivo.')
        names.add(item.name)
        validated.append({
            'name': item.name,
            'exposure_multiplier': _number(item.exposure_multiplier, 'Multiplicador'),
            'lgd': _number(item.lgd, 'LGD', maximum=1),
            'revenue_rate': _number(item.revenue_rate, 'Taxa de receita'),
        })
    rows = []
    count = len(labels)
    defaults = int(labels.sum())
    for scenario in validated:
        with np.errstate(over='ignore', invalid='ignore'):
            ead = exposures * scenario['exposure_multiplier']
            loss_if_default = ead * scenario['lgd']
            revenue_if_performing = ead * scenario['revenue_rate']
        if not all(np.isfinite(value).all() for value in (
            ead, loss_if_default, revenue_if_performing,
        )):
            raise ValueError('Cálculo monetário excede a representação numérica finita.')
        for threshold in limits:
            approved = probabilities < threshold
            approved_count = int(approved.sum())
            approved_defaults = int(labels[approved].sum())
            expected_loss = _total((probabilities * loss_if_default)[approved])
            expected_revenue = _total(((1 - probabilities) * revenue_if_performing)[approved])
            historical_loss = _total((labels * loss_if_default)[approved])
            historical_revenue = _total(((1 - labels) * revenue_if_performing)[approved])
            rows.append({
                'scenario': scenario['name'],
                'threshold': threshold,
                'observations': count,
                'approved': approved_count,
                'rejected': count - approved_count,
                'approval_rate': approved_count / count,
                'approved_defaults': approved_defaults,
                'approved_default_rate': (
                    approved_defaults / approved_count if approved_count else None
                ),
                'rejected_defaults': defaults - approved_defaults,
                'default_recall': (defaults - approved_defaults) / defaults,
                'approved_exposure': _total(ead[approved]),
                'expected_loss': expected_loss,
                'expected_revenue': expected_revenue,
                'expected_margin_before_costs': expected_revenue - expected_loss,
                'historical_scenario_loss': historical_loss,
                'historical_scenario_revenue': historical_revenue,
                'historical_scenario_margin_before_costs': historical_revenue - historical_loss,
            })
    return {
        'simulation_version': 'credit-policy-v1',
        **metadata,
        'thresholds': limits,
        'scenarios': validated,
        'observations': count,
        'defaults': defaults,
        'rows': rows,
        'limitations': [
            'Comparação descritiva; não estima efeito causal de políticas.',
            'Clientes historicamente aprovados introduzem viés de seleção; '
            'não há resultados observados dos solicitantes historicamente recusados.',
            'Probabilidades e desfechos permanecem fixos entre cenários; '
            'não se modela resposta do risco à mudança de exposição.',
            'Exposição, LGD e receita são hipóteses, não valores realizados da fonte.',
            'Margem exclui custos de captação, operação, tributos e capital; não é lucro.',
        ],
    }


def report_json(report):
    """Serializa somente agregados em memória, rejeitando NaN e infinito."""
    return json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False)
