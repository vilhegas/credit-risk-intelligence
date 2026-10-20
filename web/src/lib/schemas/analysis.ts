import { schemaVersion } from "../../types/results.ts";
import type { Dataset, Manifest, Partition } from "../../types/results.ts";
import { count, hash, identifier, list, literal, nullable, number, numericTolerance, object, rate, record, requireCondition as ensure, revision, text, texts, utc } from "./results.ts";
import type { Check, Infer } from "./results.ts";

const bool: Check<boolean> = (v) => ensure(typeof v === "boolean", "Booleano obrigatório");
const nonnegative: Check<number> = (v) => { number(v); ensure((v as number) >= 0, "Valor negativo"); };
const signedRate: Check<number> = (v) => { number(v); ensure(Math.abs(v as number) <= 1, "Fora de [-1,1]"); };
const pair = <T>(check: Check<T>): Check<[T, T]> => (v) => { list(check)(v); ensure((v as T[]).length === 2, "Par obrigatório"); };
const matrix = pair(pair(count));
const amounts = ["LIMIT_BAL", ...Array.from({ length: 6 }, (_, i) => `BILL_AMT${i + 1}`), ...Array.from({ length: 6 }, (_, i) => `PAY_AMT${i + 1}`)];
const pay = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"];
const feature = literal(...amounts, ...pay);
const financialRecord = <T>(check: Check<T>, allowed: string[]): Check<Record<string, T>> => (v) => {
  record(check)(v); ensure(Object.keys(v as object).every((key) => allowed.includes(key)), "Atributo público não permitido");
};
const curvePoint = object({ bin: count, count, mean_probability: rate, default_rate: rate });
const curve = list(curvePoint, 1);
const calibrationCurve = object({ observations: count, brier_score: rate, strategy: literal("uniform"), bins_requested: count, curve });
const scores = object({ average_precision: rate, roc_auc: rate, brier_score: rate });
const distribution = object({ observed: count, minimum: nullable(number), q25: nullable(number), median: nullable(number), q75: nullable(number),
  maximum: nullable(number), mean: nullable(number), std_sample: nullable(nonnegative), histogram: list(object({ lower: number, upper: number, count })) });
export const edaPayload = object({ target: object({ class_counts: object({ "0": count, "1": count }), default_rate: nullable(rate), minority_majority_ratio: nullable(rate), both_classes_present: bool }),
  missing: financialRecord(object({ count, rate: nullable(rate) }), [...amounts, ...pay]), distributions: financialRecord(distribution, amounts),
  patterns: financialRecord(list(object({ group: text, observations: count, defaults: count, default_rate: nullable(rate) })), [...pay, "LIMIT_BAL"]),
  correlations: list(object({ left: literal(...amounts, "defaulted"), right: literal(...amounts, "defaulted"), observations: count, pearson: nullable(signedRate), spearman: nullable(signedRate) })) });

// Public projection: configurations and split methods are sanitized descriptions,
// never unrestricted Python dictionaries containing private row positions.
const reference = object({ model_version: literal("uci-350-reference-v1"), seed: count, features: list(feature, 1), configuration: text,
  train_partition_id: identifier, train: object({ observations: count, prevalence: rate }),
  validation: object({ observations: count, prevalence: rate, scores: object({ logistic: scores, dummy: scores }), average_precision_difference: signedRate, logistic_above_dummy: bool }) });
const candidate = object({ candidate: identifier, family: literal("dummy", "logistic", "tree"), parameters: text,
  roc_auc: rate, average_precision: rate, precision: rate, recall: rate, predicted_positives: count, ap_minus_reference: signedRate, ap_minus_dummy: signedRate });
const comparison = object({ comparison_version: literal("credit-comparison-v1"), seed: count, validation_method: literal("stratified_client", "temporal"),
  train_partition_id: identifier, threshold: rate, positive_class: literal(1), zero_division: literal(0), train_observations: count, validation_observations: count,
  train_prevalence: rate, validation_prevalence: rate, table: list(candidate, 1), selected_candidate: identifier, selection_reason: text,
  tie_preference: list(identifier, 1), selected_above_reference: bool, selected_above_dummy: bool });
export const comparisonPayload = object({ reference: nullable(reference), comparison: nullable(comparison) });

