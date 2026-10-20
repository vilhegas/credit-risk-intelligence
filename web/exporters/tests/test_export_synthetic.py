"""Paridade com produtores originais, privacidade e reprodução de agregados sintéticos."""

import copy
import json

import numpy as np
import pytest
from web.exporters import export_synthetic as export

FIXTURE_TIME = "2026-10-20T12:00:00Z"  # Test fixture only, never used by the real CLI.


@pytest.fixture(scope="module")
def evidence():
    return export.compute_evidence()


@pytest.fixture(scope="module")
def package(evidence):
    return export.project_evidence(evidence, "test-only", FIXTURE_TIME)


def test_public_fields_equal_original_python_reports(evidence, package):
    documents, _, _, _, _ = package
    overview = documents["overview.json"]
    assert overview["payload"]["defaults"] == evidence.summary["defaults"]
    assert overview["payload"]["default_rate"] == evidence.summary["default_rate"]
    assert overview["observations"] == evidence.summary["observations"]
    eda = documents["eda.json"]["payload"]
    assert eda == export.select(evidence.eda, "target missing distributions patterns correlations")
    comparison = documents["comparison.json"]["payload"]
    raw = evidence.comparison.report
    assert comparison["reference"]["validation"] == raw["reference_report"]["validation"]
    assert comparison["reference"]["train"] == raw["reference_report"]["train"]
    assert (
        json.loads(comparison["reference"]["configuration"])
        == (raw["reference_report"]["configuration"])
    )
    for actual, expected in zip(comparison["comparison"]["table"], raw["table"], strict=True):
        assert {**actual, "parameters": json.loads(actual["parameters"])} == expected
    assert comparison["comparison"]["selected_candidate"] == raw["selected_candidate"]
    interpretation = documents["interpretation.json"]["payload"]
    assert interpretation["permutation"] == export.select(
        evidence.permutation,
        "version dataset_version observations " "baseline_average_precision repeats seed factors",
    )
    assert interpretation["segments"] is None
    assert documents["simulation.json"]["payload"]["report"] == evidence.simulation


def test_denominators_and_disjointness_are_preserved(evidence, package):
    documents, partitions, _, _, audit = package
    assert len(evidence.frame) == 400
    assert documents["eda.json"]["observations"] == len(evidence.split.train.y) == 240
    assert documents["overview.json"]["observations"] == len(evidence.split.validation.y) == 80
    assert all(d["origin"] == "synthetic" for d in documents.values())
    train = set(evidence.split.train.positions)
    validation = set(evidence.split.validation.positions)
    assert not train.intersection(validation)
    for part in partitions:
        assert sum(part["class_counts"].values()) == part["observations"]
        raw = audit[f"partition-{part['partition_id']}.json"]
        assert export.sha256(raw) == part["partition_sha256"]
        assert json.loads(raw)["positions"] == list(
            getattr(evidence.split, part["partition_id"]).positions
        )


def test_reference_for_simulation_is_not_replaced_by_selected_candidate(evidence, package):
    documents, _, models, policy, audit = package
    simulation = documents["simulation.json"]
    assert simulation["model_id"] == export.model_id("logistic_c1") == policy["model_id"]
    assert simulation["payload"]["report"]["model_version"] == export.demo.MODEL_VERSION
    for model in models:
        candidate = model["model_id"].removeprefix("synthetic-")
        assert model["model_sha256"] == export.sha256(audit[f"model-{candidate}.pkl"])
        assert json.loads(model["configuration"])["estimator_parameters"] == (
            evidence.comparison.models[candidate].named_steps["classifier"].get_params(deep=False)
        )
    assert policy["policy_sha256"] == export.sha256(audit["policy.json"])


def test_grid_matches_original_predictions_without_exporting_them(evidence, package):
    documents = package[0]
    grid = documents["simulation.json"]["payload"]["interactive_grid"]
    y = evidence.split.validation.y.to_numpy()
    for row in grid["rows"]:
        mask = evidence.probability < row["threshold"]
        assert row["approved"] == int(mask.sum())
        assert row["approved_defaults"] == int(y[mask].sum())
        assert row["approved_probability_sum"] == float(evidence.probability[mask].sum())
        source = next(r for r in evidence.simulation["rows"] if r["threshold"] == row["threshold"])
        assert row["approved"] == source["approved"]
        assert row["approved_defaults"] == source["approved_defaults"]
    assert grid["rows"][0]["approved"] == 0  # p < 0 never approves.
    assert evidence.simulation["rows"][0]["approved_default_rate"] is None
    assert (
        "payload.report.rows.0.approved_default_rate"
        in documents["simulation.json"]["metric_notes"]
    )


def test_repeated_computation_reproduces_bytes_and_fitted_model_hashes(package):
    second = export.project_evidence(export.compute_evidence(), "test-only", FIXTURE_TIME)
    for first, repeated in zip(package[:4], second[:4], strict=True):
        assert export.canonical_bytes(first) == export.canonical_bytes(repeated)
    assert package[4] == second[4]


