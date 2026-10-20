"""Adaptador público sintético. Não lê bases externas nem avalia o teste reservado."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import platform
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from credit_risk.analysis.eda import analyze
from credit_risk.ingestion.uci import FEATURES, TARGET
from credit_risk.modeling.comparison import compare_models
from credit_risk.modeling.interpretation import permutation_report
from credit_risk.modeling.reference import default_probability
from credit_risk.modeling.splitting import split_data
from credit_risk.presentation import demo

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
RELEASES = WEB / "src/data/releases"
PRIVATE = WEB / "reports/export-evidence"
SCHEMA = "credit-risk-web-v1"
EXPORTER = "web-synthetic-export-v1"
KINDS = (
    "overview",
    "eda",
    "comparison",
    "calibration",
    "interpretation",
    "final_evaluation",
    "simulation",
)
THRESHOLDS = tuple(i / 10 for i in range(11))
EXPOSURE, LGD, REVENUE = 100.0, 0.5, 0.1
LIMITATIONS = [
    "Demonstração inteiramente sintética; não descreve clientes reais ou a base UCI.",
    "Gerador com semente 42: as seis colunas PAY compartilham o atraso artificial; "
    "associações refletem a construção do gerador, sem interpretação causal.",
    "Não há período observado ou moeda real; horizonte e unidade monetária são hipotéticos.",
    "O fluxo QualityResult não foi aplicado; quality é nulo e não significa ausência de erros.",
    "A validação participa da comparação; não representa desempenho final independente.",
    "Simulação e permutação usam a logística de referência, não o vencedor da comparação.",
    "Calibração não foi selecionada; identity preserva as probabilidades originais.",
    "Teste reservado não foi avaliado. Nenhuma superioridade final ou uso operacional é alegado.",
    "Revisão humana e procedência de árvore Git limpa pendentes; candidato não aprovado.",
]
SOURCE_FILES = (
    "src/credit_risk/presentation/demo.py",
    "src/credit_risk/ingestion/uci.py",
    "src/credit_risk/modeling/reference.py",
    "src/credit_risk/modeling/comparison.py",
    "src/credit_risk/modeling/splitting.py",
    "src/credit_risk/modeling/interpretation.py",
    "src/credit_risk/analysis/eda.py",
    "src/credit_risk/simulation/policies.py",
    "web/exporters/export_synthetic.py",
    "web/exporters/tests/test_export_synthetic.py",
    "web/scripts/validate-release.ts",
    "web/scripts/verify-export-parity.ts",
    "web/src/lib/schemas/results.ts",
    "web/src/lib/schemas/analysis.ts",
    "web/src/lib/schemas/strict-json.ts",
    "web/src/lib/data/releases.ts",
    "web/src/types/results.ts",
    "pyproject.toml",
    "web/package-lock.json",
)


def canonical_bytes(value) -> bytes:
    """Representação canônica v1: UTF-8, sort_keys, indent=2, sem NaN, LF final."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def select(value: dict, fields: str) -> dict:
    """Lista positiva; não propaga campos novos da API silenciosamente."""
    return {key: value[key] for key in fields.split()}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def git_provenance() -> dict:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    return {
        "code_revision": git("rev-parse", "HEAD"),
        "working_tree_clean": not bool(git("status", "--porcelain", "--untracked-files=all")),
    }