const policyConfiguration = object({ threshold: rate, calibration_method: literal("identity", "sigmoid"), false_negative_cost: nonnegative,
  false_positive_cost: nonnegative, min_approval_rate: rate, min_default_recall: rate, slope: number, intercept: number });
const thresholdRow = object({ threshold: rate, observations: count, confusion_matrix: matrix, tn: count, fp: count, fn: count, tp: count,
  approved: count, approval_rate: rate, approved_default_rate: nullable(rate), default_recall: rate, total_cost: nonnegative, mean_cost: nonnegative, feasible: bool });
export const calibrationPayload = object({ version: literal("credit-calibration-v1"), development_version: text,
  calibration_partition_id: identifier, disjointness_verification: text, calibration_observations: count, selection_observations: count,
  minimum_brier_gain: nonnegative, observed_brier_gain: signedRate, before: calibrationCurve, sigmoid_candidate: calibrationCurve,
  calibration_selected: literal("identity", "sigmoid"), policy: policyConfiguration, threshold_table: list(thresholdRow, 1), selected: thresholdRow, tie_break: text });

const structuredRate = object({ numerator: count, denominator: count, value: nullable(rate), wilson_95: nullable(pair(rate)) });
const segmentMetrics = object({ average_precision: rate, roc_auc: rate, brier_score: rate, mean_probability: rate, confusion_matrix: matrix,
  false_positive_rate: structuredRate, false_negative_rate: structuredRate, default_recall: structuredRate, precision: structuredRate,
  approval_rate: structuredRate, approved_default_rate: structuredRate,
  calibration_curve: list(object({ bin: count, count, mean_probability: rate, observed: structuredRate }), 1) });
const permutation = object({ version: literal("permutation-v1"), dataset_version: text, observations: count, baseline_average_precision: rate, repeats: count, seed: count,
  factors: list(object({ feature, mean_ap_decrease: signedRate, permutation_std: nonnegative, permutation_quantiles_025_975: pair(signedRate) }), 1) });
const segments = object({ version: literal("segments-v1"), dataset_version: text, threshold: rate, minimum_size: count, minimum_class_count: count, bins: count,
  overall: segmentMetrics, segments: list(object({ segment: text, observations: count, defaults: count, non_defaults: count, sufficient: bool,
    metrics: nullable(segmentMetrics), differences_from_overall: nullable(object({ average_precision: signedRate, roc_auc: signedRate, brier_score: signedRate })), reason: nullable(text) })) });
export const interpretationPayload = object({ permutation: nullable(permutation), segments: nullable(segments) });

const finalMetrics = object({ observations: count, prevalence: rate, average_precision: rate, baseline_average_precision: rate, average_precision_difference: signedRate,
  roc_auc: rate, baseline_roc_auc: rate, brier_score: rate, baseline_brier_score: rate, precision: nullable(rate), recall: rate, f1: nullable(rate),
  confusion_matrix: matrix, approval_rate: rate, approved_default_rate: nullable(rate) });
const interval = object({ valid_resamples: count, lower: nullable(signedRate), upper: nullable(signedRate) });
const intervalNames = ["average_precision", "baseline_average_precision", "average_precision_difference", "roc_auc", "brier_score", "approval_rate", "approved_default_rate", "precision", "recall", "f1"];
export const finalPayload = object({ version: literal("final-evaluation-v1"), threshold: rate, metrics: finalMetrics, calibration_curve: curve, above_baseline_descriptive: bool,
  frozen: object({ dataset_sha256: hash, partition_sha256: hash, model_sha256: hash, policy_sha256: hash, code_revision: revision,
    environment: record(text), frozen_at_utc: utc, restricted_manifest_sha256: hash, alignment_verification: text, calibration_once_verification: text, reserved_test_verification: text }),
  uncertainty: object({ method: literal("bootstrap pareado por observação, percentil pontual de 95%"), seed: count, requested_resamples: count,
    single_class_resamples_skipped: count, intervals: financialRecord(interval, intervalNames) }) });

const simulationRow = object({ scenario: text, threshold: rate, observations: count, approved: count, rejected: count, approval_rate: rate, approved_defaults: count,
  approved_default_rate: nullable(rate), rejected_defaults: count, default_recall: rate, approved_exposure: nonnegative, expected_loss: nonnegative,
  expected_revenue: nonnegative, expected_margin_before_costs: number, historical_scenario_loss: nonnegative, historical_scenario_revenue: nonnegative,
  historical_scenario_margin_before_costs: number });
