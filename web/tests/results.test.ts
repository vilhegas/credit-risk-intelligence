import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import type { Manifest, OverviewResult } from "../src/types/results.ts";
import { loadRelease, validateAllReleases } from "../src/lib/data/releases.ts";
import { validateManifest, validateOverview } from "../src/lib/schemas/results.ts";
import { parseStrictJson } from "../src/lib/schemas/strict-json.ts";
import { validateAnalysis } from "../src/lib/schemas/analysis.ts";

// Artificial test cases only: never exported into src/data or the application.
const hash = "a".repeat(64);
const revision = "b".repeat(40);
const date = "2026-10-20T12:00:00Z";
function result(): OverviewResult {
  return { schema_version: "credit-risk-web-v1", release_id: "test-only", result_id: "summary", kind: "overview",
    dataset_id: "sample", partition_id: "validation", model_id: null, policy_id: null, origin: "synthetic",
    source_contract: "demo.indicators@demo-synthetic-v1", observations: 10,
    payload: { defaults: 2, non_defaults: 8, default_rate: 0.2 }, metric_notes: {}, limitations: ["Fixture artificial de teste"] };
}
function manifest(bytes: Buffer): Manifest {
  return { schema_version: "credit-risk-web-v1", release_id: "test-only", generated_at_utc: date,
    producer: { code_revision: revision, working_tree_clean: true, exporter_version: "test", environment: { python: "test-only" } },
    datasets: [{ dataset_id: "sample", dataset_version: "test", origin: "synthetic", source: { generator: "tests/results.test.ts", seed: 1, configuration: "Somente testes", representation: "JSON determinístico da fixture" },
      license: { generation: "Fixture local", publication_conditions: "Somente testes" }, obtained_at_utc: null, source_hashes: [{ role: "deterministic-json-input", sha256: hash }],
      population: "Fixture", observation_unit: "Registro artificial", reference_period: null, horizon: "Fictício", currency: null,
      target: { name: "default", positive_class: 1, meaning: "Fixture", availability_assumption: "Fixture" }, quality: null,
      partitions: [{ partition_id: "validation", role: "validation", observations: 10, class_counts: { "0": 8, "1": 2 }, method: "Fixture", partition_sha256: hash, used_for: ["Teste"] }],
      limitations: ["Sem período, moeda ou tratamento; dados artificiais apenas para testes"] }], models: [], policies: [],
    results: [{ result_id: "summary", kind: "overview", dataset_id: "sample", partition_id: "validation", model_id: null, policy_id: null,
      availability: "available", reason: null, path: "overview.json", sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length }],
    validation: [{ command: "fixture", revision, exit_code: 0, summary: "Fixture, não é evidência de execução", skipped_tests: [] }],
    publication_review: { reviewed_at_utc: date, reviewer: "Fixture", scope: "Teste", privacy_policy: "Fixture", decision: "approved" }, limitations: ["Somente testes"] };
}
async function withRelease(run: (root: string, m: Manifest, r: OverviewResult, directory: string) => Promise<void>) {
  const root = await mkdtemp(path.join(os.tmpdir(), "credit-risk-web-test-"));
  try {
    const directory = path.join(root, "test-only"); await mkdir(directory);
    const r = result(); const bytes = Buffer.from(JSON.stringify(r)); const m = manifest(bytes);
    await writeFile(path.join(directory, "overview.json"), bytes);
    await writeFile(path.join(directory, "manifest.json"), JSON.stringify(m));
    await run(root, m, r, directory);
  } finally { await rm(root, { recursive: true, force: true }); }
}