def fixture_manifest(package):
    documents, partitions, models, policy, audit = package
    provenance = export.git_provenance()
    return export.make_manifest(
        documents,
        partitions,
        models,
        policy,
        audit,
        "test-only",
        FIXTURE_TIME,
        provenance,
        export.environment(),
        [
            {
                "command": "unit-test fixture (not execution evidence)",
                "revision": provenance["code_revision"],
                "exit_code": 0,
                "summary": "Only a test fixture",
                "skipped_tests": [],
            }
        ],
        export.source_snapshots(),
    )


def test_manifest_integrity_real_absence_and_pending_review(package):
    manifest = fixture_manifest(package)
    assert manifest["publication_review"]["decision"] == "pending"
    assert manifest["publication_review"]["reviewer"] is None
    assert manifest["publication_review"]["reviewed_at_utc"] is None
    assert (
        manifest["producer"]["working_tree_clean"] == export.git_provenance()["working_tree_clean"]
    )
    for entry in manifest["results"]:
        if entry["availability"] == "available":
            raw = export.canonical_bytes(package[0][entry["path"]])
            assert len(raw) == entry["bytes"]
            assert export.sha256(raw) == entry["sha256"]
        else:
            assert all(
                entry[key] is None
                for key in (
                    "path",
                    "sha256",
                    "bytes",
                    "dataset_id",
                    "partition_id",
                    "model_id",
                    "policy_id",
                )
            )
            assert entry["reason"]
    assert len([r for r in manifest["results"] if r["result_id"].startswith("real-")]) == 7
    assert {r["kind"] for r in manifest["results"] if r["availability"] == "available"} == {
        "overview",
        "eda",
        "comparison",
        "interpretation",
        "simulation",
    }


def test_public_package_contains_no_private_fields_or_serialized_models(package):
    documents = package[0]
    export.public_privacy_check({**documents, "manifest.json": fixture_manifest(package)})
    assert set(documents) == {
        "overview.json",
        "eda.json",
        "comparison.json",
        "interpretation.json",
        "simulation.json",
    }
    bad = copy.deepcopy(documents)
    bad["overview.json"]["payload"]["ID"] = [1, 2]
    with pytest.raises(ValueError, match="Campo individual"):
        export.public_privacy_check(bad)
    with pytest.raises(ValueError):
        export.canonical_bytes({"invalid": np.nan})


def test_typescript_validators_and_financial_grid_parity_accept_generated_candidate(
    tmp_path, package
):
    release = tmp_path / "test-only"
    release.mkdir()
    documents = {**package[0], "manifest.json": fixture_manifest(package)}
    for name, value in documents.items():
        (release / name).write_bytes(export.canonical_bytes(value))
    assert "pending" in export.validate_with_node("test-only", tmp_path)
    # Alter data and update its checksum: semantic checks must still catch the corruption.
    value = copy.deepcopy(documents["overview.json"])
    value["payload"]["default_rate"] = 0.999
    raw = export.canonical_bytes(value)
    (release / "overview.json").write_bytes(raw)
    entry = next(r for r in documents["manifest.json"]["results"] if r["path"] == "overview.json")
    entry.update(bytes=len(raw), sha256=export.sha256(raw))
    (release / "manifest.json").write_bytes(export.canonical_bytes(documents["manifest.json"]))
    with pytest.raises(export.subprocess.CalledProcessError):
        export.validate_with_node("test-only", tmp_path)


def test_reserved_test_is_never_accessed_for_analytics(monkeypatch):
    original = export.split_data

    def split_without_test(*args, **kwargs):
        split = original(*args, **kwargs)

        class NoTest:
            train = split.train
            validation = split.validation
            metadata = split.metadata

            @property
            def test(self):
                raise AssertionError("A análise não pode acessar o teste reservado")

        return NoTest()

    monkeypatch.setattr(export, "split_data", split_without_test)
    export.project_evidence(export.compute_evidence(), "test-only", FIXTURE_TIME)


def test_existing_releases_are_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setattr(export, "RELEASES", tmp_path / "releases")
    monkeypatch.setattr(export, "PRIVATE", tmp_path / "audit")
    (export.RELEASES / "existing").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        export.export_release("existing")
    with pytest.raises(ValueError):
        export.export_release("../outside")


def test_failed_validation_does_not_promote_partial_release(tmp_path, monkeypatch, evidence):
    monkeypatch.setattr(export, "RELEASES", tmp_path / "releases")
    monkeypatch.setattr(export, "PRIVATE", tmp_path / "audit")
    monkeypatch.setattr(export, "compute_evidence", lambda: evidence)
    monkeypatch.setattr(
        export,
        "run_python_checks",
        lambda provenance: {
            "command": "unit-test fixture",
            "revision": provenance["code_revision"],
            "exit_code": 0,
            "summary": "Fixture",
            "skipped_tests": [],
        },
    )

    def fail(*_args):
        raise RuntimeError("Validation failed deliberately inside a unit test")

    monkeypatch.setattr(export, "validate_with_node", fail)
    with pytest.raises(RuntimeError, match="Validation failed"):
        export.export_release("not-promoted")
    assert not (export.RELEASES / "not-promoted").exists()
    assert not (export.PRIVATE / "not-promoted").exists()
