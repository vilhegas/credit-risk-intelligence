# Resultados públicos

`releases/` está vazio intencionalmente. Não há resultados sintéticos nem reais
aprovados nesta entrega. Não criar um manifesto com datas, hashes ou evidências
fictícios para preencher esse espaço.

Cada futura release imutável usa `releases/<release_id>/manifest.json` e somente
os JSON disponíveis declarados no catálogo. O contrato está em
[contrato-resultados-web.md](../../../docs/contrato-resultados-web.md).
Execute `npm.cmd run validate:data` dentro de `web/`; essa verificação também
é obrigatória em `npm.cmd run build`.

O loader é exclusivo de servidor/build (`node:fs` e `node:crypto`). Use
`loadRelease(releaseId)` de `src/lib/data/releases.ts` no servidor. Sem seleção,
retorna indisponibilidade explícita. Se uma release foi solicitada, arquivo
ausente ou inválido lança erro, sem fallback e sem substituir valores por zero.
`validateAllReleases()` verifica todas as pastas, inclusive não selecionadas.

Estados dos resultados:

- `synthetic`: artefato sintético válido, com gerador, semente e representação;
- `real_verified`: origem real com metadados, revisão aprovada e integridade
  verificadas contra o pacote; não é uma auditoria independente da fonte;
- `unavailable`: motivo textual, sem payload ou números inventados.

O catálogo reconhece os sete tipos do contrato e os esquemas validam seus
payloads. Os arquivos são projeções públicas selecionadas, não relatórios Python
inteiros. O exportador e a conciliação com os originais pertencem à tarefa 4.
As fixtures ficam exclusivamente em `tests/`, sem importação pela aplicação.

A lista positiva do Git só permite os nomes JSON reservados. Isso não aprova
automaticamente seu conteúdo: procedência, atribuição e privacidade exigem a
revisão humana registrada no manifesto. Não colocar dados brutos, previsões,
identificadores individuais, modelos ou credenciais aqui ou em `public/`.