test("JSON estrito rejeita duplicatas, valores não finitos, comentários e UTF-8 inválido", () => {
  for (const input of ['{"a":1,"a":2}', '{"a":1,"\\u0061":2}', '{"x":{"a":1,"a":2}}', '{"a":NaN}', '{"a":1e400}', '{"a":Infinity}', '{"a":1,}', '// comment\n{}', '{}{}', '[1,]', '{"x":"\\q"}', '\ufeff{}', '['.repeat(102) + '0' + ']'.repeat(102)]) {
    assert.throws(() => parseStrictJson(Buffer.from(input)), Error, input);
  }
  assert.throws(() => parseStrictJson(Uint8Array.from([0xff])));
  assert.deepEqual(parseStrictJson(Buffer.from('{"a":[1,true,null,"text"]}')), { a: [1, true, null, "text"] });
});
test("overview válido e zero calculado são preservados; população vazia exige nota", () => {
  assert.deepEqual(validateOverview(result()), result());
  const r = result(); r.payload = { defaults: 0, non_defaults: 10, default_rate: 0 }; validateOverview(r);
  r.observations = 0; r.payload = { defaults: 0, non_defaults: 0, default_rate: null };
  assert.throws(() => validateOverview(r)); r.metric_notes["payload.default_rate"] = "Denominador zero"; validateOverview(r);
});
test("overview rejeita números em strings, faixas, contagens, taxas, versões e campos extras", () => {
  const mutations = [
    { schema_version: "v2" }, { observations: "10" }, { observations: -1 }, { observations: Number.MAX_SAFE_INTEGER + 1 },
    { payload: { defaults: 2, non_defaults: 7, default_rate: 0.2 } }, { payload: { defaults: 2, non_defaults: 8, default_rate: 1.2 } },
    { payload: { defaults: 2, non_defaults: 8, default_rate: 0.3 } }, { payload: { defaults: 2, non_defaults: 8, default_rate: null } },
    { payload: { defaults: 2.5, non_defaults: 7.5, default_rate: 0.25 } }, { payload: { defaults: 2, non_defaults: 8, default_rate: NaN } },
    { unexpected: true }, { origin: "real" }, { source_contract: "unknown" },
  ];
  for (const change of mutations) assert.throws(() => validateOverview({ ...result(), ...change }));
});
test("manifesto rejeita metadados incompletos, revisões, datas e referências incompatíveis", () => {
  const base = manifest(Buffer.from("test")); validateManifest(base);
  for (const mutate of [
    (m: Manifest) => { m.producer.working_tree_clean = false as true; },
    (m: Manifest) => { m.producer.code_revision = "short"; },
    (m: Manifest) => { m.generated_at_utc = "2026-02-30T12:00:00Z"; },
    (m: Manifest) => { m.producer.environment = {}; },
    (m: Manifest) => { m.datasets[0].partitions[0].observations = 11; },
    (m: Manifest) => { m.results[0].model_id = "missing"; },
    (m: Manifest) => { m.results[0].partition_id = "missing"; },
    (m: Manifest) => { m.results[0].dataset_id = "missing"; },
    (m: Manifest) => { m.results.push(m.results[0]); },
    (m: Manifest) => { Object.assign(m.datasets[0], { origin: "real" }); },
    (m: Manifest) => { m.publication_review.decision = "rejected" as "approved"; },
  ]) { const m = structuredClone(base); mutate(m); assert.throws(() => validateManifest(m)); }
});
test("carregamento sintético verifica bytes, hash e denominador", async () => {
  await withRelease(async (root) => {
    const loaded = await loadRelease("test-only", root); assert.equal(loaded.status, "available");
    if (loaded.status === "available") assert.equal(loaded.results.summary.status, "synthetic");
    assert.equal(await validateAllReleases(root), 1);
  });
});
test("origem real revisada permanece distinta da demonstração", async () => {
  await withRelease(async (root, m, r, directory) => {
    Object.assign(m.datasets[0], { origin: "real", obtained_at_utc: date,
      source: { title: "Fixture", publisher: "Fixture", reference: "Fixture", url: "https://example.org/source" },
      license: { attribution: "Fixture", url: "https://example.org/license", checked_at_utc: date } });
    m.datasets[0].source_hashes = [{ role: "zip", sha256: hash }, { role: "xls", sha256: hash }];
    r.origin = "real"; r.source_contract = "analysis.eda.analyze@uci-350-eda-v1";
    const bytes = Buffer.from(JSON.stringify(r));
    if (m.results[0].availability === "available") { m.results[0].bytes = bytes.length; m.results[0].sha256 = createHash("sha256").update(bytes).digest("hex"); }
    await writeFile(path.join(directory, "overview.json"), bytes); await writeFile(path.join(directory, "manifest.json"), JSON.stringify(m));
    const loaded = await loadRelease("test-only", root);
    if (loaded.status !== "available") assert.fail();
    assert.equal(loaded.results.summary.status, "real_verified");
  });
});
test("ausência explícita não contém números, e release solicitada ausente é erro", async () => {
  assert.equal((await loadRelease()).status, "unavailable");
  await withRelease(async (root, m, _r, directory) => {
    await rm(path.join(directory, "overview.json"));
    m.datasets = []; m.results = [{ result_id: "pending", kind: "final_evaluation", dataset_id: null, partition_id: null, model_id: null, policy_id: null,
      availability: "unavailable", reason: "Não executado", path: null, sha256: null, bytes: null }];
    await writeFile(path.join(directory, "manifest.json"), JSON.stringify(m));
    const loaded = await loadRelease("test-only", root);
    if (loaded.status !== "available") assert.fail();
    assert.deepEqual(loaded.results.pending, { status: "unavailable", kind: "final_evaluation", reason: "Não executado" });
    await assert.rejects(loadRelease("missing", root));
  });
});
test("arquivos ausentes, inválidos, adulterados, não catalogados e versões incompatíveis falham", async () => {
  for (const mode of ["missing", "json", "hash", "bytes", "extra", "version", "origin", "denominator", "unsupported"]) {
    await withRelease(async (root, m, r, directory) => {
      const file = path.join(directory, "overview.json");
      if (mode === "missing") await rm(file);
      if (mode === "json") {
        const bytes = Buffer.from("{bad}"); await writeFile(file, bytes);
        m.results[0].bytes = bytes.length; m.results[0].sha256 = createHash("sha256").update(bytes).digest("hex");
      }
      if (mode === "hash") m.results[0].sha256 = "c".repeat(64);
      if (mode === "bytes") m.results[0].bytes = 1;
      if (mode === "extra") await writeFile(path.join(directory, "private.json"), "{}");
      if (["version", "origin", "denominator"].includes(mode)) {
        if (mode === "version") (r as { schema_version: string }).schema_version = "v2";
        if (mode === "origin") r.origin = "real";
        if (mode === "denominator") { r.observations = 20; r.payload.non_defaults = 18; r.payload.default_rate = 0.1; }
        const bytes = Buffer.from(JSON.stringify(r)); await writeFile(file, bytes);
        m.results[0].bytes = bytes.length; m.results[0].sha256 = createHash("sha256").update(bytes).digest("hex");
      }
      if (mode === "unsupported") {
        m.results[0].kind = "eda"; m.results[0].path = "eda.json";
        await writeFile(path.join(directory, "eda.json"), JSON.stringify(r)); await rm(file);
      }
      await writeFile(path.join(directory, "manifest.json"), JSON.stringify(m));
      await assert.rejects(loadRelease("test-only", root), Error, mode);
      await assert.rejects(validateAllReleases(root), Error, `Verificação do build: ${mode}`);
    });
  }
});

