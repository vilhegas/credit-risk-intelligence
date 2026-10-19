"""Pipelines de referência ajustados exclusivamente no treino."""

import json
import platform
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from credit_risk.ingestion.uci import FEATURES, PAY

VERSION = "uci-350-reference-v1"
AMOUNTS = tuple(name for name in FEATURES if name not in PAY)


def normalize_features(frame):
    """Adapta tipos anuláveis sem aprender parâmetros ou alterar a entrada."""
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("Forneça um DataFrame com os atributos financeiros.")
    if not frame.columns.is_unique or not set(FEATURES).issubset(frame.columns):
        raise ValueError("Os 19 atributos financeiros devem estar presentes e únicos.")
    result = pd.DataFrame(index=frame.index)
    for name in AMOUNTS:
        values = frame[name]
        if any(isinstance(value, bool | np.bool_) for value in values.dropna()):
            raise ValueError(f"Booleano inválido em {name}.")
        try:
            numeric = pd.to_numeric(values, errors="raise")
            if np.iscomplexobj(numeric.to_numpy()):
                raise ValueError("Valor complexo.")
            array = numeric.to_numpy(dtype=float, na_value=np.nan)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Valores monetários inválidos em {name}.") from exc
        if np.isinf(array).any() or not np.array_equal(np.isnan(array), values.isna()):
            raise ValueError(f"Valores monetários inválidos em {name}.")
        result[name] = array
    for name in PAY:
        values = frame[name].astype("string")
        result[name] = values.astype(object).where(values.notna(), np.nan)
    return result.loc[:, list(FEATURES)]


def build_pipeline(classifier):
    """Cria transformadores novos para cada estimador, sem ajuste antecipado."""
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return Pipeline([
        ("normalize", FunctionTransformer(normalize_features, validate=False)),
        ("columns", ColumnTransformer([
            ("numeric", numeric, list(AMOUNTS)),
            ("categorical", categorical, list(PAY)),
        ], remainder="drop")),
        ("classifier", classifier),
    ])


def _target(values, count):
    target = np.asarray(values)
    if target.ndim != 1 or len(target) != count or not count:
        raise ValueError("Alvo deve ser unidimensional, alinhado e não vazio.")
    series = pd.Series(target)
    if series.isna().any() or not series.isin([0, 1]).all():
        raise ValueError("Alvo deve conter somente 0 e 1, sem ausências.")
    target = series.to_numpy(dtype=int)
    if set(target) != {0, 1}:
        raise ValueError("Ambas as classes são obrigatórias em treino e validação.")
    return target


def default_probability(pipeline, frame):
    """Retorna a probabilidade da classe positiva, verificando seu domínio."""
    classes = list(pipeline.named_steps["classifier"].classes_)
    probability = pipeline.predict_proba(frame)[:, classes.index(1)]
    if probability.shape != (len(frame),) or not np.isfinite(probability).all():
        raise ValueError("Previsões não finitas ou com dimensão inválida.")
    if ((probability < 0) | (probability > 1)).any():
        raise ValueError("Probabilidades devem estar entre 0 e 1.")
    return probability


@dataclass(frozen=True)
class ReferenceResult:
    """Modelos em memória e comparação agregada, sem registros individuais."""

    logistic: Pipeline
    dummy: Pipeline
    report: dict

    def report_json(self):
        return json.dumps(self.report, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def train_reference(split, *, seed=42):
    """Consome treino e validação de split_data; não acessa o conjunto de teste.

    As posições devem pertencer à mesma entrada rastreável. Não há busca de
    hiperparâmetros, seleção de limiar, persistência ou avaliação final.
    """
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("Semente deve ser um inteiro entre 0 e 2**32 - 1.")
    train, validation = split.train, split.validation
    train_positions = tuple(train.positions)
    validation_positions = tuple(validation.positions)
    if (
        len(train_positions) != len(train.X)
        or len(validation_positions) != len(validation.X)
        or len(set(train_positions)) != len(train_positions)
        or len(set(validation_positions)) != len(validation_positions)
        or set(train_positions) & set(validation_positions)
    ):
        raise ValueError("Posições de treino e validação devem ser únicas e disjuntas.")
    for part in (train, validation):
        if not part.X.index.equals(part.y.index):
            raise ValueError("Índices dos atributos e do alvo devem estar alinhados.")
        normalize_features(part.X)
    y_train = _target(train.y, len(train.X))
    y_validation = _target(validation.y, len(validation.X))
    logistic = build_pipeline(LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=2000, tol=1e-4, random_state=seed,
    ))
    dummy = build_pipeline(DummyClassifier(strategy="prior", random_state=seed))
    scores = {}
    for name, model in (("logistic", logistic), ("dummy", dummy)):
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            model.fit(train.X, y_train)
        probabilities = default_probability(model, validation.X)
        scores[name] = {
            "average_precision": float(average_precision_score(y_validation, probabilities)),
            "roc_auc": float(roc_auc_score(y_validation, probabilities)),
            "brier_score": float(brier_score_loss(y_validation, probabilities)),
        }
    difference = scores["logistic"]["average_precision"] - scores["dummy"]["average_precision"]
    report = {
        "model_version": VERSION,
        "split_metadata": split.metadata,
        "seed": seed,
        "features": list(FEATURES),
        "versions": {
            "python": platform.python_version(), "pandas": pd.__version__,
            "numpy": np.__version__, "scikit_learn": sklearn.__version__,
        },
        "configuration": {
            "numeric": "median; keep_empty_features=True; StandardScaler",
            "categorical": "most_frequent; keep_empty_features=True; one-hot; unknown=ignore",
            "logistic": {
                "C": 1.0, "solver": "lbfgs", "max_iter": 2000, "tol": 1e-4,
                "penalty": "l2", "class_weight": None, "fit_intercept": True,
            },
            "dummy": {"strategy": "prior"},
        },
        "train": {"observations": len(y_train), "prevalence": float(y_train.mean())},
        "validation": {
            "observations": len(y_validation),
            "prevalence": float(y_validation.mean()),
            "scores": scores,
            "average_precision_difference": difference,
            "logistic_above_dummy": difference > 0,
        },
        "limitations": [
            "Comparação restrita à validação; nenhuma conclusão de superioridade no teste.",
            "O teste permanece reservado à avaliação final.",
            "As garantias de isolamento de clientes e tempo dependem de split_data.",
            "Amostra histórica não comprova generalização temporal ou uso operacional.",
            "Excluir demografia não garante ausência de vieses.",
        ],
    }
    result = ReferenceResult(logistic, dummy, report)
    result.report_json()
    return result
