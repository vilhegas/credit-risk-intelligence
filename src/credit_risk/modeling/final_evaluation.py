"""Avaliação agregada de previsões congeladas, sem seleção ou treinamento."""

import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_auc_score,
)


def _vector(values, *, target=False):
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.dtype.kind not in 'iuf':
        raise ValueError('Informe vetores numéricos unidimensionais, sem booleanos.')
    result = raw.astype(float)
    if not np.isfinite(result).all():
        raise ValueError('Valores devem ser finitos.')
    if target:
        if set(result.tolist()) != {0.0, 1.0}:
            raise ValueError('Ambas as classes binárias são obrigatórias.')
    elif ((result < 0) | (result > 1)).any():
        raise ValueError('Probabilidades devem estar entre zero e um.')
    return result


def _scores(y, probability, baseline, threshold):
    tn, fp, fn, tp = map(int, confusion_matrix(
        y, probability >= threshold, labels=[0, 1]
    ).ravel())
    approved = tn + fn
    precision = tp / (tp + fp) if tp + fp else None
    ap = float(average_precision_score(y, probability))
    dummy_ap = float(average_precision_score(y, baseline))
    return {
        'observations': len(y),
        'prevalence': float(y.mean()),
        'average_precision': ap,
        'baseline_average_precision': dummy_ap,
        'average_precision_difference': ap - dummy_ap,
        'roc_auc': float(roc_auc_score(y, probability)),
        'baseline_roc_auc': float(roc_auc_score(y, baseline)),
        'brier_score': float(brier_score_loss(y, probability)),
        'baseline_brier_score': float(brier_score_loss(y, baseline)),
        'precision': precision,
        'recall': tp / (tp + fn),
        'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        'confusion_matrix': [[tn, fp], [fn, tp]],
        'approval_rate': approved / len(y),
        'approved_default_rate': fn / approved if approved else None,
    }


def evaluate_once(
    y,
    probability,
    baseline_probability,
    *,
    threshold,
    frozen_manifest,
    output_directory,
    resamples=1000,
    seed=42,
):
    """Reserva uma saída inédita antes do cálculo; falhas também consomem a reserva.

    Probabilidades devem incluir a calibração congelada, aplicada uma única vez.
    A exclusividade é local ao diretório, não uma garantia contra cópias dos dados.
    """
    y = _vector(y, target=True)
    probability = _vector(probability)
    baseline = _vector(baseline_probability)
    if len(y) != len(probability) or len(y) != len(baseline):
        raise ValueError('Vetores devem estar alinhados e ter o mesmo tamanho.')
    if isinstance(threshold, bool | np.bool_) or not isinstance(
        threshold, int | float
    ) or not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Limiar inválido.')
    if type(resamples) is not int or not 100 <= resamples <= 10000:
        raise ValueError('Use entre 100 e 10000 reamostragens.')
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('Semente inválida.')
    required = {
        'dataset_sha256', 'partition_sha256', 'model_sha256',
        'policy_sha256', 'code_revision', 'environment', 'frozen_at_utc',
    }
    if not isinstance(frozen_manifest, dict) or not required <= frozen_manifest.keys():
        raise ValueError('Manifesto congelado incompleto.')
    if any(not isinstance(frozen_manifest[key], str) or not frozen_manifest[key].strip()
           for key in required):
        raise ValueError('Metadados obrigatórios devem ser textos não vazios.')
    for key in required & {
        'dataset_sha256', 'partition_sha256', 'model_sha256', 'policy_sha256'
    }:
        value = frozen_manifest[key]
        if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('SHA-256 inválido.')
    manifest_json = json.dumps(frozen_manifest, sort_keys=True, allow_nan=False)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'RESERVED.json').write_text(manifest_json, encoding='utf-8')
    metrics = _scores(y, probability, baseline, threshold)
    rng = np.random.default_rng(seed)
    keys = (
        'average_precision', 'baseline_average_precision',
        'average_precision_difference', 'roc_auc', 'brier_score',
        'approval_rate', 'approved_default_rate', 'precision', 'recall', 'f1',
    )
    samples = {key: [] for key in keys}
    skipped = 0
    for _ in range(resamples):
        positions = rng.integers(0, len(y), len(y))
        if len(np.unique(y[positions])) != 2:
            skipped += 1
            continue
        scores = _scores(y[positions], probability[positions], baseline[positions], threshold)
        for key in keys:
            if scores[key] is not None:
                samples[key].append(scores[key])
    intervals = {}
    for key, values in samples.items():
        intervals[key] = {
            'valid_resamples': len(values),
            'lower': float(np.quantile(values, 0.025)) if values else None,
            'upper': float(np.quantile(values, 0.975)) if values else None,
        }
    edges = np.linspace(0, 1, 11)
    groups = np.searchsorted(edges[1:-1], probability)
    curve = []
    for index in range(10):
        mask = groups == index
        if mask.any():
            curve.append({
                'bin': index,
                'count': int(mask.sum()),
                'mean_probability': float(probability[mask].mean()),
                'default_rate': float(y[mask].mean()),
            })
    report = {
        'version': 'final-evaluation-v1',
        'manifest': json.loads(manifest_json),
        'manifest_sha256': hashlib.sha256(manifest_json.encode()).hexdigest(),
        'threshold': threshold,
        'metrics': metrics,
        'calibration_curve': curve,
        'above_baseline_descriptive': metrics['average_precision_difference'] > 0,
        'uncertainty': {
            'method': 'bootstrap pareado por observação, percentil pontual de 95%',
            'seed': seed,
            'requested_resamples': resamples,
            'single_class_resamples_skipped': skipped,
            'intervals': intervals,
        },
        'limitations': [
            'Exige uma observação independente por cliente e alinhamento externo.',
            'Hashes e congelamento são declarações do chamador, não atestações.',
            'Bootstrap mantém modelo e política fixos; não inclui incerteza do ajuste.',
            'Intervalos não demonstram generalização temporal, causalidade ou equidade.',
            'Resultado negativo deve ser preservado sem reajuste orientado pelo teste.',
        ],
    }
    (output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False),
        encoding='utf-8',
    )
    return report
