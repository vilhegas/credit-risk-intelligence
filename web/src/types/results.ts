export const schemaVersion = "credit-risk-web-v1" as const;
export const kinds = ["overview", "eda", "comparison", "calibration", "interpretation", "final_evaluation", "simulation"] as const;
export const financialFeatures = ["LIMIT_BAL", "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
  ...Array.from({ length: 6 }, (_, i) => `BILL_AMT${i + 1}`), ...Array.from({ length: 6 }, (_, i) => `PAY_AMT${i + 1}`)];
export type ResultKind = (typeof kinds)[number];
export type Origin = "synthetic" | "real";
export type { AnalysisResult } from "../lib/schemas/analysis.ts";
export type PublicResult = OverviewResult | import("../lib/schemas/analysis.ts").AnalysisResult;
export type Partition = {
  partition_id: string;
  role: "full" | "train" | "validation" | "calibration" | "selection" | "test";
  observations: number;
  class_counts: { "0": number; "1": number };
  method: string;
  partition_sha256: string;
  used_for: string[];
};
export type Dataset = {
  dataset_id: string; dataset_version: string;
  obtained_at_utc: string | null;
  source_hashes: { role: string; sha256: string }[];
  population: string; observation_unit: string;
  reference_period: string | null; horizon: string; currency: string | null;
  target: { name: string; positive_class: 1; meaning: string; availability_assumption: string };
  quality: { input_rows: number; accepted_rows: number; rejected_rows: number; treatment_version: string; report_reference: string } | null;
  partitions: Partition[]; limitations: string[];
} & ({ origin: "synthetic";
  source: { generator: string; seed: number; configuration: string; representation: string };
  license: { generation: string; publication_conditions: string };
} | { origin: "real";
  source: { title: string; publisher: string; reference: string; url: string };
  license: { attribution: string; url: string; checked_at_utc: string };
});
export type Model = {
  model_id: string; dataset_id: string; model_version: string; family: string;
  features: string[]; configuration: string; partition_sha256: string;
  model_sha256: string; calibration_method: "identity" | "sigmoid";
};
export type Policy = {
  policy_id: string; model_id: string; policy_sha256: string;
  threshold: number; configuration: string; frozen_at_utc: string;
};
export type CatalogEntry = {
  result_id: string; kind: ResultKind;
  dataset_id: string | null; partition_id: string | null;
  model_id: string | null; policy_id: string | null;
} & ({ availability: "unavailable"; reason: string; path: null; sha256: null; bytes: null } |
  { availability: "available"; reason: null; path: string; sha256: string; bytes: number });
export type Manifest = {
  schema_version: typeof schemaVersion; release_id: string; generated_at_utc: string;
  producer: { code_revision: string; working_tree_clean: true; exporter_version: string; environment: Record<string, string> };
  datasets: Dataset[]; models: Model[]; policies: Policy[]; results: CatalogEntry[];
  validation: { command: string; revision: string; exit_code: number; summary: string; skipped_tests: string[] }[];
  publication_review: { reviewed_at_utc: string; reviewer: string; scope: string; privacy_policy: string; decision: "approved" };
  limitations: string[];
};
export type OverviewResult = {
  schema_version: typeof schemaVersion; release_id: string; result_id: string; kind: "overview";
  dataset_id: string; partition_id: string; model_id: string | null; policy_id: string | null;
  origin: Origin; source_contract: string; observations: number;
  payload: { defaults: number; non_defaults: number; default_rate: number | null };
  metric_notes: Record<string, string>; limitations: string[];
};
export type LoadedResult =
  | { status: "unavailable"; kind: ResultKind; reason: string }
  | { status: "synthetic" | "real_verified"; result: PublicResult; dataset: Dataset; partition: Partition };
export type LoadedRelease = { status: "unavailable"; reason: string } |
  { status: "available"; manifest: Manifest; results: Record<string, LoadedResult> };
