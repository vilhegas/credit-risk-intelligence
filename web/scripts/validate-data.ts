import { validateAllReleases } from "../src/lib/data/releases.ts";

const count = await validateAllReleases();
console.log(`Resultados: ${count} pacote(s) validado(s).${count === 0 ? " Nenhum resultado publicável disponível." : " Candidatos pendentes continuam indisponíveis para apresentação."}`);
