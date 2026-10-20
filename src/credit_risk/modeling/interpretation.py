"""Interpretação por permutação e avaliação agregada, sem ajuste de modelos."""

import json
from numbers import Integral

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from credit_risk.ingestion.uci import FEATURES
from credit_risk.modeling.reference import default_probability


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} deve ser inteiro >= {minimum}.")


def _vectors(y, probability):
    labels = np.asarray(y)
    raw = np.asarray(probability)
    if labels.ndim != 1 or raw.ndim != 1 or not len(labels):
        raise ValueError("Forneça vetores unidimensionais não vazios.")
    if len(labels) != len(raw):
        raise ValueError("Alvos e probabilidades devem estar alinhados.")
    if labels.dtype.kind not in "iuf" or not np.isin(labels, [0, 1]).all():
        raise ValueError("Alvo deve conter somente 0 e 1 numéricos.")
    if raw.dtype.kind not in "iuf":
        raise ValueError("Probabilidades devem ser numéricas.")
    values = raw.astype(float)
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("Probabilidades devem ser finitas entre zero e um.")
    return labels.astype(int), values


def _model_probability(model, frame):
    """Aceita pipelines existentes e classificadores binários já ajustados."""
    if hasattr(model, "named_steps"):
        return default_probability(model, frame)
    classes = np.asarray(getattr(model, "classes_", None))
    if (
        classes.ndim != 1
        or len(classes) != 2
        or classes.dtype.kind not in "iuf"
        or not np.array_equal(np.sort(classes), [0, 1])
    ):
        raise ValueError("Modelo deve possuir as classes numéricas 0 e 1.")
    if not callable(getattr(model, "predict_proba", None)):
        raise ValueError("Modelo deve implementar predict_proba.")
    probabilities = np.asarray(model.predict_proba(frame))
    if probabilities.shape != (len(frame), len(classes)):
        raise ValueError(
            "predict_proba deve retornar uma coluna por classe e uma linha por observação."
        )
    if probabilities.dtype.kind not in "iuf":
        raise ValueError("Probabilidades devem ser numéricas.")
    if (
        not np.isfinite(probabilities).all()
        or ((probabilities < 0) | (probabilities > 1)).any()
        or not np.allclose(probabilities.sum(axis=1), 1)
    ):
        raise ValueError("Probabilidades devem ser finitas entre zero e um e somar um por linha.")
    return probabilities[:, int(np.flatnonzero(classes == 1)[0])]


def permutation_report(model, X, y, *, dataset_version, repeats=20, seed=42):
    """Queda de average precision ao permutar cada atributo financeiro original."""
    _integer(repeats, "repeats", 2)
    _integer(seed, "seed", 0)
    if seed > 2**32 - 1:
        raise ValueError("Semente fora do intervalo permitido.")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("Informe dataset_version.")
    if not isinstance(X, pd.DataFrame) or not X.columns.is_unique:
        raise ValueError("X deve ser DataFrame com colunas únicas.")
    if not set(FEATURES).issubset(X.columns):
        raise ValueError("Faltam atributos financeiros.")
    if isinstance(y, pd.Series) and not X.index.equals(y.index):
        raise ValueError("Índices de X e y devem estar alinhados.")
    frame = X.loc[:, list(FEATURES)].copy(deep=True)
    labels, probability = _vectors(y, _model_probability(model, frame))
    if len(frame) != len(labels) or len(np.unique(labels)) != 2:
        raise ValueError("Ambas as classes são necessárias para interpretação.")
    baseline = float(average_precision_score(labels, probability))
    rng = np.random.default_rng(seed)
    factors = []
    for feature in FEATURES:
        decreases = []
        for _ in range(repeats):
            shuffled = frame.copy(deep=True)
            shuffled[feature] = frame[feature].iloc[rng.permutation(len(frame))].array
            _, permuted = _vectors(labels, _model_probability(model, shuffled))
            decreases.append(baseline - float(average_precision_score(labels, permuted)))
        factors.append(
            {
                "feature": feature,
                "mean_ap_decrease": float(np.mean(decreases)),
                "permutation_std": float(np.std(decreases, ddof=1)),
                "permutation_quantiles_025_975": np.quantile(decreases, [0.025, 0.975]).tolist(),
            }
        )
    factors.sort(key=lambda row: (-row["mean_ap_decrease"], row["feature"]))
    return {
        "version": "permutation-v1",
        "dataset_version": dataset_version,
        "observations": len(frame),
        "baseline_average_precision": baseline,
        "repeats": int(repeats),
        "seed": int(seed),
        "factors": factors,
        "limitations": [
            "Importância preditiva não demonstra causalidade nem direção de efeito.",
            "Atributos correlacionados podem compartilhar ou ocultar importância.",
            "Permutações podem gerar combinações financeiras pouco plausíveis.",
            "Dispersão entre permutações não é intervalo de confiança populacional.",
        ],
    }


def _wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    rate = successes / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / total + z * z / (4 * total**2)) / denominator
    return [float(max(0, center - radius)), float(min(1, center + radius))]