function analysisFixtures() {
  const m = manifest(Buffer.from("fixture")); const d = m.datasets[0];
  const partition = d.partitions[0];
  d.partitions.push({ ...partition, partition_id: "train", role: "train" }, { ...partition, partition_id: "calibration", role: "calibration" });
  m.models.push({ model_id: "model", dataset_id: d.dataset_id, model_version: "fixture-v1", family: "logistic", features: ["LIMIT_BAL"], configuration: "Fixture", partition_sha256: hash, model_sha256: hash, calibration_method: "identity" });
  m.policies.push({ policy_id: "policy", model_id: "model", policy_sha256: hash, threshold: 0.5, configuration: "Fixture", frozen_at_utc: date });
  const point = { bin: 2, count: 10, mean_probability: 0.2, default_rate: 0.2 };
  const scores = { average_precision: 0.2, roc_auc: 0.5, brier_score: 0.16 };
  const amounts = ["LIMIT_BAL", ...Array.from({ length: 6 }, (_, i) => `BILL_AMT${i + 1}`), ...Array.from({ length: 6 }, (_, i) => `PAY_AMT${i + 1}`)];
  const pay = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"];
  const thresholdRow = { threshold: 0.5, observations: 10, confusion_matrix: [[8, 0], [2, 0]], tn: 8, fp: 0, fn: 2, tp: 0,
    approved: 10, approval_rate: 1, approved_default_rate: 0.2, default_recall: 0, total_cost: 2, mean_cost: 0.2, feasible: true };
  const payloads = {
    eda: { target: { class_counts: { "0": 8, "1": 2 }, default_rate: 0.2, minority_majority_ratio: 0.25, both_classes_present: true },
      missing: Object.fromEntries([...amounts, ...pay].map((name) => [name, { count: 0, rate: 0 }])),
      distributions: Object.fromEntries(amounts.map((name) => [name, { observed: 10, minimum: 0, q25: 2, median: 4, q75: 6, maximum: 9, mean: 4.5, std_sample: 3,
        histogram: Array.from({ length: 10 }, (_, i) => ({ lower: i, upper: i + 1, count: 1 })) }])),
      patterns: Object.fromEntries([...pay, "LIMIT_BAL"].map((name) => [name, [{ group: "fixture", observations: 10, defaults: 2, default_rate: 0.2 }]])), correlations: [] },
    comparison: { reference: { model_version: "uci-350-reference-v1", seed: 1, features: ["LIMIT_BAL"], configuration: "Fixture", train_partition_id: "train",
      train: { observations: 10, prevalence: 0.2 }, validation: { observations: 10, prevalence: 0.2, scores: { logistic: scores, dummy: scores }, average_precision_difference: 0, logistic_above_dummy: false } }, comparison: null },
    calibration: { version: "credit-calibration-v1", development_version: "fixture", calibration_partition_id: "calibration", disjointness_verification: "Fixture",
      calibration_observations: 10, selection_observations: 10, minimum_brier_gain: 0, observed_brier_gain: 0,
      before: { observations: 10, brier_score: 0.16, strategy: "uniform", bins_requested: 10, curve: [point] },
      sigmoid_candidate: { observations: 10, brier_score: 0.16, strategy: "uniform", bins_requested: 10, curve: [point] }, calibration_selected: "identity",
      policy: { threshold: 0.5, calibration_method: "identity", false_negative_cost: 1, false_positive_cost: 1, min_approval_rate: 0, min_default_recall: 0, slope: 1, intercept: 0 },
      threshold_table: [thresholdRow], selected: thresholdRow, tie_break: "Menor custo; menor limiar" },
    interpretation: { permutation: { version: "permutation-v1", dataset_version: "test", observations: 10, baseline_average_precision: 0.2, repeats: 2, seed: 1,
      factors: [{ feature: "LIMIT_BAL", mean_ap_decrease: -0.02, permutation_std: 0.01, permutation_quantiles_025_975: [-0.03, -0.01] }] }, segments: null },
    final_evaluation: { version: "final-evaluation-v1", threshold: 0.5, metrics: { observations: 10, prevalence: 0.2, average_precision: 0.2, baseline_average_precision: 0.2,
      average_precision_difference: 0, roc_auc: 0.5, baseline_roc_auc: 0.5, brier_score: 0.16, baseline_brier_score: 0.16, precision: null, recall: 0, f1: 0,
      confusion_matrix: [[8, 0], [2, 0]], approval_rate: 1, approved_default_rate: 0.2 }, calibration_curve: [point], above_baseline_descriptive: false,
      frozen: { dataset_sha256: hash, partition_sha256: hash, model_sha256: hash, policy_sha256: hash, code_revision: revision,
        environment: { python: "fixture" }, frozen_at_utc: date, restricted_manifest_sha256: hash, alignment_verification: "Fixture", calibration_once_verification: "Fixture", reserved_test_verification: "Fixture" },
      uncertainty: { method: "bootstrap pareado por observação, percentil pontual de 95%", seed: 1, requested_resamples: 100, single_class_resamples_skipped: 0,
        intervals: Object.fromEntries(["average_precision", "baseline_average_precision", "average_precision_difference", "roc_auc", "brier_score", "approval_rate", "approved_default_rate", "precision", "recall", "f1"].map((key) => [key, { valid_resamples: 100, lower: key === "average_precision_difference" ? -0.1 : 0, upper: 0.5 }])) } },
    simulation: { report: { simulation_version: "credit-policy-v1", dataset_version: "test", model_version: "fixture-v1", currency: "Unidade artificial", horizon: "Fixture", exposure_assumption: "Constante de teste",
      thresholds: [0.3, 0.5, 0.8], scenarios: [{ name: "fixture", exposure_multiplier: 1, lgd: 0.5, revenue_rate: 0.01 }], observations: 10, defaults: 2,
      rows: [0.3, 0.5, 0.8].map((threshold) => ({ scenario: "fixture", threshold, observations: 10, approved: 10, rejected: 0, approval_rate: 1, approved_defaults: 2, approved_default_rate: 0.2, rejected_defaults: 0, default_recall: 0,
        approved_exposure: 100, expected_loss: 10, expected_revenue: 0.8, expected_margin_before_costs: -9.2, historical_scenario_loss: 10, historical_scenario_revenue: 0.8, historical_scenario_margin_before_costs: -9.2 })), limitations: ["Fixture artificial"] }, interactive_grid: null },
  };
  const sources = { eda: "analysis.eda.analyze@uci-350-eda-v1", comparison: "modeling.reference.train_reference@uci-350-reference-v1", calibration: "modeling.calibration.select_policy@credit-calibration-v1", interpretation: "modeling.interpretation.permutation_report@permutation-v1", final_evaluation: "modeling.final_evaluation.evaluate_once@final-evaluation-v1", simulation: "simulation.policies.simulate_policies@credit-policy-v1" };
  function fixture<K extends keyof typeof payloads>(kind: K) {
    const notes: Record<string, string> = {};
    const payload = structuredClone(payloads[kind]);
    function addNotes(value: unknown, current: string) {
      if (value === null) notes[current] = "Ausência explícita na fixture";
      else if (value && typeof value === "object") for (const [key, child] of Object.entries(value)) addNotes(child, `${current}.${key}`);
    }
    addNotes(payload, "payload");
    const r = { ...result(), kind, model_id: "model", policy_id: "policy", source_contract: sources[kind], payload, metric_notes: notes };
    const part = { ...partition, role: kind === "final_evaluation" ? "test" as const : kind === "calibration" ? "selection" as const : "validation" as const };
    return { r, m, d, part };
  }
  return { fixture };
}

