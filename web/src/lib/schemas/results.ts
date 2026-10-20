import { financialFeatures, kinds, schemaVersion } from "../../types/results.ts";
import type { Dataset, Manifest, OverviewResult } from "../../types/results.ts";

export type Check<T = unknown> = ((value: unknown) => void) & { readonly __type?: T };
export type Infer<C> = C extends Check<infer T> ? T : never;
export function requireCondition(ok: unknown, message: string): asserts ok {
  if (!ok) throw new Error(message);
}
export const text: Check<string> = (v) => requireCondition(typeof v === "string" && v.trim().length > 0, "Texto obrigatório");
export const literal = <const T extends readonly unknown[]>(...values: T): Check<T[number]> => (v) => requireCondition(values.includes(v), `Literal incompatível: ${String(v)}`);
export const nullable = <T>(check: Check<T>): Check<T | null> => (v) => { if (v !== null) check(v); };
export const number: Check<number> = (v) => requireCondition(typeof v === "number" && Number.isFinite(v), "Número finito obrigatório");
export const count: Check<number> = (v) => { number(v); requireCondition(Number.isSafeInteger(v) && (v as number) >= 0, "Contagem inválida"); };
export const rate: Check<number> = (v) => { number(v); requireCondition((v as number) >= 0 && (v as number) <= 1, "Taxa fora de [0,1]"); };
const pattern = (regex: RegExp): Check<string> => (v) => { text(v); requireCondition(regex.test(v as string), "Formato inválido"); };
export const hash = pattern(/^[a-f0-9]{64}$/);
export const revision = pattern(/^[a-f0-9]{40}$/);
export const identifier = pattern(/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/);
export const utc: Check<string> = (v) => {
  text(v);
  requireCondition(/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/.test(v as string), "Data UTC obrigatória");
  const date = new Date(v as string);
  const normalized = (v as string).includes(".") ? (v as string).replace(/\.(\d+)Z$/, (_, fraction: string) => `.${fraction.padEnd(3, "0")}Z`) : (v as string).replace(/Z$/, ".000Z");
  requireCondition(Number.isFinite(date.getTime()) && date.toISOString() === normalized, "Data UTC inválida");
};
export const list = <T>(check: Check<T>, minimum = 0): Check<T[]> => (v) => {
  requireCondition(Array.isArray(v) && v.length >= minimum, "Lista inválida");
  v.forEach(check);
};
export const texts = list(text, 1);
export const record = <T>(check: Check<T>): Check<Record<string, T>> => (v) => {
  requireCondition(v !== null && typeof v === "object" && !Array.isArray(v), "Objeto obrigatório");
  Object.values(v).forEach(check);
};
export const object = <S extends Record<string, Check>>(fields: S): Check<{ [K in keyof S]: Infer<S[K]> }> => (v) => {
  record(() => {})(v);
  const data = v as Record<string, unknown>;
  requireCondition(Object.keys(data).length === Object.keys(fields).length && Object.keys(data).every((key) => Object.hasOwn(fields, key)), "Campos ausentes ou desconhecidos");
  for (const [key, check] of Object.entries(fields)) {
    try { check(data[key]); } catch (error) { throw new Error(`${key}: ${(error as Error).message}`); }
  }
};
const quality = nullable(object({ input_rows: count, accepted_rows: count, rejected_rows: count, treatment_version: text, report_reference: text }));
const partition = object({ partition_id: identifier, role: literal("full", "train", "validation", "calibration", "selection", "test"), observations: count,
  class_counts: object({ "0": count, "1": count }), method: text, partition_sha256: hash, used_for: texts });
const publicUrl: Check<string> = (v) => {
  text(v); const url = new URL(v as string);
  requireCondition(url.protocol === "https:" && !url.username && !url.password && !["localhost", "127.0.0.1", "[::1]"].includes(url.hostname), "URL pública HTTPS obrigatória");
};
const realSource = object({ title: text, publisher: text, reference: text, url: publicUrl });
const syntheticSource = object({ generator: text, seed: count, configuration: text, representation: text });
const realLicense = object({ attribution: text, url: publicUrl, checked_at_utc: utc });
const syntheticLicense = object({ generation: text, publication_conditions: text });
const datasetFields = object({ dataset_id: identifier, dataset_version: text, origin: literal("real", "synthetic"), source: () => {}, license: () => {},
  obtained_at_utc: nullable(utc), source_hashes: list(object({ role: text, sha256: hash }), 1), population: text, observation_unit: text,
  reference_period: nullable(text), horizon: text, currency: nullable(text), target: object({ name: text, positive_class: literal(1), meaning: text, availability_assumption: text }),
  quality, partitions: list(partition, 1), limitations: texts });
const dataset: Check = (v) => {
  datasetFields(v); const d = v as Dataset;
  if (d.origin === "real") { realSource(d.source); realLicense(d.license); }
  else { syntheticSource(d.source); syntheticLicense(d.license); }
};
const model = object({ model_id: identifier, dataset_id: identifier, model_version: text, family: text, features: list(literal(...financialFeatures), 1), configuration: text,
  partition_sha256: hash, model_sha256: hash, calibration_method: literal("identity", "sigmoid") });