const grid = object({ exposure_mode: literal("constant"), observations: count, defaults: count, probability_stage: literal("raw", "calibrated"),
  rows: list(object({ threshold: rate, approved: count, approved_defaults: count, approved_probability_sum: nonnegative }), 3), parity_verification: text });
export const simulationPayload = object({ report: object({ simulation_version: literal("credit-policy-v1"), dataset_version: text, model_version: text,
  currency: text, horizon: text, exposure_assumption: text, thresholds: list(rate, 3),
  scenarios: list(object({ name: text, exposure_multiplier: nonnegative, lgd: rate, revenue_rate: nonnegative }), 1), observations: count, defaults: count,
  rows: list(simulationRow, 3), limitations: texts }), interactive_grid: nullable(grid) });

const payloads = { eda: edaPayload, comparison: comparisonPayload, calibration: calibrationPayload, interpretation: interpretationPayload, final_evaluation: finalPayload, simulation: simulationPayload };
type Payloads = { [K in keyof typeof payloads]: Infer<(typeof payloads)[K]> };
type Envelope = {
  schema_version: typeof schemaVersion; release_id: string; result_id: string; dataset_id: string; partition_id: string;
  model_id: string | null; policy_id: string | null; origin: "synthetic" | "real"; source_contract: string; observations: number; metric_notes: Record<string, string>; limitations: string[];
};
export type AnalysisResult = { [K in keyof Payloads]: Envelope & { kind: K; payload: Payloads[K] } }[keyof Payloads];
const sourceContracts = {
  eda: ["analysis.eda.analyze@uci-350-eda-v1"], comparison: ["modeling.reference.train_reference@uci-350-reference-v1", "modeling.comparison.compare_models@credit-comparison-v1"],
  calibration: ["modeling.calibration.select_policy@credit-calibration-v1"], interpretation: ["modeling.interpretation.permutation_report@permutation-v1", "modeling.interpretation.segment_report@segments-v1"],
  final_evaluation: ["modeling.final_evaluation.evaluate_once@final-evaluation-v1"], simulation: ["simulation.policies.simulate_policies@credit-policy-v1"],
};
export function close(actual: number, expected: number) { ensure(Math.abs(actual - expected) <= numericTolerance * Math.max(1, Math.abs(expected)), "Valor calculado inconsistente"); }
function fraction(value: number | null, numerator: number, denominator: number) {
  ensure(numerator <= denominator, "Numerador excede denominador");
  if (!denominator) ensure(value === null, "Denominador zero exige nulo");
  else { ensure(value !== null, "Taxa ausente"); close(value, numerator / denominator); }
}
function unique(values: (string | number)[]) { ensure(new Set(values).size === values.length, "Valores duplicados"); }
function checkMatrix(m: [[number, number], [number, number]], n: number, defaults?: number) {
  ensure(m.flat().reduce((a, b) => a + b, 0) === n, "Matriz não soma denominador");
  if (defaults !== undefined) ensure(m[1][0] + m[1][1] === defaults, "Matriz diverge das classes");
}
function checkCurve(points: Infer<typeof curve>, n: number, bins: number) {
  unique(points.map((p) => p.bin));
  ensure(points.reduce((sum, p) => sum + p.count, 0) === n, "Bins não somam denominador");
  for (const p of points) ensure(p.count > 0 && p.bin < bins && p.mean_probability >= p.bin / bins - numericTolerance && p.mean_probability <= (p.bin + 1) / bins + numericTolerance, "Bin inválido");
}
function noteNulls(value: unknown, notes: Record<string, string>, current = "payload") {
  if (value === null) { ensure(Object.hasOwn(notes, current), `Nulo sem motivo: ${current}`); return; }
  if (value && typeof value === "object") for (const [key, child] of Object.entries(value)) if (key !== "reason") noteNulls(child, notes, `${current}.${key}`);
}
export function validateAnalysis(value: unknown, manifest: Manifest, dataset: Dataset, partition: Partition): AnalysisResult {
  ensure(value && typeof value === "object", "Envelope obrigatório");
  const kind = (value as { kind?: string }).kind;
  ensure(kind && Object.hasOwn(payloads, kind), "Tipo não suportado");
  const k = kind as keyof Payloads;
  object({ schema_version: literal(schemaVersion), release_id: identifier, result_id: identifier, kind: literal(k), dataset_id: identifier, partition_id: identifier,
    model_id: nullable(identifier), policy_id: nullable(identifier), origin: literal("real", "synthetic"), source_contract: literal(...sourceContracts[k]), observations: count,
    payload: payloads[k], metric_notes: record(text), limitations: texts })(value);
  const r = value as AnalysisResult;
  ensure(r.observations === partition.observations && r.origin === dataset.origin, "Origem/denominador incompatível");
  noteNulls(r.payload, r.metric_notes);
  const n = r.observations; const defaults = partition.class_counts["1"];
  const model = manifest.models.find((m) => m.model_id === r.model_id);
  const policy = manifest.policies.find((p) => p.policy_id === r.policy_id);
  if (r.kind !== "eda") ensure(model, "Resultado exige modelo rastreável");
  if (["calibration", "final_evaluation", "simulation"].includes(r.kind)) ensure(policy, "Resultado exige política rastreável");
  if (r.kind === "eda") {
    const p = r.payload;
    ensure(p.target.class_counts["1"] === defaults && p.target.class_counts["0"] === partition.class_counts["0"], "Alvo diverge da partição");
    fraction(p.target.default_rate, defaults, n);
    fraction(p.target.minority_majority_ratio, Math.min(defaults, n - defaults), Math.max(defaults, n - defaults));
    ensure(p.target.both_classes_present === (defaults > 0 && defaults < n), "Presença de classes inconsistente");
    ensure(Object.keys(p.missing).length === 19 && Object.keys(p.distributions).length === 13 && Object.keys(p.patterns).length === 7, "Projeção EDA incompleta");
    for (const [name, missing] of Object.entries(p.missing)) {
      fraction(missing.rate, missing.count, n);
      const d = p.distributions[name]; if (!d) continue;
      ensure(d.observed + missing.count === n && d.histogram.reduce((sum, b) => sum + b.count, 0) === d.observed, "Histograma/ausências inconsistentes");
      ensure(d.histogram.length === (d.observed ? 10 : 0), "Histograma exige dez bins");
      const order = [d.minimum, d.q25, d.median, d.q75, d.maximum];
      if (d.observed) { ensure(order.every((v) => v !== null) && d.mean !== null, "Resumo ausente"); ensure(order.every((v, i) => !i || v! >= order[i - 1]!), "Quantis fora de ordem"); }
      else ensure(order.every((v) => v === null) && d.mean === null && d.std_sample === null, "Resumo de população vazia");
      ensure(d.observed >= 2 ? d.std_sample !== null : d.std_sample === null, "Desvio amostral incompatível");
      d.histogram.forEach((b, i) => { ensure(b.lower < b.upper, "Bin invertido"); if (i) close(b.lower, d.histogram[i - 1].upper); });
    }
    for (const rows of Object.values(p.patterns)) { unique(rows.map((g) => g.group)); ensure(rows.reduce((s, g) => s + g.observations, 0) === n && rows.reduce((s, g) => s + g.defaults, 0) === defaults, "Grupos não cobrem população"); rows.forEach((g) => fraction(g.default_rate, g.defaults, g.observations)); }
    unique(p.correlations.map((c) => [c.left, c.right].sort().join(":")));
    for (const c of p.correlations) ensure(c.left !== c.right && c.observations <= n && (c.observations >= 3 || c.pearson === null && c.spearman === null), "Correlação sem suporte");
  } else if (r.kind === "comparison") {
    ensure(partition.role === "validation", "Comparação exige validação");
    const p = r.payload; ensure(p.reference || p.comparison, "Comparação vazia");
    ensure(r.source_contract.includes("train_reference") ? p.reference : p.comparison, "Produtor não corresponde ao relatório");
    for (const report of [p.reference, p.comparison]) if (report) {
      const train = dataset.partitions.find((part) => part.partition_id === report.train_partition_id);
      ensure(train?.role === "train", "Treino não encontrado");
      const trainN = "train" in report ? report.train.observations : report.train_observations;
      const validationN = "validation" in report ? report.validation.observations : report.validation_observations;
      ensure(trainN === train.observations && validationN === n, "Volumes da comparação incompatíveis");
      close("train" in report ? report.train.prevalence : report.train_prevalence, train.class_counts["1"] / trainN);
      close("validation" in report ? report.validation.prevalence : report.validation_prevalence, defaults / n);
    }
    if (p.reference) { const v = p.reference.validation; close(v.average_precision_difference, v.scores.logistic.average_precision - v.scores.dummy.average_precision); ensure(v.logistic_above_dummy === (v.average_precision_difference > 0), "Conclusão inconsistente"); }
    if (p.comparison) {
      const c = p.comparison; unique(c.table.map((row) => row.candidate)); unique(c.tie_preference);
      const reference = c.table.find((row) => row.candidate === "logistic_c1"); const dummy = c.table.find((row) => row.candidate === "dummy");
      ensure(reference && dummy && c.table.length === 7 && c.tie_preference.length === 7 && c.table.every((row) => c.tie_preference.includes(row.candidate)), "Candidatos incompletos");
      for (const [i, row] of c.table.entries()) { ensure(row.predicted_positives <= n, "Positivos excedem denominador"); if (!row.predicted_positives) ensure(row.precision === 0 && Object.hasOwn(r.metric_notes, `payload.comparison.table.${i}.precision`), "Convenção zero_division sem nota"); close(row.ap_minus_reference, row.average_precision - reference.average_precision); close(row.ap_minus_dummy, row.average_precision - dummy.average_precision); }
      const selected = [...c.table].sort((a, b) => b.average_precision - a.average_precision || c.tie_preference.indexOf(a.candidate) - c.tie_preference.indexOf(b.candidate))[0];
      ensure(selected.candidate === c.selected_candidate && c.selected_above_reference === (selected.average_precision > reference.average_precision) && c.selected_above_dummy === (selected.average_precision > dummy.average_precision), "Seleção inconsistente");
    }
  } else if (r.kind === "calibration") {
    ensure(partition.role === "selection", "Calibração exige seleção");
    const p = r.payload; const calibration = dataset.partitions.find((part) => part.partition_id === p.calibration_partition_id);
    ensure(calibration?.role === "calibration" && calibration.partition_id !== partition.partition_id && calibration.observations === p.calibration_observations && p.selection_observations === n, "Partições de calibração incompatíveis");
    for (const c of [p.before, p.sigmoid_candidate]) { ensure(c.observations === n && c.bins_requested > 0, "Curva de outra população"); checkCurve(c.curve, n, c.bins_requested); }
    close(p.observed_brier_gain, p.before.brier_score - p.sigmoid_candidate.brier_score);
    ensure(p.calibration_selected === (p.observed_brier_gain > p.minimum_brier_gain ? "sigmoid" : "identity") && p.policy.calibration_method === p.calibration_selected && model?.calibration_method === p.calibration_selected, "Calibrador incompatível");
    unique(p.threshold_table.map((row) => row.threshold));
    for (const row of p.threshold_table) { checkMatrix(row.confusion_matrix, n, defaults); ensure(row.observations === n && row.tn === row.confusion_matrix[0][0] && row.fp === row.confusion_matrix[0][1] && row.fn === row.confusion_matrix[1][0] && row.tp === row.confusion_matrix[1][1] && row.approved === row.tn + row.fn, "Contagens de política incompatíveis"); fraction(row.approval_rate, row.approved, n); fraction(row.approved_default_rate, row.fn, row.approved); fraction(row.default_recall, row.tp, defaults); close(row.mean_cost, row.total_cost / n); close(row.total_cost, row.fn * p.policy.false_negative_cost + row.fp * p.policy.false_positive_cost); ensure(row.feasible === (row.approval_rate >= p.policy.min_approval_rate && row.default_recall >= p.policy.min_default_recall), "Viabilidade inconsistente"); }
    const best = p.threshold_table.filter((row) => row.feasible).sort((a, b) => a.total_cost - b.total_cost || a.threshold - b.threshold)[0];
    ensure(best && Object.entries(best).every(([key, value]) => JSON.stringify(value) === JSON.stringify(p.selected[key as keyof typeof best])) && p.policy.threshold === best.threshold && policy?.threshold === best.threshold, "Limiar selecionado incompatível");
  } else if (r.kind === "interpretation") {
    const p = r.payload; ensure(p.permutation || p.segments, "Interpretação vazia");
    ensure(r.source_contract.includes("permutation_report") ? p.permutation : p.segments, "Produtor não corresponde ao relatório");
    if (p.permutation) { const v = p.permutation; ensure(v.dataset_version === dataset.dataset_version && v.observations === n && v.repeats >= 2 && v.seed < 2 ** 32, "Permutação incompatível"); unique(v.factors.map((f) => f.feature)); v.factors.forEach((f) => ensure(f.permutation_quantiles_025_975[0] <= f.permutation_quantiles_025_975[1], "Quantis invertidos")); }
    if (p.segments) {
      const v = p.segments; ensure(v.dataset_version === dataset.dataset_version && v.minimum_size >= 2 && v.minimum_class_count >= 1 && v.bins >= 1 && v.bins <= 100, "Critérios inválidos");
      checkSegmentMetrics(v.overall, n, defaults, v.bins); unique(v.segments.map((s) => s.segment));
      ensure(v.segments.reduce((s, g) => s + g.observations, 0) === n && v.segments.reduce((s, g) => s + g.defaults, 0) === defaults, "Segmentos não cobrem população");
      for (const s of v.segments) { ensure(s.defaults + s.non_defaults === s.observations && s.sufficient === (s.observations >= v.minimum_size && Math.min(s.defaults, s.non_defaults) >= v.minimum_class_count), "Suficiência inconsistente");
        if (s.sufficient) { ensure(s.metrics && s.differences_from_overall && s.reason === null, "Métricas de segmento ausentes"); checkSegmentMetrics(s.metrics, s.observations, s.defaults, v.bins); for (const key of ["average_precision", "roc_auc", "brier_score"] as const) close(s.differences_from_overall[key], s.metrics[key] - v.overall[key]); }
        else ensure(s.metrics === null && s.differences_from_overall === null && s.reason, "Segmento insuficiente com métricas");
      }
    }
  } else if (r.kind === "final_evaluation") {
    ensure(partition.role === "test", "Avaliação final exige teste reservado");
    const p = r.payload; const m = p.metrics; const f = p.frozen; const u = p.uncertainty;
    ensure(m.observations === n && f.partition_sha256 === partition.partition_sha256 && f.model_sha256 === model?.model_sha256 && f.policy_sha256 === policy?.policy_sha256 && p.threshold === policy?.threshold && f.frozen_at_utc === policy?.frozen_at_utc && dataset.source_hashes.some((h) => h.sha256 === f.dataset_sha256), "Congelamento incompatível");
    checkMatrix(m.confusion_matrix, n, defaults); const [[tn, fp], [fn, tp]] = m.confusion_matrix;
    fraction(m.prevalence, defaults, n); fraction(m.precision, tp, tp + fp); fraction(m.recall, tp, defaults); fraction(m.f1, 2 * tp, 2 * tp + fp + fn); fraction(m.approval_rate, tn + fn, n); fraction(m.approved_default_rate, fn, tn + fn);
    close(m.average_precision_difference, m.average_precision - m.baseline_average_precision); ensure(p.above_baseline_descriptive === (m.average_precision_difference > 0), "Conclusão final inconsistente"); checkCurve(p.calibration_curve, n, 10);
    ensure(u.requested_resamples >= 100 && u.requested_resamples <= 10000 && u.single_class_resamples_skipped <= u.requested_resamples && Object.keys(u.intervals).length === intervalNames.length, "Bootstrap inválido");
    for (const [key, interval] of Object.entries(u.intervals)) { ensure(interval.valid_resamples <= u.requested_resamples - u.single_class_resamples_skipped, "Denominador bootstrap inválido"); if (interval.valid_resamples) ensure(interval.lower !== null && interval.upper !== null && interval.lower <= interval.upper && (key === "average_precision_difference" || interval.lower >= 0), "Intervalo inválido"); else ensure(interval.lower === null && interval.upper === null, "Intervalo sem reamostragens"); }
  } else if (r.kind === "simulation") {
    const p = r.payload; const report = p.report;
    ensure(report.observations === n && report.defaults === defaults && report.dataset_version === dataset.dataset_version && report.model_version === model?.model_version, "Simulação de outra população/modelo");
    unique(report.thresholds); ensure(report.thresholds.every((t, i) => !i || t > report.thresholds[i - 1]), "Limiares desordenados"); unique(report.scenarios.map((s) => s.name)); unique(report.rows.map((row) => `${row.scenario}:${row.threshold}`));
    ensure(report.rows.length === report.thresholds.length * report.scenarios.length, "Grade de cenários incompleta");
    for (const row of report.rows) { ensure(report.thresholds.includes(row.threshold) && report.scenarios.some((s) => s.name === row.scenario) && row.observations === n && row.approved + row.rejected === n && row.approved_defaults + row.rejected_defaults === defaults && row.approved_defaults <= row.approved && row.rejected_defaults <= row.rejected, "Contagens da simulação inválidas"); fraction(row.approval_rate, row.approved, n); fraction(row.approved_default_rate, row.approved_defaults, row.approved); fraction(row.default_recall, row.rejected_defaults, defaults); close(row.expected_margin_before_costs, row.expected_revenue - row.expected_loss); close(row.historical_scenario_margin_before_costs, row.historical_scenario_revenue - row.historical_scenario_loss);
      if (row.threshold === 0) ensure(row.approved === 0, "Limiar zero não aprova");
      if (!row.approved) ensure([row.approved_exposure, row.expected_loss, row.expected_revenue, row.historical_scenario_loss, row.historical_scenario_revenue].every((v) => v === 0), "Montantes sem aprovados");
    }
    for (const scenario of report.scenarios) {
      const rows = report.rows.filter((row) => row.scenario === scenario.name).sort((a, b) => a.threshold - b.threshold);
      for (const [i, row] of rows.entries()) if (i) ensure(row.approved >= rows[i - 1].approved && row.approved_defaults >= rows[i - 1].approved_defaults, "Aprovações não monotônicas");
    }
    if (p.interactive_grid) { const g = p.interactive_grid; ensure(g.observations === n && g.defaults === defaults && g.probability_stage === (model?.calibration_method === "sigmoid" ? "calibrated" : "raw"), "Grade incompatível"); unique(g.rows.map((row) => row.threshold)); for (const [i, row] of g.rows.entries()) { ensure(report.thresholds.includes(row.threshold) && row.approved <= n && row.approved_defaults <= Math.min(defaults, row.approved) && defaults - row.approved_defaults <= n - row.approved && row.approved_probability_sum <= row.approved, "Grade inválida"); ensure(report.rows.filter((r) => r.threshold === row.threshold).every((r) => r.approved === row.approved && r.approved_defaults === row.approved_defaults), "Grade diverge do relatório"); if (i) { const previous = g.rows[i - 1]; ensure(row.threshold > previous.threshold && row.approved >= previous.approved && row.approved_defaults >= previous.approved_defaults && row.approved_probability_sum >= previous.approved_probability_sum, "Grade não monotônica"); } } }
  }
  return r;
}

