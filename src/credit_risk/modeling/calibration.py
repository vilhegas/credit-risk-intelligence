"""Calibração em desenvolvimento e seleção explícita de política de crédito."""

import json
from dataclasses import asdict, dataclass
from numbers import Real

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss


def _number(value, name, minimum=0.0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name}: número real obrigatório.')
    value = float(value)
    if not np.isfinite(value) or value < minimum:
        raise ValueError(f'{name}: valor inválido.')
    if maximum is not None and value > maximum:
        raise ValueError(f'{name}: valor inválido.')
    return value


def _probabilities(values):
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size == 0 or raw.dtype.kind not in 'iuf':
        raise ValueError('Probabilidades devem formar um vetor numérico não vazio.')
    result = raw.astype(float, copy=True)
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError('Probabilidades inválidas.')
    return result


def _observations(y, probability):
    probability = _probabilities(probability)
    target = np.asarray(y)
    if target.ndim != 1 or target.shape != probability.shape:
        raise ValueError('Alvo e probabilidades devem estar alinhados.')
    if target.dtype.kind not in 'biuf' or not np.isin(target, [0, 1]).all():
        raise ValueError('Alvo deve ser binário.')
    if set(target.tolist()) != {0, 1}:
        raise ValueError('Ambas as classes são obrigatórias.')
    return target.astype(int), probability


def _logits(probability):
    clipped = np.clip(probability, 1e-6, 1 - 1e-6)
    return np.log(clipped / (1 - clipped)).reshape(-1, 1)


@dataclass(frozen=True)
class Policy:
    """Parâmetros escalares congelados; nenhuma adaptação durante avaliação."""

    threshold: float
    false_negative_cost: float
    false_positive_cost: float
    min_approval_rate: float
    min_default_recall: float
    calibration_method: str = 'identity'
    slope: float = 1.0
    intercept: float = 0.0

    def __post_init__(self):
        for name in ('threshold', 'min_approval_rate', 'min_default_recall'):
            _number(getattr(self, name), name, maximum=1)
        for name in ('false_negative_cost', 'false_positive_cost'):
            _number(getattr(self, name), name)
        if self.calibration_method not in {'identity', 'sigmoid'}:
            raise ValueError('Método de calibração inválido.')
        for value in (self.slope, self.intercept):
            if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
                raise ValueError('Coeficientes inválidos.')

    def probabilities(self, raw_probability):
        probability = _probabilities(raw_probability)
        if self.calibration_method == 'identity':
            return probability
        score = self.slope * _logits(probability).ravel() + self.intercept
        return np.exp(-np.logaddexp(0, -score))

    def report_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, allow_nan=False)


def calibration_report(y, probability, *, bins=10):
    """Brier e curva uniforme, com denominadores e intervalos vazios omitidos."""
    target, probability = _observations(y, probability)
    if isinstance(bins, bool) or not isinstance(bins, int) or not 2 <= bins <= 100:
        raise ValueError('Quantidade de intervalos inválida.')
    observed, predicted = calibration_curve(
        target, probability, n_bins=bins, strategy='uniform'
    )
    boundaries = np.linspace(0, 1, bins + 1)
    assignments = np.searchsorted(boundaries[1:-1], probability)
    counts = np.bincount(assignments, minlength=bins)
    occupied = np.flatnonzero(counts)
    return {
        'observations': len(target),
        'brier_score': float(brier_score_loss(target, probability)),
        'strategy': 'uniform',
        'bins_requested': bins,
        'curve': [
            {
                'bin': int(index),
                'count': int(counts[index]),
                'mean_probability': float(mean),
                'default_rate': float(rate),
            }
            for index, mean, rate in zip(occupied, predicted, observed, strict=True)
        ],
    }


def evaluate_policy(policy, y, raw_probability):
    """Recusar quando p >= limiar; positivo significa inadimplência prevista."""
    target, raw = _observations(y, raw_probability)
    probability = policy.probabilities(raw)
    refused = probability >= policy.threshold
    positive = target == 1
    tp = int(np.sum(refused & positive))
    fp = int(np.sum(refused & ~positive))
    fn = int(np.sum(~refused & positive))
    tn = int(np.sum(~refused & ~positive))
    total_cost = fn * policy.false_negative_cost + fp * policy.false_positive_cost
    approved = tn + fn
    return {
        'threshold': float(policy.threshold),
        'observations': len(target),
        'confusion_matrix': [[tn, fp], [fn, tp]],
        'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
        'approved': approved,
        'approval_rate': approved / len(target),
        'approved_default_rate': fn / approved if approved else None,
        'default_recall': tp / (tp + fn),
        'total_cost': total_cost,
        'mean_cost': total_cost / len(target),
    }


