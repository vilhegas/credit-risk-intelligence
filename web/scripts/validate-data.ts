import { validateAllReleases } from "../src/lib/data/releases.ts";

const count = await validateAllReleases();
console.log(`Resultados: ${count} release(s) validada(s).${count === 0 ? " Nenhum resultado publicável disponível." : ""}`);
