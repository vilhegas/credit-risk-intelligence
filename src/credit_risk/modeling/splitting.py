"""Partições isoladas por cliente e seleção explícita de preditores."""

from dataclasses import dataclass
from math import floor

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from credit_risk.ingestion.uci import FEATURES, TARGET

VERSION = "credit-split-v1"


@dataclass(frozen=True)
class Partition:
    """Dados independentes; posições referem-se à entrada, não ao índice."""

    X: pd.DataFrame
    y: pd.Series
    positions: tuple[int, ...]


@dataclass(frozen=True)
class SplitResult:
    train: Partition
    validation: Partition
    test: Partition
    metadata: dict


def _dates(values, name):
    try:
        result = pd.to_datetime(values, errors="raise", utc=True)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"Datas inválidas: {name}.") from exc
    if result.isna().any():
        raise ValueError(f"Datas ausentes: {name}.")
    return result


def split_data(
    frame: pd.DataFrame,
    dataset_version: str,
    *,
    client_column: str = "ID",
    reference_column: str = "reference_date",
    label_end_column: str = "label_end_date",
    availability_columns: dict[str, str] | None = None,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    seed: int = 42,
) -> SplitResult:
    """Separa registros tratados, sem ajustar transformações ou escrever dados.

    Sem datas, ou com referência única, aplica estratificação por cliente.
    Múltiplas referências exigem datas de disponibilidade de cada atributo
    e término do horizonte do alvo. Nenhum erro temporal provoca fallback.
    """
    fractions = (train_fraction, validation_fraction)
    if any(isinstance(v, bool) or not isinstance(v, int | float) for v in fractions):
        raise ValueError("Frações devem ser números reais.")
    if not all(np.isfinite(v) and 0 < v < 1 for v in fractions):
        raise ValueError("Frações devem estar entre zero e um.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Reserve uma fração positiva para teste.")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("Semente inteira inválida.")
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("Informe a versão rastreável dos dados.")
    required = {*FEATURES, TARGET, client_column}
    if not frame.columns.is_unique or not required.issubset(frame.columns):
        raise ValueError("Colunas obrigatórias ausentes ou duplicadas.")
    if client_column in {*FEATURES, TARGET}:
        raise ValueError("Cliente não pode ser preditor nem alvo.")
    data = frame.reset_index(drop=True).copy(deep=True)
    clients = data[client_column]
    if clients.isna().any() or clients.empty:
        raise ValueError("Clientes ausentes ou amostra vazia.")
    # Identificadores não são normalizados silenciosamente entre tipos.
    valid_ids = clients.map(
        lambda value: (
            isinstance(value, str) and bool(value.strip())
        ) or (
            isinstance(value, int | np.integer) and not isinstance(value, bool | np.bool_)
        )
    )
    if not valid_ids.all() or clients.map(type).nunique() != 1:
        raise ValueError("Use identificadores escalares, consistentes e não vazios.")
    target = data[TARGET]
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError("Alvo deve ser binário e completo.")
    if target.map(lambda value: isinstance(value, bool | np.bool_)).any():
        raise ValueError("Alvo booleano não é aceito.")

    reference = None
    if reference_column in data:
        reference = _dates(data[reference_column], reference_column)
    availability = availability_columns or {}
    if availability and set(availability) != set(FEATURES):
        raise ValueError("Informe disponibilidade para todos os 19 preditores.")
    if availability:
        if reference is None:
            raise ValueError("Disponibilidade exige data de referência.")
        for feature, column in availability.items():
            if column not in data:
                raise ValueError(f"Coluna de disponibilidade ausente: {feature}.")
            if (_dates(data[column], column) > reference).any():
                raise ValueError(f"Atributo posterior à decisão: {feature}.")

    limitations = []
    excluded = set()
    boundaries = None
    if reference is not None and reference.nunique() > 1:
        if not availability or label_end_column not in data:
            raise ValueError("Divisão temporal exige disponibilidade e fim do horizonte.")
        label_end = _dates(data[label_end_column], label_end_column)
        if (label_end <= reference).any():
            raise ValueError("O horizonte deve terminar após a referência.")
        dates = reference.drop_duplicates().sort_values().tolist()
        if len(dates) < 3:
            raise ValueError("Referências insuficientes para três períodos isolados.")
        first = max(1, floor(len(dates) * train_fraction))
        second = max(first + 1, floor(len(dates) * (train_fraction + validation_fraction)))
        second = min(second, len(dates) - 1)
        cut_validation, cut_test = dates[first], dates[second]
        labels = pd.Series(2, index=data.index)
        labels.loc[reference < cut_test] = 1
        labels.loc[reference < cut_validation] = 0
        # Exclui todos os registros de clientes que atravessam fronteiras.
        crossing = labels.groupby(clients).nunique()
        excluded.update(data.index[clients.isin(crossing[crossing > 1].index)].tolist())
        # Rótulos do passado devem estar disponíveis antes do período seguinte.
        overlap = ((labels == 0) & (label_end >= cut_validation)) | (
            (labels == 1) & (label_end >= cut_test)
        )
        excluded.update(data.index[overlap].tolist())
        positions = [
            tuple(int(i) for i in data.index[(labels == label) & ~data.index.isin(excluded)])
            for label in range(3)
        ]
        method = "temporal"
        boundaries = [cut_validation.isoformat(), cut_test.isoformat()]
        limitations.append("Frações temporais aproximam quantidades de datas, não de linhas.")
        limitations.append("Expurgo pode alterar população, volume e prevalência das partições.")
    else:
        grouped = target.groupby(clients, sort=True)
        if (grouped.nunique() > 1).any():
            raise ValueError("Estratificação exige alvo consistente por cliente.")
        labels = grouped.first()
        try:
            train_ids, remaining_ids = train_test_split(
                labels.index.to_numpy(),
                train_size=train_fraction,
                random_state=seed,
                stratify=labels.to_numpy(),
            )
            validation_ids, test_ids = train_test_split(
                remaining_ids,
                train_size=validation_fraction / (1 - train_fraction),
                random_state=seed,
                stratify=labels.loc[remaining_ids].to_numpy(),
            )
        except ValueError as exc:
            raise ValueError("Clientes insuficientes para estratificar três conjuntos.") from exc
        positions = [
            tuple(int(i) for i in data.index[clients.isin(ids)])
            for ids in (train_ids, validation_ids, test_ids)
        ]
        method = "stratified_client"
        limitations.append("Referências insuficientes: divisão não mede generalização temporal.")
        limitations.append("Frações e estratificação referem-se a clientes, não a linhas.")
        if not availability:
            limitations.append(
                "Disponibilidade dos 19 campos pressupõe o contrato UCI: histórico até "
                "setembro de 2005 disponível no fechamento; não verificada por registro."
            )

    partitions = []
    summaries = {}
    client_sets = []
    for name, selected in zip(("train", "validation", "test"), positions, strict=True):
        subset = data.iloc[list(selected)]
        if set(subset[TARGET].unique()) != {0, 1}:
            raise ValueError(f"Ambas as classes são obrigatórias em {name} após separação.")
        partitions.append(Partition(
            X=subset.loc[:, list(FEATURES)].copy(deep=True),
            y=subset[TARGET].astype(int).copy(deep=True),
            positions=selected,
        ))
        client_sets.append(set(subset[client_column]))
        summaries[name] = {
            "rows": len(subset),
            "clients": int(subset[client_column].nunique()),
            "class_counts": {
                str(label): int((subset[TARGET] == label).sum()) for label in (0, 1)
            },
        }
    if any(client_sets[i] & client_sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("Sobreposição de clientes entre conjuntos.")
    metadata = {
        "split_version": VERSION,
        "dataset_version": dataset_version.strip(),
        "method": method,
        "seed": seed,
        "requested_fractions": {
            "train": train_fraction,
            "validation": validation_fraction,
            "test": 1 - train_fraction - validation_fraction,
        },
        "features": list(FEATURES),
        "boundaries_utc": boundaries,
        "excluded_rows": len(excluded),
        "partitions": summaries,
        "limitations": limitations,
    }
    return SplitResult(*partitions, metadata=metadata)
