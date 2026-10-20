"""Busca limitada em treino e comparação no holdout de validação existente."""

import json
import warnings
from dataclasses import dataclass

import numpy as np
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    average_precision_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.tree import DecisionTreeClassifier

from credit_risk.modeling.reference import default_probability, train_reference

VERSION = "credit-comparison-v1"
THRESHOLD = 0.5
CANDIDATES = (
    ("logistic_c1", "logistic", {"C": 1.0}),
    ("logistic_c01", "logistic", {"C": 0.1}),
    ("logistic_c10", "logistic", {"C": 10.0}),
    ("tree_depth3", "tree", {"max_depth": 3, "min_samples_leaf": 10}),
    ("tree_depth6", "tree", {"max_depth": 6, "min_samples_leaf": 10}),
    ("tree_depth10", "tree", {"max_depth": 10, "min_samples_leaf": 10}),
)


@dataclass
class ComparisonResult:
    """Modelos ajustados e relatório agregado; nenhuma persistência automática."""

    selected: object
    models: dict
    report: dict

    def report_json(self) -> str:
        """Serializa resultados sem linhas individuais ou valores não finitos."""
        return json.dumps(
            self.report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2
        )


def _scores(model, partition):
    probability = default_probability(model, partition.X)
    prediction = (probability >= THRESHOLD).astype(int)
    return {
        "roc_auc": float(roc_auc_score(partition.y, probability)),
        "average_precision": float(average_precision_score(partition.y, probability)),
        "precision": float(precision_score(partition.y, prediction, zero_division=0)),
        "recall": float(recall_score(partition.y, prediction, zero_division=0)),
        "predicted_positives": int(prediction.sum()),
    }


def compare_models(split, seed=42) -> ComparisonResult:
    """Compara seis configurações fixas sem acessar split.test.

    Recebe exclusivamente partições produzidas por split_data. O holdout
    existente preserva isolamento por cliente ou cronologia e expurgo.
    Não cria folds aleatórios, não reajusta sobre validação e não busca limiar.
    """
    if (
        isinstance(seed, bool)
        or not isinstance(seed, int)
        or not 0 <= seed < 2**32
    ):
        raise ValueError("Semente deve ser inteiro entre 0 e 2**32 - 1.")
    method = split.metadata.get("method")
    if method not in {"stratified_client", "temporal"}:
        raise ValueError("Use partições documentadas produzidas por split_data.")

    # Reutiliza as verificações e os pipelines existentes, inclusive a referência C=1.
    reference = train_reference(split, seed=seed)
    estimator_step = reference.logistic.steps[-1][0]
    models = {"dummy": reference.dummy}
    rows = [{
        "candidate": "dummy",
        "family": "dummy",
        "parameters": {"strategy": "prior"},
        **_scores(reference.dummy, split.validation),
    }]
    for name, family, parameters in CANDIDATES:
        if name == "logistic_c1":
            model = reference.logistic
        else:
            # clone remove todo estado aprendido, inclusive imputação e vocabulário.
            model = clone(reference.logistic)
            if family == "tree":
                estimator = DecisionTreeClassifier(random_state=seed, **parameters)
                model.set_params(**{estimator_step: estimator})
            else:
                model.set_params(**{
                    f"{estimator_step}__C": parameters["C"],
                })
            with warnings.catch_warnings():
                warnings.simplefilter("error", ConvergenceWarning)
                model.fit(split.train.X, split.train.y)
        models[name] = model
        rows.append({
            "candidate": name,
            "family": family,
            "parameters": parameters.copy(),
            **_scores(model, split.validation),
        })

    # Inclui Dummy na escolha para preservar resultados negativos.
    # Em empate exato, conserva C=1; depois Dummy; demais na ordem declarada.
    preference = ["logistic_c1", "dummy", *[
        name for name, _, _ in CANDIDATES if name != "logistic_c1"
    ]]
    selected_row = max(
        rows,
        key=lambda row: (
            row["average_precision"], -preference.index(row["candidate"])
        ),
    )
    baseline = next(row for row in rows if row["candidate"] == "logistic_c1")
    dummy = rows[0]
    for row in rows:
        row["ap_minus_reference"] = (
            row["average_precision"] - baseline["average_precision"]
        )
        row["ap_minus_dummy"] = row["average_precision"] - dummy["average_precision"]
    selected_name = selected_row["candidate"]
    report = {
        "comparison_version": VERSION,
        "seed": seed,
        "validation_method": method,
        "split_metadata": split.metadata,
        "reference_report": reference.report,
        "budget": {
            "logistic_configurations": 3,
            "tree_configurations": 3,
            "total_fits_including_dummy": 7,
            "tree_max_depth": 10,
        },
        "threshold": THRESHOLD,
        "positive_class": 1,
        "zero_division": 0,
        "train_observations": len(split.train.y),
        "validation_observations": len(split.validation.y),
        "train_prevalence": float(np.mean(split.train.y)),
        "validation_prevalence": float(np.mean(split.validation.y)),
        "table": rows,
        "selected_candidate": selected_name,
        "selection_reason": (
            "Maior average precision na validação entre as configurações fixadas e Dummy. "
            "Empates exatos seguem a preferência registrada; não há busca de limiar."
        ),
        "tie_preference": preference,
        "selected_above_reference": bool(
            selected_row["average_precision"] > baseline["average_precision"]
        ),
        "selected_above_dummy": bool(
            selected_row["average_precision"] > dummy["average_precision"]
        ),
        "limitations": [
            "A validação participa da seleção e não é uma estimativa final independente.",
            "O teste permanece reservado; nenhuma superioridade final foi demonstrada.",
            "Não há validação cruzada: usa-se o holdout existente sem alterar suas fronteiras.",
            "Metadados declarados não comprovam a procedência de partições manuais.",
            "Precisão sem positivos previstos é registrada como zero com denominador explícito.",
            "A seleção não exige melhoria sobre a regressão logística de referência.",
            "Divisão estratificada não demonstra generalização temporal.",
            "Reprodução exige os mesmos dados, partições, código e ambiente.",
        ],
    }
    return ComparisonResult(selected=models[selected_name], models=models, report=report)