const policy = object({ policy_id: identifier, model_id: identifier, policy_sha256: hash, threshold: rate, configuration: text, frozen_at_utc: utc });
const entry = object({ result_id: identifier, kind: literal(...kinds), dataset_id: nullable(identifier), partition_id: nullable(identifier),
  model_id: nullable(identifier), policy_id: nullable(identifier), availability: literal("available", "unavailable"), reason: nullable(text),
  path: nullable(text), sha256: nullable(hash), bytes: nullable(count) });
const manifest = object({ schema_version: literal(schemaVersion), release_id: identifier, generated_at_utc: utc,
  producer: object({ code_revision: revision, working_tree_clean: literal(true), exporter_version: text, environment: record(text) }),
  datasets: list(dataset), models: list(model), policies: list(policy), results: list(entry),
  validation: list(object({ command: text, revision, exit_code: count, summary: text, skipped_tests: list(text) }), 1),
  publication_review: object({ reviewed_at_utc: utc, reviewer: text, scope: text, privacy_policy: text, decision: literal("approved") }), limitations: texts });

function unique(values: string[]) { requireCondition(new Set(values).size === values.length, "Identificadores duplicados"); }
export function validateManifest(value: unknown): Manifest {
  manifest(value);
  const m = value as Manifest;
  requireCondition(Object.keys(m.producer.environment).includes("python"), "Ambiente Python ausente");
  unique(m.datasets.map((d) => d.dataset_id)); unique(m.models.map((d) => d.model_id));
  unique(m.policies.map((d) => d.policy_id)); unique(m.results.map((d) => d.result_id));
  unique(m.results.filter((r) => r.path !== null).map((r) => r.path!));
  for (const d of m.datasets) {
    unique(d.partitions.map((p) => p.partition_id));
    unique(d.source_hashes.map((h) => h.role));
    requireCondition(d.origin === "real" ? d.obtained_at_utc !== null : d.obtained_at_utc === null, "Obtenção incompatível com origem");
    if (d.origin === "real") requireCondition(["zip", "xls"].every((role) => d.source_hashes.some((h) => h.role === role)), "Hashes da fonte real ausentes");
    if (d.quality) requireCondition(d.quality.input_rows === d.quality.accepted_rows + d.quality.rejected_rows, "Qualidade inconsistente");
    for (const p of d.partitions) requireCondition(p.class_counts["0"] + p.class_counts["1"] === p.observations, "Classes não somam o denominador");
  }
  for (const model of m.models) {
    unique(model.features);
    const d = m.datasets.find((d) => d.dataset_id === model.dataset_id);
    requireCondition(d?.partitions.some((p) => p.partition_sha256 === model.partition_sha256), "Modelo sem dados/partição compatível");
  }
  for (const p of m.policies) requireCondition(m.models.some((model) => model.model_id === p.model_id), "Política sem modelo");
  for (const r of m.results) {
    const d = m.datasets.find((d) => d.dataset_id === r.dataset_id);
    const model = m.models.find((model) => model.model_id === r.model_id);
    const p = m.policies.find((p) => p.policy_id === r.policy_id);
    requireCondition(r.dataset_id === null || d, "Dataset não encontrado");
    requireCondition(r.partition_id === null || d?.partitions.some((part) => part.partition_id === r.partition_id), "Partição não encontrada");
    requireCondition(r.model_id === null || (model && model.dataset_id === r.dataset_id), "Modelo incompatível");
    requireCondition(r.policy_id === null || (p && p.model_id === r.model_id), "Política incompatível");
    if (r.availability === "unavailable") requireCondition(r.reason && r.path === null && r.sha256 === null && r.bytes === null, "Indisponibilidade malformada");
    else {
      requireCondition(d && r.partition_id && r.reason === null && r.sha256 && r.bytes > 0, "Disponibilidade sem evidência");
      requireCondition(r.path === `${r.kind.replaceAll("_", "-")}.json`, "Caminho não permitido");
    }
  }
  return m;
}

export const numericTolerance = 1e-10;
export function validateOverview(value: unknown): OverviewResult {
  object({ schema_version: literal(schemaVersion), release_id: identifier, result_id: identifier, kind: literal("overview"), dataset_id: identifier,
    partition_id: identifier, model_id: nullable(identifier), policy_id: nullable(identifier), origin: literal("real", "synthetic"), source_contract: text,
    observations: count, payload: object({ defaults: count, non_defaults: count, default_rate: nullable(rate) }), metric_notes: record(text), limitations: texts })(value);
  const r = value as OverviewResult;
  const p = r.payload;
  requireCondition(p.defaults + p.non_defaults === r.observations, "Contagens não somam observações");
  requireCondition(r.observations === 0 ? p.default_rate === null && Object.hasOwn(r.metric_notes, "payload.default_rate") :
    p.default_rate !== null && Math.abs(p.default_rate - p.defaults / r.observations) <= numericTolerance, "Taxa/denominador inconsistente");
  requireCondition(["demo.indicators@demo-synthetic-v1", "analysis.eda.analyze@uci-350-eda-v1"].includes(r.source_contract), "Produtor de overview não suportado");
  if (r.source_contract.startsWith("demo.")) requireCondition(r.origin === "synthetic", "Demonstração não pode ser real");
  return r;
}
