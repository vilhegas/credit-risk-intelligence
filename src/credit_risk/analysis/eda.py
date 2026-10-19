"""Exploração determinística e relatório HTML sem serviços externos."""

import argparse
import hashlib
import html
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from credit_risk.ingestion.uci import FEATURES, PAY, TARGET
from credit_risk.preprocessing.quality import treat_frame

VERSION = "uci-350-eda-v1"
AMOUNTS = tuple(name for name in FEATURES if name not in PAY)
LIMITATIONS = (
    "Associações descritivas não demonstram causalidade nem efeito de políticas de crédito.",
    "Amostra histórica de clientes existentes em Taiwan; "
    "não representa clientes atuais brasileiros.",
    "Uma referência comum em setembro de 2005 não permite avaliar generalização temporal.",
    "A disponibilidade dos atributos no fechamento do mês é uma hipótese documental.",
    "Inadimplência segue o alvo da fonte; "
    "não equivale automaticamente a atraso superior a 90 dias.",
    "Limite concedido não representa necessariamente exposição no momento da inadimplência.",
    "Demografia e identificadores são excluídos desta análise; "
    "isso não garante ausência de vieses.",
    "Grupos pequenos têm taxas instáveis. Não são calculados intervalos ou testes inferenciais.",
    "Correlações usam pares completos, ignoram ausências e podem refletir seleção da amostra.",
    "PAY é categórico: códigos não documentados são preservados sem interpretação ordinal.",
    "Usar somente treino após definir partições; "
    "explorar teste pode contaminar decisões de modelagem.",
)


def _number(value):
    return None if pd.isna(value) else float(value)


def _groups(labels, target):
    table = pd.DataFrame({"group": labels, "target": target})
    rows = []
    for label, group in table.groupby("group", sort=True, observed=True):
        rows.append({
            "group": str(label),
            "observations": len(group),
            "defaults": int(group["target"].sum()),
            "default_rate": float(group["target"].mean()),
        })
    return rows


def analyze(frame: pd.DataFrame, dataset_version: str) -> dict:
    """Analisa registros aceitos pelo tratamento, sem alterar a entrada.

    Exige os 19 atributos financeiros e o alvo original. Colunas adicionais
    não participam de nenhum agregado. Não ajusta transformações preditivas.
    """
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        raise ValueError("Informe uma versão rastreável dos dados.")
    required = [*FEATURES, TARGET]
    if not frame.columns.is_unique or not set(required).issubset(frame.columns):
        raise ValueError("Colunas financeiras e alvo são obrigatórios e únicos.")
    target = frame[TARGET]
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError("Alvo deve conter apenas 0 e 1, sem ausências.")
    target = target.astype(int).reset_index(drop=True)
    numeric = pd.DataFrame(index=range(len(frame)))
    for name in AMOUNTS:
        values = frame[name].reset_index(drop=True)
        if any(isinstance(v, bool | np.bool_) for v in values.dropna()):
            raise ValueError(f"Booleano inválido em {name}.")
        try:
            converted = pd.to_numeric(values, errors="raise")
            if np.iscomplexobj(converted.to_numpy()):
                raise ValueError("Valores complexos.")
            array = converted.to_numpy(dtype=float, na_value=np.nan)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Variável monetária inválida: {name}.") from exc
        if np.isinf(array).any() or not np.array_equal(np.isnan(array), values.isna()):
            raise ValueError(f"Valores inválidos em {name}.")
        numeric[name] = array

    distributions = {}
    for name in AMOUNTS:
        values = numeric[name].dropna()
        if values.empty:
            bins = []
        else:
            counts, edges = np.histogram(values, bins=10)
            bins = [
                {"lower": float(edges[i]), "upper": float(edges[i + 1]), "count": int(n)}
                for i, n in enumerate(counts)
            ]
        distributions[name] = {
            "observed": len(values),
            "minimum": _number(values.min()),
            "q25": _number(values.quantile(0.25)),
            "median": _number(values.median()),
            "q75": _number(values.quantile(0.75)),
            "maximum": _number(values.max()),
            "mean": _number(values.mean()),
            "std_sample": _number(values.std(ddof=1)),
            "histogram": bins,
        }

    patterns = {}
    for name in PAY:
        labels = frame[name].reset_index(drop=True).astype("string").fillna("ausente")
        patterns[name] = _groups(labels, target)
    limits = numeric["LIMIT_BAL"]
    labels = pd.Series("ausente", index=limits.index, dtype="string")
    labels.loc[limits.notna() & (limits < 100000)] = "abaixo_100000"
    labels.loc[(limits >= 100000) & (limits < 300000)] = "100000_a_299999"
    labels.loc[limits >= 300000] = "300000_ou_mais"
    patterns["LIMIT_BAL"] = _groups(labels, target)

    correlations = []
    correlation_data = numeric.assign(defaulted=target)
    names = list(correlation_data.columns)
    for position, left in enumerate(names):
        for right in names[position + 1:]:
            pairs = correlation_data[[left, right]].dropna()
            valid = len(pairs) >= 3 and all(pairs[name].nunique() > 1 for name in pairs)
            correlations.append({
                "left": left,
                "right": right,
                "observations": len(pairs),
                "pearson": _number(pairs[left].corr(pairs[right])) if valid else None,
                "spearman": (
                    _number(pairs[left].corr(pairs[right], method="spearman"))
                    if valid else None
                ),
            })
    counts = [int((target == label).sum()) for label in (0, 1)]
    return {
        "analysis_version": VERSION,
        "dataset_version": dataset_version.strip(),
        "versions": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "observations": len(frame),
        "target": {
            "class_counts": {"0": counts[0], "1": counts[1]},
            "default_rate": float(target.mean()) if len(target) else None,
            "minority_majority_ratio": min(counts) / max(counts) if max(counts) else None,
            "both_classes_present": all(counts),
        },
        "missing": {
            name: {
                "count": int(frame[name].isna().sum()),
                "rate": float(frame[name].isna().mean()) if len(frame) else None,
            }
            for name in FEATURES
        },
        "distributions": distributions,
        "patterns": patterns,
        "correlations": correlations,
        "limitations": list(LIMITATIONS),
    }