for (const kind of ["eda", "comparison", "calibration", "interpretation", "final_evaluation", "simulation"] as const) {
  test(`${kind}: payload válido, produtor incompatível e campos desconhecidos`, () => {
    const { r, m, d, part } = analysisFixtures().fixture(kind);
    assert.equal(validateAnalysis(r, m, d, part).kind, kind);
    assert.throws(() => validateAnalysis({ ...r, source_contract: "unknown-v2" }, m, d, part));
    assert.throws(() => validateAnalysis({ ...r, payload: { ...r.payload, private_rows: [] } }, m, d, part));
    assert.throws(() => validateAnalysis({ ...r, observations: 11 }, m, d, part));
  });
}
test("invariantes específicos rejeitam resultados quantitativos incoerentes", () => {
  const fixtures = analysisFixtures();
  const eda = fixtures.fixture("eda"); eda.r.payload.missing.LIMIT_BAL.count = 1;
  assert.throws(() => validateAnalysis(eda.r, eda.m, eda.d, eda.part));
  const comparison = fixtures.fixture("comparison"); comparison.r.payload.reference.validation.average_precision_difference = 0.1;
  assert.throws(() => validateAnalysis(comparison.r, comparison.m, comparison.d, comparison.part));
  const calibration = fixtures.fixture("calibration"); calibration.r.payload.calibration_selected = "sigmoid";
  assert.throws(() => validateAnalysis(calibration.r, calibration.m, calibration.d, calibration.part));
  const interpretation = fixtures.fixture("interpretation"); interpretation.r.payload.permutation.factors[0].permutation_quantiles_025_975 = [0.1, -0.1];
  assert.throws(() => validateAnalysis(interpretation.r, interpretation.m, interpretation.d, interpretation.part));
  const final = fixtures.fixture("final_evaluation"); final.r.payload.uncertainty.intervals.average_precision.valid_resamples = 101;
  assert.throws(() => validateAnalysis(final.r, final.m, final.d, final.part));
  const simulation = fixtures.fixture("simulation"); simulation.r.payload.report.rows[0].expected_margin_before_costs = 0;
  assert.throws(() => validateAnalysis(simulation.r, simulation.m, simulation.d, simulation.part));
});