function checkSegmentMetrics(m: Infer<typeof segmentMetrics>, n: number, defaults: number, bins: number) {
  checkMatrix(m.confusion_matrix, n, defaults); const [[tn, fp], [fn, tp]] = m.confusion_matrix;
  const expected = { false_positive_rate: [fp, tn + fp], false_negative_rate: [fn, defaults], default_recall: [tp, defaults], precision: [tp, tp + fp], approval_rate: [tn + fn, n], approved_default_rate: [fn, tn + fn] };
  for (const [key, [numerator, denominator]] of Object.entries(expected)) {
    const r = m[key as keyof typeof expected]; ensure(r.numerator === numerator && r.denominator === denominator, "Taxa estruturada incompatível"); fraction(r.value, numerator, denominator);
    if (denominator) { ensure(r.wilson_95, "Wilson ausente"); const z = 1.959963984540054; const p = numerator / denominator; const d = 1 + z * z / denominator; const center = (p + z * z / (2 * denominator)) / d; const radius = z * Math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator ** 2)) / d; close(r.wilson_95[0], Math.max(0, center - radius)); close(r.wilson_95[1], Math.min(1, center + radius)); }
    else ensure(r.wilson_95 === null, "Wilson sem denominador");
  }
  checkCurve(m.calibration_curve.map((p) => ({ ...p, default_rate: p.observed.value ?? 0 })), n, bins);
  for (const p of m.calibration_curve) { ensure(p.observed.denominator === p.count, "Denominador do bin inválido"); fraction(p.observed.value, p.observed.numerator, p.count); }
}
