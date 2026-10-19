"""Tratamento determinístico da UCI 350, sem ajuste estatístico."""

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from credit_risk.ingestion.uci import COLUMNS, MAX_ROWS, PAY, TARGET

CONTRACT = "uci-350-quality-v1"
CATEGORIES = {
    **{name: {-1, *range(1, 10)} for name in PAY},
    "SEX": {1, 2},
    "EDUCATION": {1, 2, 3, 4},
    "MARRIAGE": {1, 2, 3},
}
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}


@dataclass(frozen=True)
class QualityResult:
    """Resultados independentes da entrada; posições são baseadas em zero."""

    accepted: pd.DataFrame
    rejected: pd.DataFrame
    report: dict

    def report_json(self) -> str:
        """Serializa o relatório agregado sem gravar arquivos."""
        return json.dumps(self.report, ensure_ascii=False, allow_nan=False, indent=2)


def _missing(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in MISSING_TOKENS
    return bool(pd.isna(value))


def treat_frame(frame: pd.DataFrame) -> QualityResult:
    """Normaliza uma cópia e registra rejeições sem modificar a camada original.

    Aceita somente células escalares, cabeçalho exato e até MAX_ROWS linhas.
    Ausências em atributos permanecem ausentes. ID e alvo são obrigatórios.
    """
    if tuple(frame.columns) != COLUMNS:
        raise ValueError("Cabeçalho ou ordem das 25 colunas incompatível.")
    if len(frame) > MAX_ROWS:
        raise ValueError("Quantidade de registros acima do limite.")
    if any(not pd.api.types.is_scalar(value) for value in frame.to_numpy().flat):
        raise ValueError("As células devem conter valores escalares.")

    raw = frame.copy(deep=True).reset_index(drop=True)
    normalized = pd.DataFrame(index=raw.index)
    reasons = [[] for _ in range(len(raw))]
    missing_input = {}
    invalid_cells = {}
    undocumented = {}

    for name in COLUMNS:
        values = []
        missing_count = 0
        invalid_count = 0
        unknown_count = 0
        for position, value in enumerate(raw[name]):
            if _missing(value):
                missing_count += 1
                values.append(pd.NA)
                if name in ("ID", TARGET):
                    reasons[position].append(f"{name}:ausente")
                continue
            try:
                if isinstance(value, (bool, np.bool_)):
                    raise ValueError("Booleano não aceito")
                candidate = value.strip() if isinstance(value, str) else value
                number = pd.to_numeric(candidate, errors="raise")
                if np.iscomplexobj(number) or not np.isfinite(number):
                    raise ValueError("Número não finito ou complexo")
                if abs(number) > 2**53 - 1 or number != np.trunc(number):
                    raise ValueError("Inteiro fora do contrato")
                integer = int(number)
                if name == "ID" and integer <= 0:
                    raise ValueError("Identificador não positivo")
                if name == TARGET and integer not in (0, 1):
                    raise ValueError("Alvo fora do domínio")
            except (TypeError, ValueError, OverflowError):
                invalid_count += 1
                reasons[position].append(f"{name}:invalido")
                values.append(pd.NA)
                continue
            if name in CATEGORIES:
                if integer in CATEGORIES[name]:
                    values.append(str(integer))
                else:
                    unknown_count += 1
                    values.append(f"nao_documentado:{integer}")
            else:
                values.append(integer)
        dtype = "string" if name in CATEGORIES else "Int64"
        normalized[name] = pd.Series(values, index=raw.index, dtype=dtype)
        missing_input[name] = missing_count
        invalid_cells[name] = invalid_count
        if name in CATEGORIES:
            undocumented[name] = unknown_count

    eligible = [position for position, row_reasons in enumerate(reasons) if not row_reasons]
    candidates = normalized.loc[eligible]
    duplicate_rows = 0
    conflicting_rows = 0
    for _, group in candidates.groupby("ID", sort=False):
        if len(group) <= 1:
            continue
        if len(group.drop_duplicates()) == 1:
            for position in group.index[1:]:
                reasons[position].append("duplicata_identica")
                duplicate_rows += 1
        else:
            for position in group.index:
                reasons[position].append("id_conflitante")
                conflicting_rows += 1

    accepted_positions = [position for position, row in enumerate(reasons) if not row]
    rejected_positions = [position for position, row in enumerate(reasons) if row]
    accepted = normalized.loc[accepted_positions].copy()
    accepted.index.name = "source_position"
    rejected = raw.loc[rejected_positions].copy()
    rejected.index.name = "source_position"
    rejected["rejection_reasons"] = [tuple(reasons[p]) for p in rejected_positions]
    report = {
        "contract_version": CONTRACT,
        "input_rows": len(raw),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "duplicate_rows_removed": duplicate_rows,
        "conflicting_id_rows": conflicting_rows,
        "missing_input_by_column": missing_input,
        "invalid_cells_by_column": invalid_cells,
        "undocumented_codes_by_column": undocumented,
        "missing_accepted_by_column": {
            name: int(accepted[name].isna().sum()) for name in COLUMNS
        },
        "rejections_by_reason": {
            reason: sum(reason in row for row in reasons)
            for reason in sorted({reason for row in reasons for reason in row})
        },
    }
    return QualityResult(accepted, rejected, report)