test("comparação preserva empate e convenção de precisão zero com nota", () => {
  const { r, m, d, part } = analysisFixtures().fixture("comparison");
  const names = ["logistic_c1", "dummy", "logistic_a", "logistic_b", "tree_a", "tree_b", "tree_c"];
  const table = names.map((candidate) => ({ candidate, family: candidate === "dummy" ? "dummy" : candidate.startsWith("tree") ? "tree" : "logistic",
    parameters: "Fixture", roc_auc: 0.5, average_precision: 0.2, precision: 0, recall: 0, predicted_positives: 0, ap_minus_reference: 0, ap_minus_dummy: 0 }));
  const comparison = { comparison_version: "credit-comparison-v1", seed: 1, validation_method: "stratified_client", train_partition_id: "train", threshold: 0.5,
    positive_class: 1, zero_division: 0, train_observations: 10, validation_observations: 10, train_prevalence: 0.2, validation_prevalence: 0.2,
    table, selected_candidate: "logistic_c1", selection_reason: "Fixture", tie_preference: names, selected_above_reference: false, selected_above_dummy: false };
  const value = { ...r, source_contract: "modeling.comparison.compare_models@credit-comparison-v1", payload: { ...r.payload, comparison } };
  assert.throws(() => validateAnalysis(value, m, d, part));
  table.forEach((_, i) => { value.metric_notes[`payload.comparison.table.${i}.precision`] = "zero_division=0 sem positivos previstos"; });
  validateAnalysis(value, m, d, part);
  comparison.selected_candidate = "dummy";
  assert.throws(() => validateAnalysis(value, m, d, part));
});

