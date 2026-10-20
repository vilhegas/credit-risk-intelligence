import assert from "node:assert/strict";
import { readdir } from "node:fs/promises";
import test from "node:test";
import { loadRelease, releasesDirectory, validateReleaseArtifacts } from "../src/lib/data/releases.ts";
import { verifyExportParity } from "../scripts/verify-export-parity.ts";

test("pacotes exportados: integridade, origem sintética, paridade e revisão pendente", async () => {
  for (const entry of await readdir(releasesDirectory, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const release = await validateReleaseArtifacts(entry.name);
    if (release.manifest.producer.exporter_version !== "web-synthetic-export-v1") continue;
    verifyExportParity(release);
    assert.ok(release.manifest.datasets.every((d) => d.origin === "synthetic"));
    for (const result of release.manifest.results.filter((r) => r.result_id.startsWith("real-"))) {
      assert.equal(result.availability, "unavailable");
      assert.equal(result.path, null);
    }
    if (release.manifest.publication_review.decision === "pending") {
      const loaded = await loadRelease(entry.name);
      assert.equal(loaded.status, "unavailable");
      assert.equal("results" in loaded, false);
    }
    const altered = structuredClone(release);
    const simulation = Object.values(altered.results).find((r) => r.status !== "unavailable" && r.result.kind === "simulation");
    if (simulation?.status !== "unavailable" && simulation?.result.kind === "simulation") {
      simulation.result.payload.report.rows[0].expected_revenue = 123;
      assert.throws(() => verifyExportParity(altered));
    }
  }
});