def _rate(successes, total):
    return {
        "numerator": int(successes),
        "denominator": int(total),
        "value": float(successes / total) if total else None,
        "wilson_95": _wilson(successes, total),
    }


def _metrics(y, p, threshold, bins):
    predicted = p >= threshold
    positives = int(y.sum())
    negatives = len(y) - positives
    tp = int(((y == 1) & predicted).sum())
    fp = int(((y == 0) & predicted).sum())
    fn, tn = positives - tp, negatives - fp
    curve = []
    # Fronteiras internas pertencem ao intervalo inferior, como no Scikit-learn.
    assigned = np.searchsorted(np.linspace(0, 1, bins + 1)[1:-1], p)
    for index in range(bins):
        mask = assigned == index
        if mask.any():
            count = int(mask.sum())
            curve.append(
                {
                    "bin": index,
                    "count": count,
                    "mean_probability": float(p[mask].mean()),
                    "observed": _rate(int(y[mask].sum()), count),
                }
            )
    return {
        "average_precision": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier_score": float(brier_score_loss(y, p)),
        "mean_probability": float(p.mean()),
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "false_positive_rate": _rate(fp, negatives),
        "false_negative_rate": _rate(fn, positives),
        "default_recall": _rate(tp, positives),
        "precision": _rate(tp, tp + fp),
        "approval_rate": _rate(tn + fn, len(y)),
        "approved_default_rate": _rate(fn, tn + fn),
        "calibration_curve": curve,
    }


def segment_report(
    y,
    probability,
    segments,
    *,
    dataset_version,
    threshold,
    minimum_size=100,
    minimum_class_count=20,
    bins=10,
):
    """Avalia probabilidades finais já calibradas e limiar previamente congelado."""
    _integer(minimum_size, "minimum_size", 2)
    _integer(minimum_class_count, "minimum_class_count", 1)
    _integer(bins, "bins", 1)
    if bins > 100:
        raise ValueError("bins deve ser <= 100.")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("Informe dataset_version.")
    if isinstance(threshold, bool) or not isinstance(threshold, int | float):
        raise ValueError("Limiar deve ser numérico.")
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Limiar deve estar entre zero e um.")
    indexed = [item for item in (y, probability, segments) if isinstance(item, pd.Series)]
    if indexed and any(not item.index.equals(indexed[0].index) for item in indexed[1:]):
        raise ValueError("Índices devem estar alinhados.")
    labels, values = _vectors(y, probability)
    groups = np.asarray(segments, dtype=object)
    if groups.ndim != 1 or len(groups) != len(labels):
        raise ValueError("Segmentos devem estar alinhados aos alvos.")
    if any(not isinstance(item, str) or not item.strip() for item in groups):
        raise ValueError("Use rótulos textuais não vazios; nomeie ausências explicitamente.")
    if len(np.unique(labels)) != 2:
        raise ValueError("Ambas as classes são necessárias na amostra global.")
    overall = _metrics(labels, values, threshold, bins)
    rows = []
    for name in sorted(set(groups)):
        mask = groups == name
        target, probabilities = labels[mask], values[mask]
        count, defaults = len(target), int(target.sum())
        sufficient = (
            count >= minimum_size and min(defaults, count - defaults) >= minimum_class_count
        )
        row = {
            "segment": name,
            "observations": count,
            "defaults": defaults,
            "non_defaults": count - defaults,
            "sufficient": sufficient,
            "metrics": None,
            "differences_from_overall": None,
            "reason": None if sufficient else "Amostra ou contagens por classe insuficientes.",
        }
        if sufficient:
            metrics = _metrics(target, probabilities, threshold, bins)
            row["metrics"] = metrics
            row["differences_from_overall"] = {
                metric: metrics[metric] - overall[metric]
                for metric in ("average_precision", "roc_auc", "brier_score")
            }
        rows.append(row)
    return {
        "version": "segments-v1",
        "dataset_version": dataset_version,
        "threshold": float(threshold),
        "minimum_size": int(minimum_size),
        "minimum_class_count": int(minimum_class_count),
        "bins": int(bins),
        "overall": overall,
        "segments": rows,
        "limitations": [
            "Diferenças são descritivas e não demonstram equidade, discriminação ou causalidade.",
            "Diferenças frente ao global comparam amostras sobrepostas; "
            "não são testes estatísticos.",
            "Average precision depende da prevalência de cada segmento.",
            "Wilson pressupõe observações independentes; não corrige clientes repetidos.",
            "Intervalos são pontuais, sem correção por comparações múltiplas.",
            "Não há intervalos populacionais para AP, AUC, Brier ou suas diferenças.",
            "Amostra suficiente pela regra não garante representatividade ou poder estatístico.",
            "Sem dados demográficos adequados, esta análise financeira não avalia equidade.",
        ],
    }


def report_json(report):
    """Serializa agregados sem aceitar NaN ou infinito."""
    return json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False)
