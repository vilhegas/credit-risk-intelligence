import assert from "node:assert/strict";
import type { validateReleaseArtifacts } from "../src/lib/data/releases.ts";

/** Evidence check only; does not implement a dashboard or choose a policy. */
export function verifyExportParity(release: Awaited<ReturnType<typeof validateReleaseArtifacts>>) {
  const close = (actual: number, expected: number) => assert.ok(Math.abs(actual - expected) <= 1e-10 * Math.max(1, Math.abs(expected)));
  for (const loaded of Object.values(release.results)) {
    if (loaded.status === "unavailable" || loaded.result.kind !== "simulation") continue;
    assert.equal(loaded.result.origin, "synthetic");
    const { report, interactive_grid: grid } = loaded.result.payload;
    assert.ok(grid);
    const policy = release.manifest.policies.find((p) => p.policy_id === loaded.result.policy_id);
    assert.ok(policy);
    const configuration = JSON.parse(policy.configuration) as { simulation?: { exposure?: unknown } };
    const exposure = configuration.simulation?.exposure;
    assert.ok(typeof exposure === "number" && Number.isFinite(exposure) && exposure >= 0);
    assert.equal(grid.rows.length, report.thresholds.length);
    for (const row of report.rows) {
      const aggregate = grid.rows.find((g) => g.threshold === row.threshold);
      const scenario = report.scenarios.find((s) => s.name === row.scenario);
      assert.ok(aggregate && scenario);
      const ead = exposure * scenario.exposure_multiplier;
      close(row.approved_exposure, aggregate.approved * ead);
      close(row.expected_loss, aggregate.approved_probability_sum * ead * scenario.lgd);
      close(row.expected_revenue, (aggregate.approved - aggregate.approved_probability_sum) * ead * scenario.revenue_rate);
      close(row.historical_scenario_loss, aggregate.approved_defaults * ead * scenario.lgd);
      close(row.historical_scenario_revenue, (aggregate.approved - aggregate.approved_defaults) * ead * scenario.revenue_rate);
    }
  }
}
