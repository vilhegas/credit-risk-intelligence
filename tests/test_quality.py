"""Verificações de qualidade com entradas exclusivamente sintéticas."""

import json

import numpy as np
import pandas as pd
import pytest

from credit_risk.ingestion.uci import COLUMNS, FEATURES, TARGET
from credit_risk.preprocessing.quality import treat_frame


def make_frame(count=2):
    rows = [{name: 1 for name in COLUMNS} for _ in range(count)]
    for position, row in enumerate(rows):
        row["ID"] = position + 1
        row[TARGET] = position % 2
    return pd.DataFrame(rows, columns=COLUMNS)


def test_normalization_preserves_raw_and_missing_values():
    frame = make_frame().astype(object)
    frame.index = [9, 9]
    frame.loc[:, "LIMIT_BAL"] = [" 100 ", " N/A "]
    frame.loc[:, "PAY_0"] = ["-2", "0"]
    frame.loc[:, "BILL_AMT1"] = [-100, 0]
    original = frame.copy(deep=True)
    result = treat_frame(frame)
    pd.testing.assert_frame_equal(frame, original)
    assert result.accepted.index.tolist() == [0, 1]
    assert str(result.accepted["LIMIT_BAL"].dtype) == "Int64"
    assert result.accepted.loc[0, "LIMIT_BAL"] == 100
    assert pd.isna(result.accepted.loc[1, "LIMIT_BAL"])
    assert result.accepted["PAY_0"].tolist() == ["nao_documentado:-2", "nao_documentado:0"]
    assert result.accepted["BILL_AMT1"].tolist() == [-100, 0]
    report = json.loads(result.report_json())
    assert report["missing_input_by_column"]["LIMIT_BAL"] == 1
    assert report["undocumented_codes_by_column"]["PAY_0"] == 2
    assert not set(FEATURES) & {"ID", TARGET, "SEX", "EDUCATION", "MARRIAGE", "AGE"}


@pytest.mark.parametrize(
    ("column", "value", "reason"),
    [
        ("ID", None, "ID:ausente"),
        ("ID", 0, "ID:invalido"),
        (TARGET, "", f"{TARGET}:ausente"),
        (TARGET, 2, f"{TARGET}:invalido"),
        ("AGE", "inválido", "AGE:invalido"),
        ("LIMIT_BAL", np.inf, "LIMIT_BAL:invalido"),
        ("LIMIT_BAL", 1.5, "LIMIT_BAL:invalido"),
        ("LIMIT_BAL", 2**53, "LIMIT_BAL:invalido"),
        ("LIMIT_BAL", True, "LIMIT_BAL:invalido"),
        ("LIMIT_BAL", 1 + 2j, "LIMIT_BAL:invalido"),
    ],
)
def test_invalid_rows_are_auditable(column, value, reason):
    frame = make_frame().astype(object)
    frame.loc[0, column] = value
    result = treat_frame(frame)
    assert result.accepted.index.tolist() == [1]
    assert result.rejected.index.tolist() == [0]
    assert reason in result.rejected.loc[0, "rejection_reasons"]
    pd.testing.assert_frame_equal(
        result.rejected.loc[:, list(COLUMNS)],
        frame.iloc[[0]].rename_axis("source_position"),
    )
    assert result.report["rejected_rows"] == 1


def test_duplicates_and_conflicts():
    frame = make_frame(3)
    frame.loc[1] = frame.loc[0]
    frame = pd.concat([frame, frame.iloc[[2]]], ignore_index=True)
    frame.loc[3, TARGET] = 1 - frame.loc[2, TARGET]
    result = treat_frame(frame)
    assert result.accepted.index.tolist() == [0]
    assert result.report["duplicate_rows_removed"] == 1
    assert result.report["conflicting_id_rows"] == 2
    assert result.report["input_rows"] == (
        result.report["accepted_rows"] + result.report["rejected_rows"]
    )


def test_missing_features_do_not_prevent_duplicate_detection():
    frame = make_frame().astype(object)
    frame.loc[0, "PAY_AMT1"] = None
    frame.loc[1] = frame.loc[0]
    result = treat_frame(frame)
    assert len(result.accepted) == 1
    assert pd.isna(result.accepted.loc[0, "PAY_AMT1"])
    assert result.report["duplicate_rows_removed"] == 1


def test_empty_and_all_rejected_frames():
    empty = treat_frame(make_frame(0))
    assert empty.report["input_rows"] == 0
    assert json.loads(empty.report_json())["accepted_rows"] == 0
    frame = make_frame()
    frame[TARGET] = 7
    assert treat_frame(frame).accepted.empty


def test_structural_errors():
    with pytest.raises(ValueError, match="Cabeçalho"):
        treat_frame(make_frame().drop(columns="AGE"))
    frame = make_frame().astype(object)
    frame.at[0, "AGE"] = [1, 2]
    with pytest.raises(ValueError, match="escalares"):
        treat_frame(frame)


def test_deterministic_result():
    frame = make_frame()
    first = treat_frame(frame)
    second = treat_frame(frame)
    pd.testing.assert_frame_equal(first.accepted, second.accepted)
    assert first.report_json() == second.report_json()
