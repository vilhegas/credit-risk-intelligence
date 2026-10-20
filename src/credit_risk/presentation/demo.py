"""Serviços da demonstração local, sem arquivos externos ou logs de entradas."""

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from credit_risk.ingestion.uci import FEATURES, PAY, TARGET
from credit_risk.modeling.reference import default_probability, train_reference
from credit_risk.modeling.splitting import split_data
from credit_risk.simulation.policies import Scenario, simulate_policies

MODEL_VERSION = "demo-logistic-synthetic-v1"
DATASET_VERSION = "demo-synthetic-v1"
MONEY_LIMIT = 1_000_000_000


def demonstration_frame():
    """Cria dados artificiais determinísticos, sem identificadores reais."""
    rng = np.random.default_rng(42)
    count = 400
    frame = pd.DataFrame(index=range(count))
    delay = rng.integers(1, 5, count)
    for name in FEATURES:
        if name in PAY:
            frame[name] = pd.Series(delay, dtype="string")
        else:
            frame[name] = rng.integers(0, 200001, count)
    frame["ID"] = np.arange(count) + 1
    probability = 0.1 + 0.18 * (delay - 1)
    frame[TARGET] = (rng.random(count) < probability).astype(int)
    return frame


@lru_cache(maxsize=1)
def _bundle():
    """Ajusta somente código local conhecido; nunca desserializa estimadores."""
    split = split_data(demonstration_frame(), DATASET_VERSION)
    model = train_reference(split).logistic
    probability = default_probability(model, split.validation.X)
    return model, split.validation.y.to_numpy(copy=True), probability


def example_record():
    return {name: "1" if name in PAY else 10000 for name in FEATURES}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("O JSON contém campos repetidos.")
        result[key] = value
    return result


def parse_record(text):
    """Aceita exatamente os atributos financeiros, com limites explícitos."""
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError("Informe um objeto JSON com até 10.000 caracteres.")
    try:
        record = json.loads(text, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RecursionError):
        raise ValueError("JSON inválido. Use um objeto com os 19 campos financeiros.") from None
    if not isinstance(record, dict) or set(record) != set(FEATURES):
        raise ValueError("Informe exatamente os 19 campos do exemplo, sem campos adicionais.")
    cleaned = {}
    for name in FEATURES:
        value = record[name]
        if name in PAY:
            if isinstance(value, str) and value in {str(i) for i in range(1, 10)} | {"-1"}:
                cleaned[name] = value
            elif isinstance(value, str) and value in {
                "nao_documentado:-2", "nao_documentado:0"
            }:
                cleaned[name] = value
            else:
                raise ValueError(
                    f"{name}: use uma categoria textual -1, 1 a 9, "
                    "nao_documentado:-2 ou nao_documentado:0."
                )
        else:
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not -MONEY_LIMIT <= value <= MONEY_LIMIT
                or value != int(value)
            ):
                raise ValueError(
                    f"{name}: informe um inteiro entre -1.000.000.000 e 1.000.000.000."
                )
            cleaned[name] = int(value)
    return pd.DataFrame([cleaned], columns=FEATURES)


def predict_record(text):
    record = parse_record(text)
    model, _, _ = _bundle()
    return float(default_probability(model, record)[0])


def indicators():
    _, y, _ = _bundle()
    return {
        "observations": len(y),
        "defaults": int(y.sum()),
        "default_rate": float(y.mean()),
    }


def explore_policies(thresholds, exposure, lgd, revenue_rate):
    _, y, probability = _bundle()
    return simulate_policies(
        y=y,
        probability=probability,
        exposure=np.full(len(y), exposure),
        thresholds=thresholds,
        scenarios=[Scenario("demonstracao", 1, lgd, revenue_rate)],
        dataset_version=DATASET_VERSION,
        model_version=MODEL_VERSION,
        currency="unidade hipotética",
        horizon="um mês hipotético",
        exposure_assumption="Exposição artificial constante; independente de LIMIT_BAL.",
    )
