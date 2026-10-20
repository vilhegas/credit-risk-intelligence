# Credit Risk Intelligence — frontend

Frontend independente com Next.js, TypeScript estrito, Tailwind CSS e ESLint. A tarefa 3 acrescentou carregamento e validação de resultados; a tarefa 4 entrega o [processo de evidências sintéticas](../docs/evidencias-web.md) e seu candidato para revisão, sem alterar a página inicial. Páginas analíticas, gráficos e controles de simulação pertencem às próximas tarefas. Python é usado somente na exportação offline; o build continua usando Node e JSON.

## Ambiente

- Windows com Node.js **24.15.0 ou superior da linha 24.x** e npm **11.x**. A versão de referência está em `.nvmrc`; nenhum gerenciador de versões é obrigatório.
- Apenas dependências gratuitas. Não requer Python, PostgreSQL, Docker ou credenciais.
- As versões diretas são fixadas em `package.json`; `package-lock.json` registra a resolução transitiva e deve ser versionado.

## Executar no Windows

No PowerShell, a partir da raiz do repositório Credit Risk Intelligence:

```powershell
Set-Location .\web
node --version
npm.cmd --version
npm.cmd ci --cache .npm-cache
npm.cmd run dev
```

Abrir `http://127.0.0.1:3000`. Encerrar com `Ctrl+C`. `npm ci` instala os pacotes do lockfile; executá-lo quando a instalação for necessária. O parâmetro `--cache .npm-cache` mantém o cache da instalação dentro de `web/`, ignorado pelo Git. O servidor local fica vinculado a `127.0.0.1`.

Os exemplos usam `npm.cmd` porque o PowerShell pode bloquear `npm.ps1` pela política de execução. Não é necessário alterar essa política. No CMD, ou onde o atalho funcionar, `npm` é equivalente.

## Validações

Executar dentro de `web/`:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

Ou executar todas em sequência com `npm.cmd run check`. O lint usa ESLint diretamente e trata avisos como falha. A verificação de tipos gera os tipos de rotas com `next typegen` antes de executar `tsc --noEmit`, permitindo rodar antes do primeiro build. O build executa `validate:data` antes de compilar e mantém a verificação de tipos do Next.js habilitada. Um artefato disponível inválido ou ausente interrompe o comando.

`npm.cmd run test` utiliza `node:test` e `node:assert/strict` do Node 24, com remoção nativa de tipos TypeScript. Nenhuma dependência adicional foi instalada. As fixtures artificiais estão restritas a `tests/`; os testes usam diretórios temporários removidos ao terminar. A suíte cobre JSON estrito, os sete payloads, origem, metadados, denominadores, integridade, incompatibilidade e indisponibilidade.

`npm.cmd run validate:data` confere todos os pacotes independentemente das páginas. Há um candidato sintético pendente em `src/data/releases/synthetic-demo-v1/`; sucesso na validação não representa aprovação de publicação. O carregador público mantém candidatos pendentes indisponíveis. Veja [src/data/README.md](src/data/README.md) para os estados e [o processo de evidências](../docs/evidencias-web.md) para regeneração no Windows.

Para conferir a versão de produção local após o build:

```powershell
npm.cmd run start
```

A revisão manual deve conferir navegação por âncoras, link de pular conteúdo, teclado, foco visível, zoom de 200% e larguras de celular e desktop. Os testes atuais verificam a camada de dados; não substituem testes de acessibilidade ou revisão visual da interface.

## Estrutura

```text
src/app/layout.tsx       Idioma, metadados e link de acesso ao conteúdo
src/app/page.tsx         Página inicial, sem métricas ou dados de exemplo
src/app/globals.css      Tailwind e tokens visuais iniciais
src/components/         Cabeçalho e navegação básica
src/types/results.ts    Contratos e estados de carregamento
src/lib/schemas/        Validação estrita de JSON, metadados e payloads
src/lib/data/           Leitura de releases e verificação de integridade
src/data/releases/      Futuros agregados públicos revisados (vazio)
tests/                  Testes unitários e de carregamento com node:test
scripts/validate-data.ts Verificação obrigatória antes do build
eslint.config.mjs       Regras Next.js e TypeScript
next.config.ts          Raiz de compilação restrita a web/
postcss.config.mjs      Integração Tailwind CSS
tsconfig.json           TypeScript em modo estrito
```

A fonte tipográfica é local ao sistema; o build não baixa fontes externas. Não há banco, API, leitura dos arquivos Python ou variáveis de ambiente obrigatórias. A camada de dados lê exclusivamente os agregados públicos da release no servidor/build.

## Preparação para Vercel

Em uma futura importação do repositório GitHub, selecionar **Root Directory: `web`**, preset **Next.js**, Node.js **24.x** e build **`npm run build`**. Manter a saída padrão do framework; usar `npm ci` para instalação a partir do lockfile. Não é necessário criar `vercel.json` nem configurar serviços de banco para esta etapa. A publicação manual detalhada pertence à tarefa 12 e não é realizada por estes arquivos.

`web/.gitignore` exclui dependências, builds, arquivos locais de ambiente, configurações locais npm, logs, metadados da Vercel e relatórios temporários. Nunca publicar segredos, dados brutos ou previsões individuais. As regras editoriais e de resultados permanecem em [apresentacao-web.md](../docs/apresentacao-web.md) e [contrato-resultados-web.md](../docs/contrato-resultados-web.md).
