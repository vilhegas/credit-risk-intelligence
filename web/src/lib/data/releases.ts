import { createHash } from "node:crypto";
import { lstat, readdir, readFile, realpath } from "node:fs/promises";
import path from "node:path";
import type { LoadedRelease, LoadedResult } from "../../types/results.ts";
import { parseStrictJson } from "../schemas/strict-json.ts";
import { requireCondition, validateManifest, validateOverview } from "../schemas/results.ts";
import { validateAnalysis } from "../schemas/analysis.ts";

export const releasesDirectory = path.join(process.cwd(), "src/data/releases");
const maxArtifactBytes = 10 * 1024 * 1024;

async function readArtifact(directory: string, filename: string): Promise<Buffer> {
  const target = path.join(directory, filename);
  const stat = await lstat(target);
  requireCondition(stat.isFile() && !stat.isSymbolicLink(), `Artefato não regular: ${filename}`);
  requireCondition(stat.size <= maxArtifactBytes, `Artefato excede 10 MiB: ${filename}`);
  const resolved = await realpath(target);
  requireCondition(path.dirname(resolved) === await realpath(directory), "Artefato fora da release");
  return readFile(target);
}

/** Verifies artifacts for review, including pending candidates. Does not authorize display. */
export async function validateReleaseArtifacts(releaseId: string, root = releasesDirectory) {
  requireCondition(/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(releaseId), "Identificador de release inválido");
  const directory = path.join(root, releaseId);
  requireCondition(!(await lstat(directory)).isSymbolicLink(), "Release não pode ser link simbólico");
  const manifest = validateManifest(parseStrictJson(await readArtifact(directory, "manifest.json")), { allowPendingReview: true });
  requireCondition(manifest.release_id === releaseId, "Release diverge do diretório");
  const expected = new Set(["manifest.json", ...manifest.results.flatMap((r) => r.path ? [r.path] : [])]);
  const files = await readdir(directory);
  requireCondition(files.every((file) => expected.has(file)) && files.length === expected.size, "Arquivos ausentes ou não catalogados");
  const results: Record<string, LoadedResult> = Object.create(null);
  for (const entry of manifest.results) {
    if (entry.availability === "unavailable") {
      results[entry.result_id] = { status: "unavailable", kind: entry.kind, reason: entry.reason };
      continue;
    }
    const bytes = await readArtifact(directory, entry.path);
    requireCondition(bytes.length === entry.bytes, `Tamanho divergente: ${entry.result_id}`);
    requireCondition(createHash("sha256").update(bytes).digest("hex") === entry.sha256, `Hash divergente: ${entry.result_id}`);
    const dataset = manifest.datasets.find((d) => d.dataset_id === entry.dataset_id)!;
    const partition = dataset.partitions.find((p) => p.partition_id === entry.partition_id)!;
    const decoded = parseStrictJson(bytes);
    const result = entry.kind === "overview" ? validateOverview(decoded) : validateAnalysis(decoded, manifest, dataset, partition);
    for (const key of ["result_id", "kind", "dataset_id", "partition_id", "model_id", "policy_id"] as const) {
      requireCondition(result[key] === entry[key], `Envelope diverge do catálogo: ${key}`);
    }
    requireCondition(result.release_id === manifest.release_id, "Envelope de outra release");
    requireCondition(result.origin === dataset.origin, "Origem diverge dos dados");
    requireCondition(result.observations === partition.observations, "Denominador diverge da partição");
    if (result.kind === "overview") requireCondition(result.payload.defaults === partition.class_counts["1"] && result.payload.non_defaults === partition.class_counts["0"], "Classes divergem da partição");
    results[entry.result_id] = { status: dataset.origin === "real" ? "real_verified" : "synthetic", result, dataset, partition };
  }
  return { manifest, results };
}

/** Server/build only. Pending candidates never expose their results to a page. */
export async function loadRelease(releaseId?: string, root = releasesDirectory): Promise<LoadedRelease> {
  if (releaseId === undefined) return { status: "unavailable", reason: "Nenhuma release de resultados foi selecionada e verificada." };
  const verified = await validateReleaseArtifacts(releaseId, root);
  if (verified.manifest.publication_review.decision !== "approved" || !verified.manifest.producer.working_tree_clean) {
    return { status: "unavailable", reason: "Pacote candidato aguardando revisão e procedência de uma árvore Git limpa." };
  }
  return { status: "available", ...verified };
}

/** Validate every release, including releases not yet selected by a page. */
export async function validateAllReleases(root = releasesDirectory): Promise<number> {
  const entries = await readdir(root, { withFileTypes: true });
  let count = 0;
  for (const entry of entries) {
    if (entry.name === ".gitkeep" && entry.isFile()) continue;
    requireCondition(entry.isDirectory() && !entry.isSymbolicLink(), "Entrada inesperada no diretório de releases");
    await loadRelease(entry.name, root);
    count++;
  }
  return count;
}
