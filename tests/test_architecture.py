"""Verifica a disponibilidade dos módulos no pacote instalado."""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "credit_risk",
        "credit_risk.ingestion",
        "credit_risk.preprocessing",
        "credit_risk.analysis",
        "credit_risk.modeling",
        "credit_risk.simulation",
        "credit_risk.presentation",
    ],
)
def test_architecture_modules_are_importable(module_name: str) -> None:
    module = import_module(module_name)

    assert module.__name__ == module_name
    assert module.__doc__
    assert module.__file__ is not None