def environment() -> dict:
    result = {
        "python": platform.python_version(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "threadpool_limit": "1",
    }
    for library in ("numpy", "pandas", "scikit-learn", "scipy", "threadpoolctl"):
        result[library] = version(library)
    with threadpool_limits(limits=1):
        result["numeric_runtime"] = (
            canonical_bytes(
                [
                    select(item, "internal_api version architecture num_threads")
                    if "architecture" in item
                    else select(item, "internal_api version num_threads")
                    for item in threadpool_info()
                ]
            )
            .decode()
            .strip()
        )
    result["node"] = subprocess.check_output(["node", "--version"], text=True).strip()
    return result


def source_snapshots() -> dict[str, bytes]:
    return {name: (ROOT / name).read_bytes() for name in SOURCE_FILES}


@dataclass
class Evidence:
    """Objetos restritos em memória; nunca serializados no pacote público."""

    frame: object
    split: object
    comparison: object
    eda: dict
    permutation: dict
    summary: dict
    simulation: dict
    probability: np.ndarray


def compute_evidence() -> Evidence:
    # Reuses the exact generator, split defaults, pipelines and policy service.
    # No final_evaluation import or invocation is needed.
    with threadpool_limits(limits=1):
        frame = demo.demonstration_frame()
        split = split_data(frame, demo.DATASET_VERSION)
        compared = compare_models(split, seed=42)
        model = compared.models["logistic_c1"]
        probability = default_probability(model, split.validation.X)
        eda_input = split.train.X.copy()
        eda_input[TARGET] = split.train.y
        eda = analyze(eda_input, demo.DATASET_VERSION)
        permutation = permutation_report(
            model,
            split.validation.X,
            split.validation.y,
            dataset_version=demo.DATASET_VERSION,
            repeats=20,
            seed=42,
        )
        # The original demo independently reproduces its reference pipeline.
        demo._bundle.cache_clear()
        summary = demo.indicators()
        simulation = demo.explore_policies(THRESHOLDS, EXPOSURE, LGD, REVENUE)
        if not np.array_equal(probability, demo._bundle()[2]):
            raise ValueError("Probabilidades da referência divergem da demonstração original")
        return Evidence(frame, split, compared, eda, permutation, summary, simulation, probability)


def notes_for_nulls(value, path="payload") -> dict[str, str]:
    if value is None:
        return {
            path: "Não calculado ou matematicamente indefinido; "
            "nenhuma substituição por zero. Ver limitações e denominadores."
        }
    notes = {}
    items = (
        enumerate(value)
        if isinstance(value, list)
        else (value.items() if isinstance(value, dict) else [])
    )
    for key, child in items:
        notes.update(notes_for_nulls(child, f"{path}.{key}"))
    return notes


def policy_configuration() -> dict:
    return {
        "threshold": 0.5,
        "decision_rule": "approve if p < threshold",
        "calibration_method": "identity",
        "selection": "fixed demonstration; no tuning",
        "simulation": {
            "exposure": EXPOSURE,
            "lgd": LGD,
            "revenue_rate": REVENUE,
            "thresholds": list(THRESHOLDS),
        },
    }


def model_id(candidate: str) -> str:
    return f"synthetic-{candidate}"


def model_version(candidate: str) -> str:
    return demo.MODEL_VERSION if candidate == "logistic_c1" else f"credit-comparison-v1-{candidate}"


def public_privacy_check(documents: dict) -> None:
    """Complementa os schemas com a exclusão de campos individuais e demográficos."""
    forbidden = {
        "ID",
        "AGE",
        "SEX",
        "EDUCATION",
        "MARRIAGE",
        "positions",
        "clients",
        "records",
        "predictions",
        "probabilities",
        "coef_",
        "intercept_",
        "tree_",
    }

    def visit(value):
        if isinstance(value, dict):
            if forbidden.intersection(value):
                raise ValueError("Campo individual, demográfico ou estado de modelo no pacote")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and (str(ROOT) in value or re.search(r"[A-Za-z]:\\", value)):
            raise ValueError("Caminho local privado no pacote")

    visit(documents)
    canonical_bytes(documents)  # Also refuses every non-finite number.


def project_evidence(e: Evidence, release_id: str, frozen_at: str):
    """Retorna artefatos públicos e evidências locais separadas; não escreve arquivos."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", release_id):
        raise ValueError("Identificador de release inválido")
    input_bytes = canonical_bytes(
        {"columns": list(e.frame.columns), "rows": e.frame.astype(object).values.tolist()}
    )
    audit = {"input.json": input_bytes}
    dataset_hash = sha256(input_bytes)
    partitions = []
    for name in ("train", "validation"):
        part = getattr(e.split, name)
        raw = canonical_bytes(
            {
                "format": "ordered-input-positions-v1",
                "dataset_sha256": dataset_hash,
                "partition": name,
                "positions": list(part.positions),
            }
        )
        audit[f"partition-{name}.json"] = raw
        partitions.append(
            {
                "partition_id": name,
                "role": name,
                "observations": len(part.y),
                "class_counts": {str(c): int((part.y == c).sum()) for c in (0, 1)},
                "method": "credit-split-v1; stratified_client; seed=42; "
                "frações solicitadas treino=0.6, validação=0.2, reserva=0.2; "
                "sem datas observadas; composição/ordem restritas; clientes disjuntos",
                "partition_sha256": sha256(raw),
                "used_for": [
                    "eda e ajuste"
                    if name == "train"
                    else "comparação, permutação e simulação sintéticas"
                ],
            }
        )
    # Preserve complete fitted artifacts privately; the public output gets hashes only.
    models = []
    for row in e.comparison.report["table"]:
        candidate = row["candidate"]
        raw = pickle.dumps(e.comparison.models[candidate], protocol=5)
        audit[f"model-{candidate}.pkl"] = raw
        models.append(
            {
                "model_id": model_id(candidate),
                "dataset_id": demo.DATASET_VERSION,
                "model_version": model_version(candidate),
                "family": row["family"],
                "features": list(FEATURES),
                "configuration": canonical_bytes(
                    {
                        "candidate_parameters": row["parameters"],
                        "seed": 42,
                        "preprocessing": select(
                            e.comparison.report["reference_report"]["configuration"],
                            "numeric categorical",
                        ),
                        "estimator_parameters": e.comparison.models[candidate]
                        .named_steps["classifier"]
                        .get_params(deep=False),
                        "state_representation": "pickle protocol 5; restricted local artifact",
                    }
                )
                .decode()
                .strip(),
                "partition_sha256": partitions[0]["partition_sha256"],
                "model_sha256": sha256(raw),
                "calibration_method": "identity",
            }
        )
    configuration = policy_configuration()
    policy_raw = canonical_bytes(
        {
            "model_sha256": next(
                m["model_sha256"] for m in models if m["model_id"] == model_id("logistic_c1")
            ),
            "configuration": configuration,
            "frozen_at_utc": frozen_at,
        }
    )
    audit["policy.json"] = policy_raw
    policy = {
        "policy_id": "synthetic-reference-policy",
        "model_id": model_id("logistic_c1"),
        "policy_sha256": sha256(policy_raw),
        "threshold": 0.5,
        "configuration": canonical_bytes(configuration).decode().strip(),
        "frozen_at_utc": frozen_at,
    }

    documents = {}

    def envelope(kind, payload, source, partition="validation", has_model=True, has_policy=False):
        part = next(p for p in partitions if p["partition_id"] == partition)
        value = {
            "schema_version": SCHEMA,
            "release_id": release_id,
            "result_id": f"synthetic-{kind}",
            "kind": kind,
            "dataset_id": demo.DATASET_VERSION,
            "partition_id": partition,
            "model_id": model_id("logistic_c1") if has_model else None,
            "policy_id": policy["policy_id"] if has_policy else None,
            "origin": "synthetic",
            "source_contract": source,
            "observations": part["observations"],
            "payload": payload,
            "metric_notes": notes_for_nulls(payload),
            "limitations": list(LIMITATIONS),
        }
        documents[f"{kind.replace('_', '-')}.json"] = value
        return value

    summary = e.summary
    envelope(
        "overview",
        {
            "defaults": summary["defaults"],
            "non_defaults": summary["observations"] - summary["defaults"],
            "default_rate": summary["default_rate"],
        },
        "demo.indicators@demo-synthetic-v1",
        has_model=False,
    )
    envelope(
        "eda",
        select(e.eda, "target missing distributions patterns correlations"),
        "analysis.eda.analyze@uci-350-eda-v1",
        partition="train",
        has_model=False,
    )
    raw = e.comparison.report
    reference = select(raw["reference_report"], "model_version seed features train validation")
    reference.update(
        train_partition_id="train",
        configuration=canonical_bytes(raw["reference_report"]["configuration"]).decode().strip(),
    )
    comparison = select(
        raw,
        "comparison_version seed validation_method threshold positive_class "
        "zero_division train_observations validation_observations train_prevalence "
        "validation_prevalence selected_candidate selection_reason tie_preference "
        "selected_above_reference selected_above_dummy",
    )
    comparison["train_partition_id"] = "train"
    comparison["table"] = [
        {**row, "parameters": canonical_bytes(row["parameters"]).decode().strip()}
        for row in raw["table"]
    ]
    compared = envelope(
        "comparison",
        {"reference": reference, "comparison": comparison},
        "modeling.comparison.compare_models@credit-comparison-v1",
    )
    compared["limitations"].extend(raw["limitations"])
    for i, row in enumerate(comparison["table"]):
        if row["predicted_positives"] == 0:
            compared["metric_notes"][f"payload.comparison.table.{i}.precision"] = (
                "Precisão zero conforme zero_division=0 da API, sem positivos previstos."
            )
    permutation = select(
        e.permutation,
        "version dataset_version observations " "baseline_average_precision repeats seed factors",
    )
    interpreted = envelope(
        "interpretation",
        {"permutation": permutation, "segments": None},
        "modeling.interpretation.permutation_report@permutation-v1",
    )
    interpreted["metric_notes"]["payload.segments"] = (
        "Análise por segmentos não executada nesta release."
    )
    interpreted["limitations"].extend(e.permutation["limitations"])
    grid_rows = []
    y = e.split.validation.y.to_numpy()
    for threshold in THRESHOLDS:
        approved = e.probability < threshold
        grid_rows.append(
            {
                "threshold": threshold,
                "approved": int(approved.sum()),
                "approved_defaults": int(y[approved].sum()),
                "approved_probability_sum": float(e.probability[approved].sum()),
            }
        )
    grid = {
        "exposure_mode": "constant",
        "observations": len(y),
        "defaults": int(y.sum()),
        "probability_stage": "raw",
        "rows": grid_rows,
        "parity_verification": "web/scripts/validate-release.ts e "
        "web/exporters/tests/test_export_synthetic.py; tolerância relativa 1e-10, "
        "contagens exatas; somente exposição constante",
    }
    simulation = envelope(
        "simulation",
        {"report": e.simulation, "interactive_grid": grid},
        "simulation.policies.simulate_policies@credit-policy-v1",
        has_policy=True,
    )
    simulation["limitations"].extend(e.simulation["limitations"])
    for name, report in {
        "comparison": raw,
        "eda": e.eda,
        "permutation": e.permutation,
        "overview": e.summary,
        "simulation": e.simulation,
    }.items():
        audit[f"source-{name}.json"] = canonical_bytes(report)
    public_privacy_check(documents)
    return documents, partitions, models, policy, audit


def make_manifest(
    documents,
    partitions,
    models,
    policy,
    audit,
    release_id,
    generated_at,
    provenance,
    env,
    validations,
    snapshots,
):
    hashes = [{"role": "deterministic-json-input-v1", "sha256": sha256(audit["input.json"])}]
    hashes.extend(
        {"role": f"code:{name}", "sha256": sha256(raw)} for name, raw in snapshots.items()
    )
    dataset = {
        "dataset_id": demo.DATASET_VERSION,
        "dataset_version": demo.DATASET_VERSION,
        "origin": "synthetic",
        "source": {
            "generator": "src/credit_risk/presentation/demo.py:demonstration_frame",
            "seed": 42,
            "configuration": "400 registros; gerador original; "
            "split_data padrão 0.6/0.2/0.2, seed=42; sem dados importados",
            "representation": "deterministic-json-input-v1: objeto columns/rows na ordem "
            "do gerador; JSON UTF-8 sort_keys=True indent=2 ensure_ascii=False, "
            "allow_nan=False, LF final; cópia somente em evidência local restrita",
        },
        "license": {
            "generation": "Geração artificial local, sem dados pessoais ou fonte UCI",
            "publication_conditions": "Somente agregados sintéticos em lista positiva; "
            "revisão humana pendente conforme docs/evidencias-web.md",
        },
        "obtained_at_utc": None,
        "source_hashes": hashes,
        "population": f"{len(json.loads(audit['input.json'])['rows'])} registros artificiais "
        "antes da divisão; denominadores efetivos nas partições",
        "observation_unit": "registro artificial, não cliente real",
        "reference_period": None,
        "horizon": "um mês hipotético",
        "currency": None,
        "target": {
            "name": TARGET,
            "positive_class": 1,
            "meaning": "inadimplência artificial sorteada pelo gerador",
            "availability_assumption": "Atributos gerados artificialmente; "
            "não há verificação de disponibilidade temporal observada",
        },
        "quality": None,
        "partitions": partitions,
        "limitations": list(LIMITATIONS),
    }
    results = []
    for filename, result in documents.items():
        raw = canonical_bytes(result)
        results.append(
            {
                **select(result, "result_id kind dataset_id partition_id model_id policy_id"),
                "availability": "available",
                "reason": None,
                "path": filename,
                "sha256": sha256(raw),
                "bytes": len(raw),
            }
        )
    for kind in ("calibration", "final_evaluation"):
        results.append(
            unavailable(
                f"synthetic-{kind}",
                kind,
                "Calibração não executada; referência identity sem seleção."
                if kind == "calibration"
                else "Teste reservado não avaliado; nenhuma avaliação final executada.",
            )
        )
    for kind in KINDS:
        results.append(
            unavailable(
                f"real-{kind}",
                kind,
                "Resultado real indisponível: nenhuma fonte real importada, "
                "nenhum artefato real verificado ou revisão de privacidade real.",
            )
        )
    result = {
        "schema_version": SCHEMA,
        "release_id": release_id,
        "generated_at_utc": generated_at,
        "producer": {**provenance, "exporter_version": EXPORTER, "environment": env},
        "datasets": [dataset],
        "models": models,
        "policies": [policy],
        "results": results,
        "validation": validations,
        "publication_review": {
            "reviewed_at_utc": None,
            "reviewer": None,
            "decision": "pending",
            "scope": "Candidato sintético para revisão; sem autorização de publicação",
            "privacy_policy": "docs/evidencias-web.md#privacidade-e-revisão",
        },
        "limitations": list(LIMITATIONS),
    }
    public_privacy_check(result)
    return result


def unavailable(result_id, kind, reason):
    return {
        "result_id": result_id,
        "kind": kind,
        "dataset_id": None,
        "partition_id": None,
        "model_id": None,
        "policy_id": None,
        "availability": "unavailable",
        "reason": reason,
        "path": None,
        "sha256": None,
        "bytes": None,
    }


def validate_with_node(release_id: str, root: Path) -> str:
    command = [
        "node",
        "--experimental-strip-types",
        "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
        "scripts/validate-release.ts",
        release_id,
        str(root),
    ]
    return subprocess.check_output(command, cwd=WEB, text=True, encoding="utf-8")


def run_python_checks(provenance) -> dict:
    # Export tests call pure functions, never this CLI: no recursive pytest execution.
    files = [
        "web/exporters/tests",
        "tests/test_demo.py",
        "tests/test_eda.py",
        "tests/test_reference.py",
        "tests/test_comparison.py",
        "tests/test_splitting.py",
        "tests/test_interpretation.py",
        "tests/test_simulation.py",
    ]
    temporary_root = WEB / "reports"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="credit-web-checks-", dir=temporary_root) as temporary:
        report = Path(temporary) / "pytest.xml"
        command = [
            sys.executable,
            "-m",
            "pytest",
            *files,
            "-q",
            "-p",
            "no:cacheprovider",
            f"--basetemp={Path(temporary) / 'pytest'}",
            f"--junitxml={report}",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode:
            sys.stderr.write(completed.stdout + completed.stderr)
            raise RuntimeError("Testes Python falharam; nenhum pacote foi promovido")
        suites = ET.parse(report).getroot().findall("testsuite")
        total = sum(int(s.get("tests", "0")) for s in suites)
        skipped = [
            case.get("name", "teste sem nome")
            for suite in suites
            for case in suite.findall("testcase")
            if case.find("skipped") is not None
        ]
        return {
            "command": "python -m pytest "
            + " ".join(files)
            + " -q -p no:cacheprovider --basetemp=<temporário>/pytest "
            "--junitxml=<temporário>/pytest.xml",
            "revision": provenance["code_revision"],
            "exit_code": completed.returncode,
            "summary": f"{total} testes executados; {len(skipped)} ignorados; "
            "saída JUnit conferida; sem PostgreSQL ou fonte externa",
            "skipped_tests": skipped,
        }


def export_release(release_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", release_id):
        raise ValueError("Identificador de release inválido")
    target, private_target = RELEASES / release_id, PRIVATE / release_id
    if target.exists() or private_target.exists():
        raise FileExistsError(
            "Release/evidência já existe; use um novo identificador, sem sobrescrever"
        )
    provenance = git_provenance()
    snapshots = source_snapshots()
    validation = run_python_checks(provenance)
    evidence = compute_evidence()
    frozen_at = utc_now()  # Actual snapshot time; the rule was fixed in code, never tuned.
    documents, partitions, models, policy, audit = project_evidence(evidence, release_id, frozen_at)
    manifest = make_manifest(
        documents,
        partitions,
        models,
        policy,
        audit,
        release_id,
        utc_now(),
        provenance,
        environment(),
        [validation],
        snapshots,
    )
    # Staging is outside src/data; a failed export cannot poison a Next.js build.
    staging_parent = WEB / "reports"
    staging_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="export-stage-", dir=staging_parent) as temporary:
        stage_root = Path(temporary)
        stage = stage_root / release_id
        stage.mkdir()
        for name, document in {**documents, "manifest.json": manifest}.items():
            (stage / name).write_bytes(canonical_bytes(document))
        validate_with_node(release_id, stage_root)
        manifest["validation"].append(
            {
                "command": "node --experimental-strip-types scripts/validate-release.ts "
                "<release-id> <staging-root>",
                "revision": provenance["code_revision"],
                "exit_code": 0,
                "summary": "Schemas TypeScript, integridade e paridade financeira "
                "da grade contra simulate_policies aprovados com tolerância relativa 1e-10",
                "skipped_tests": [],
            }
        )
        (stage / "manifest.json").write_bytes(canonical_bytes(manifest))
        validate_with_node(release_id, stage_root)
        if git_provenance() != provenance or source_snapshots() != snapshots:
            raise RuntimeError("Código/Git mudou durante a exportação; execute novamente")
        # Local restricted audit never lives under public/ or src/data/.
        private_target.mkdir(parents=True, exist_ok=False)
        for name, raw in audit.items():
            (private_target / name).write_bytes(raw)
        for name, raw in snapshots.items():
            destination = private_target / "source-code" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        (private_target / "manifest.json").write_bytes(canonical_bytes(manifest))
        RELEASES.mkdir(parents=True, exist_ok=True)
        # Both absolute targets are fixed children of the intended output roots.
        if target.resolve().parent != RELEASES.resolve():
            raise ValueError("Destino fora da pasta de releases")
        os.rename(stage, target)  # New immutable directory; never overwrites an existing release.
    return target


def verify_release(release_id: str) -> None:
    """Recalcula só desenvolvimento sintético; não altera release nem evidências."""
    validate_with_node(release_id, RELEASES)
    existing = json.loads((RELEASES / release_id / "manifest.json").read_text(encoding="utf-8"))
    if existing["producer"]["exporter_version"] != EXPORTER:
        raise ValueError("Exportador incompatível")
    if existing["producer"]["environment"] != environment():
        raise ValueError("Ambiente diverge; reprodução byte a byte exige as versões registradas")
    expected_sources = {
        item["role"][5:]: item["sha256"]
        for item in existing["datasets"][0]["source_hashes"]
        if item["role"].startswith("code:")
    }
    if {name: sha256(raw) for name, raw in source_snapshots().items()} != expected_sources:
        raise ValueError("Código diverge da release; utilize o snapshot local revisado")
    evidence = compute_evidence()
    documents, partitions, models, policy, audit = project_evidence(
        evidence, release_id, existing["policies"][0]["frozen_at_utc"]
    )
    for name, value in documents.items():
        if canonical_bytes(value) != (RELEASES / release_id / name).read_bytes():
            raise ValueError(f"Artefato não reproduzível: {name}")
    if (
        partitions != existing["datasets"][0]["partitions"]
        or models != existing["models"]
        or [policy] != existing["policies"]
        or sha256(audit["input.json"]) != existing["datasets"][0]["source_hashes"][0]["sha256"]
    ):
        raise ValueError("Procedência não reproduzível")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--release-id", help="Novo ID imutável; sempre gera candidato pendente")
    group.add_argument("--verify", help="Regenerar em memória e conferir release existente")
    args = parser.parse_args()
    if args.verify:
        verify_release(args.verify)
        print("Reprodução aprovada: artefatos, dados, partições, modelos e política coincidem.")
    else:
        path = export_release(args.release_id)
        print(f"Candidato sintético gerado: web/src/data/releases/{path.name}; revisão pendente.")


if __name__ == "__main__":
    main()