def _bars(labels, values):
    """SVG agregado com rótulos escapados e escala explícita pelo valor."""
    height = max(45, len(labels) * 28 + 10)
    maximum = max(values, default=0) or 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {height}" '
        'role="img" aria-label="Gráfico de barras com valores">'
    ]
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        y = index * 28 + 5
        parts.append(
            f'<text x="0" y="{y + 16}" font-size="12">{html.escape(str(label))}</text>'
            f'<rect x="350" y="{y}" width="{value / maximum * 420:.3f}" '
            'height="20" fill="#276599"/>'
            f'<text x="780" y="{y + 16}" font-size="12">{value:.6g}</text>'
        )
    return "".join([*parts, "</svg>"])


def render_html(result: dict) -> str:
    """Produz relatório autossuficiente, sem JavaScript ou recursos remotos."""
    sections = [
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Análise exploratória de crédito</title><body>',
        '<h1>Análise exploratória de crédito</h1>',
        f'<p>Versão: {html.escape(result["dataset_version"])}. '
        f'Observações aceitas: {result["observations"]}.</p>',
        '<p>Fonte prevista: UCI 350, clientes existentes em Taiwan, referência '
        'convencional em setembro de 2005. Valores monetários em NT$.</p>',
        '<h2>Limitações e interpretação</h2><ul>',
        *(f'<li>{html.escape(item)}</li>' for item in result["limitations"]),
        '</ul><h2>Alvo e desequilíbrio</h2>',
        _bars(list(result["target"]["class_counts"]),
              list(result["target"]["class_counts"].values())),
        '<p>0: sem inadimplência; 1: inadimplência no mês seguinte.</p>',
        '<h2>Ausências por atributo</h2>',
        _bars(list(result["missing"]), [v["count"] for v in result["missing"].values()]),
        '<h2>Distribuições monetárias</h2>',
        '<p>Dez intervalos de mesma largura por variável, ignorando ausências. '
        'Intervalos fechados à esquerda, exceto o último, fechado também à direita. '
        'Extremos, zeros e negativos são preservados.</p>',
    ]
    for name, distribution in result["distributions"].items():
        bins = distribution["histogram"]
        sections.extend([
            f'<h3>{html.escape(name)}</h3>',
            _bars([f'{b["lower"]:.6g} a {b["upper"]:.6g}' for b in bins],
                  [b["count"] for b in bins]),
        ])
    sections.append('<h2>Taxas de inadimplência por grupo</h2>')
    for name, rows in result["patterns"].items():
        sections.extend([
            f'<h3>{html.escape(name)}</h3>',
            _bars([f'{r["group"]} (n={r["observations"]}, '
                   f'inadimplentes={r["defaults"]})' for r in rows],
                  [r["default_rate"] for r in rows]),
        ])
    sections.extend([
        '<h2>Resultados completos e correlações</h2>',
        '<p>Taxas entre 0 e 1. Pearson e Spearman apenas para valores monetários '
        'e alvo. Correlações indisponíveis com menos de três pares ou variável '
        'constante. Nenhuma correlação implica causalidade. Detalhes incluem '
        'denominadores por par e por grupo.</p>',
        '<details><summary>Consultar estatísticas e metadados</summary><pre>',
        html.escape(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)),
        '</pre></details></body></html>',
    ])
    return "\n".join(sections)


def main(argv=None):
    """Lê CSV local com contrato bruto, trata e exporta apenas agregados."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="CSV local com as 25 colunas originais.")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="Diretório novo para artefatos; nunca sobrescreve uma execução.")
    args = parser.parse_args(argv)
    source_bytes = args.input.read_bytes()
    from io import BytesIO

    raw = pd.read_csv(BytesIO(source_bytes), dtype=object, keep_default_na=False)
    quality = treat_frame(raw)
    result = analyze(quality.accepted, args.dataset_version)
    result["input_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    result["quality"] = quality.report
    serialized = json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    report = render_html(result)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "summary.json").write_text(serialized, encoding="utf-8")
    (args.output / "report.html").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
