import { validateReleaseArtifacts } from "../src/lib/data/releases.ts";
import { verifyExportParity } from "./verify-export-parity.ts";

const [releaseId, root] = process.argv.slice(2);
if (!releaseId || !root) throw new Error("Uso: node scripts/validate-release.ts <release-id> <raiz-das-releases>");
const release = await validateReleaseArtifacts(releaseId, root);
verifyExportParity(release);
console.log(`Pacote sintético validado: ${releaseId}; integridade, contratos e paridade da grade aprovados; revisão ${release.manifest.publication_review.decision}.`);