test("segmentos preservam Wilson e indisponibilidade matemática da precisão", () => {
  const { r, m, d, part } = analysisFixtures().fixture("interpretation");
  const zeroOfTwo = { numerator: 0, denominator: 2, value: 0, wilson_95: [0, 0.6576197724933469] };
  const metrics = { average_precision: 0.2, roc_auc: 0.5, brier_score: 0.16, mean_probability: 0.2, confusion_matrix: [[8, 0], [2, 0]],
    false_positive_rate: { numerator: 0, denominator: 8, value: 0, wilson_95: [0, 0.32440756488388023] },
    false_negative_rate: { numerator: 2, denominator: 2, value: 1, wilson_95: [0.34238022750665303, 1] },
    default_recall: zeroOfTwo, precision: { numerator: 0, denominator: 0, value: null, wilson_95: null },
    approval_rate: { numerator: 10, denominator: 10, value: 1, wilson_95: [0.7224672001371107, 1] },
    approved_default_rate: { numerator: 2, denominator: 10, value: 0.2, wilson_95: [0.05668215145437519, 0.5098375284633583] },
    calibration_curve: [{ bin: 2, count: 10, mean_probability: 0.2, observed: { numerator: 2, denominator: 10, value: 0.2, wilson_95: [0.05668215145437519, 0.5098375284633583] } }] };
  const segments = { version: "segments-v1", dataset_version: "test", threshold: 0.5, minimum_size: 2, minimum_class_count: 1, bins: 10, overall: metrics,
    segments: [{ segment: "fixture", observations: 10, defaults: 2, non_defaults: 8, sufficient: true, metrics, differences_from_overall: { average_precision: 0, roc_auc: 0, brier_score: 0 }, reason: null }] };
  const value = { ...r, source_contract: "modeling.interpretation.segment_report@segments-v1", payload: { permutation: null, segments }, metric_notes: {
    "payload.permutation": "Não executado", "payload.segments.overall.precision.value": "Nenhum positivo previsto", "payload.segments.overall.precision.wilson_95": "Denominador zero",
    "payload.segments.segments.0.metrics.precision.value": "Nenhum positivo previsto", "payload.segments.segments.0.metrics.precision.wilson_95": "Denominador zero" } };
  validateAnalysis(value, m, d, part);
  metrics.default_recall.wilson_95[1] = 1;
  assert.throws(() => validateAnalysis(value, m, d, part));
});

test("grade interativa exige paridade de contagens e soma de probabilidades válida", () => {
  const { r, m, d, part } = analysisFixtures().fixture("simulation");
  const interactive_grid = { exposure_mode: "constant", observations: 10, defaults: 2, probability_stage: "raw", parity_verification: "Fixture",
    rows: [0.3, 0.5, 0.8].map((threshold) => ({ threshold, approved: 10, approved_defaults: 2, approved_probability_sum: 2 })) };
  const value = { ...r, payload: { ...r.payload, interactive_grid } };
  validateAnalysis(value, m, d, part);
  interactive_grid.rows[0].approved_probability_sum = 11;
  assert.throws(() => validateAnalysis(value, m, d, part));
});
test("caminhos arbitrários e tentativas de traversal são rejeitados", async () => {
  for (const file of ["../overview.json", "/overview.json", "C:\\overview.json", "https://example.com/overview.json", "folder/overview.json"]) {
    const m = manifest(Buffer.from("test")); m.results[0].path = file; assert.throws(() => validateManifest(m));
  }
  await assert.rejects(loadRelease("../outside"));
});