def _keys(values, expected):
    keys = tuple(values)
    if len(keys) != expected or not all(isinstance(key, str) and key.strip() for key in keys):
        raise ValueError('Chaves de cliente devem ser strings alinhadas e não vazias.')
    return set(keys)


def select_policy(
    calibration_y,
    calibration_probability,
    selection_y,
    selection_probability,
    *,
    calibration_clients,
    selection_clients,
    thresholds,
    false_negative_cost,
    false_positive_cost,
    min_approval_rate,
    min_default_recall,
    minimum_brier_gain,
    development_version,
):
    """Ajustar sigmoid em calibração e escolher em seleção, sem receber teste."""
    if not isinstance(development_version, str) or not development_version.strip():
        raise ValueError('Versão de desenvolvimento obrigatória.')
    cy, cp = _observations(calibration_y, calibration_probability)
    sy, sp = _observations(selection_y, selection_probability)
    calibration_keys = _keys(calibration_clients, len(cy))
    selection_keys = _keys(selection_clients, len(sy))
    if calibration_keys & selection_keys:
        raise ValueError('Clientes de calibração e seleção devem ser disjuntos.')
    gain = _number(minimum_brier_gain, 'Ganho mínimo de Brier')
    candidates = tuple(sorted({
        _number(value, 'Limiar', maximum=1) for value in thresholds
    }))
    if not candidates:
        raise ValueError('Forneça pelo menos um limiar explícito.')
    base = Policy(
        candidates[0], false_negative_cost, false_positive_cost,
        min_approval_rate, min_default_recall,
    )
    calibrator = LogisticRegression(C=1.0, solver='lbfgs', max_iter=2000)
    calibrator.fit(_logits(cp), cy)
    if int(calibrator.n_iter_[0]) >= calibrator.max_iter:
        raise ValueError('Calibração sem convergência confirmada.')
    sigmoid = Policy(
        **{**asdict(base), 'calibration_method': 'sigmoid',
           'slope': float(calibrator.coef_[0, 0]),
           'intercept': float(calibrator.intercept_[0])}
    )
    before = calibration_report(sy, sp)
    after = calibration_report(sy, sigmoid.probabilities(sp))
    improvement = before['brier_score'] - after['brier_score']
    chosen = sigmoid if improvement > gain else base
    rows = []
    feasible = []
    for threshold in candidates:
        policy = Policy(**{**asdict(chosen), 'threshold': threshold})
        row = evaluate_policy(policy, sy, sp)
        row['feasible'] = (
            row['approval_rate'] >= min_approval_rate
            and row['default_recall'] >= min_default_recall
        )
        rows.append(row)
        if row['feasible']:
            feasible.append((policy, row))
    if not feasible:
        raise ValueError('Nenhum limiar atende às restrições explícitas.')
    frozen, selected = min(
        feasible, key=lambda item: (item[1]['total_cost'], item[0].threshold)
    )
    report = {
        'version': 'credit-calibration-v1',
        'development_version': development_version,
        'calibration_observations': len(cy),
        'selection_observations': len(sy),
        'minimum_brier_gain': gain,
        'observed_brier_gain': improvement,
        'before': before,
        'sigmoid_candidate': after,
        'calibration_selected': frozen.calibration_method,
        'policy': asdict(frozen),
        'threshold_table': rows,
        'selected': selected,
        'tie_break': 'Menor custo total; depois menor limiar.',
        'limitations': [
            'Seleção compartilhada de calibração e limiar pode produzir otimismo.',
            'Custos são unidades hipotéticas declaradas, não perda financeira estimada.',
            'Teste final reservado; nenhuma métrica final calculada nesta seleção.',
        ],
    }
    json.dumps(report, allow_nan=False)
    return frozen, report
