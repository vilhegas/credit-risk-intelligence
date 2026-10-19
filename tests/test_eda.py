"""Exploração reproduzível com dados exclusivamente sintéticos."""

import json

import numpy as np
import pandas as pd
import pytest

from credit_risk.analysis.eda import analyze, main, render_html
from credit_risk.ingestion.uci import COLUMNS, FEATURES, TARGET
from credit_risk.preprocessing.quality import treat_frame


def sample():
    rows = [{name: 1 for name in COLUMNS} for _ in range(4)]
    for i, row in enumerate(rows):
        row.update(ID=i + 1, LIMIT_BAL=i * 100000, BILL_AMT1=i * 10 - 10)
        row[TARGET] = i % 2
    rows[0]["PAY_0"] = -2
    rows[1]["PAY_0"] = 0
    return pd.DataFrame(rows, columns=COLUMNS)


def test_statistics_missing_groups_and_correlations():
    frame = treat_frame(sample()).accepted
    frame.loc[0, "LIMIT_BAL"] = pd.NA
    frame["PAY_AMT1"] = pd.NA
    original = frame.copy(deep=True)
    result = analyze(frame, "synthetic-v1")
    pd.testing.assert_frame_equal(frame, original)
    assert result["target"]["default_rate"] == 0.5
    assert result["target"]["minority_majority_ratio"] == 1
    assert result["missing"]["LIMIT_BAL"] == {"count": 1, "rate": 0.25}
    distribution = result["distributions"]["LIMIT_BAL"]
    assert distribution["median"] == 200000
    assert sum(b["count"] for b in distribution["histogram"]) == 3
    assert result["distributions"]["BILL_AMT1"]["minimum"] == -10
    assert result["distributions"]["PAY_AMT1"]["histogram"] == []
    groups = {r["group"]: r for r in result["patterns"]["LIMIT_BAL"]}
    assert groups["100000_a_299999"]["observations"] == 2
    assert groups["100000_a_299999"]["default_rate"] == 0.5
    assert groups["300000_ou_mais"]["defaults"] == 1
    assert groups["ausente"]["observations"] == 1
    assert "nao_documentado:-2" in {r["group"] for r in result["patterns"]["PAY_0"]}
    pair = next(r for r in result["correlations"]
                if r["left"] == "LIMIT_BAL" and r["right"] == "BILL_AMT1")
    assert pair["observations"] == 3
    assert pair["pearson"] == pytest.approx(1)
    assert pair["spearman"] == pytest.approx(1)
    assert all(r["pearson"] is None for r in result["correlations"]
               if "PAY_AMT1" in (r["left"], r["right"]))
    json.dumps(result, allow_nan=False)
    assert not set(result["distributions"]) & {"ID", "AGE", TARGET}
    assert len(result["missing"]) == len(FEATURES)


def test_empty_single_class_and_invalid_input():
    frame = treat_frame(sample()).accepted
    empty = analyze(frame.iloc[:0], "empty")
    assert empty["target"]["default_rate"] is None
    assert empty["patterns"]["LIMIT_BAL"] == []
    assert all(row["pearson"] is None for row in empty["correlations"])
    frame[TARGET] = 0
    assert analyze(frame, "single")["target"]["minority_majority_ratio"] == 0
    frame.loc[0, TARGET] = 2
    with pytest.raises(ValueError, match="Alvo"):
        analyze(frame, "invalid")
    frame.loc[0, TARGET] = 0
    frame["LIMIT_BAL"] = np.inf
    with pytest.raises(ValueError, match="inválidos"):
        analyze(frame, "invalid")


def test_report_escapes_text():
    result = analyze(treat_frame(sample()).accepted, "<script>exemplo</script>")
    report = render_html(result)
    assert "<svg" in report
    assert "<script>" not in report
    assert "&lt;script&gt;" in report
    assert "causalidade" in report


def test_full_local_execution_is_reproducible(tmp_path):
    source = tmp_path / "synthetic.csv"
    frame = sample()
    frame.loc[0, TARGET] = 3
    frame.to_csv(source, index=False)
    first, second = tmp_path / "first", tmp_path / "second"
    for output in (first, second):
        main([str(source), "--dataset-version", "synthetic-v1", "--output", str(output)])
    for name in ("summary.json", "report.html"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    result = json.loads((first / "summary.json").read_text(encoding="utf-8"))
    assert result["observations"] == 3
    assert result["quality"]["rejected_rows"] == 1
    with pytest.raises(FileExistsError):
        main([str(source), "--dataset-version", "synthetic-v1", "--output", str(first)])
