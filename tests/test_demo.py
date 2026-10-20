"""Contratos e fluxo interativo usando exclusivamente dados artificiais."""

import json
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from credit_risk.presentation.demo import (
    example_record,
    explore_policies,
    indicators,
    parse_record,
    predict_record,
)


def test_complete_service_flow():
    text = json.dumps(example_record())
    probability = predict_record(text)
    assert 0 <= probability <= 1
    assert predict_record(text) == probability
    summary = indicators()
    assert 0 < summary["defaults"] < summary["observations"]
    report = explore_policies([0, 0.5, 1], 100, 0.5, 0.1)
    assert len(report["rows"]) == 3
    assert report["rows"][0]["approved"] == 0
    assert report["rows"][0]["approved_default_rate"] is None
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("text", [
    "{", "[]", "null", "{}", '{"ID": 1}',
    '{"LIMIT_BAL": 1, "LIMIT_BAL": 2}', "[" * 2000,
])
def test_invalid_json_contract(text):
    with pytest.raises(ValueError):
        parse_record(text)


@pytest.mark.parametrize("field,value", [
    ("LIMIT_BAL", True), ("LIMIT_BAL", np.nan), ("LIMIT_BAL", np.inf),
    ("LIMIT_BAL", 1.5), ("LIMIT_BAL", 10**50), ("LIMIT_BAL", None),
    ("PAY_0", 1), ("PAY_0", "texto privado"), ("PAY_0", [1]),
])
def test_invalid_fields_have_safe_messages(field, value):
    record = example_record()
    record[field] = value
    with pytest.raises(ValueError) as error:
        parse_record(json.dumps(record))
    assert field in str(error.value)
    assert "texto privado" not in str(error.value)


def test_extra_fields_and_duplicate_thresholds_rejected():
    record = example_record()
    record["nome"] = "valor privado"
    with pytest.raises(ValueError):
        parse_record(json.dumps(record))
    with pytest.raises(ValueError):
        explore_policies([0.5, 0.5, 0.8], 100, 0.5, 0.1)


def test_streamlit_flow_and_clear_errors():
    path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(path)).run(timeout=60)
    assert not app.exception
    app.button[0].click().run(timeout=60)
    assert any("Probabilidade estimada" in metric.label for metric in app.metric)
    app.text_area[0].set_value("{").run()
    app.button[0].click().run()
    assert any("JSON inválido" in error.value for error in app.error)
    app.button[1].click().run(timeout=60)
    assert not app.exception
    assert len(app.dataframe) == 1
    app.number_input[1].set_value(0.2).run()
    app.button[1].click().run()
    assert any("três limiares distintos" in error.value for error in app.error)
