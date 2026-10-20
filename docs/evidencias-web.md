# Evidências publicáveis — tarefa 4

`web/exporters/export_synthetic.py` reaproveita os produtores locais e gera um
**candidato sintético para revisão**. Não lê dados importados, não acessa serviços,
não usa PostgreSQL e não importa nem executa avaliação final. O build Next.js
consome somente JSON; Python não é necessário na Vercel.

## Artefatos e resultados

O gerador original `demonstration_frame`, versão `demo-synthetic-v1`, usa semente
42 e produz 400 registros artificiais. `split_data` preserva seus parâmetros:
treino 0,6, validação 0,2, restante reservado, semente 42, estratificação por
cliente artificial. Nenhum dado é atribuído à população UCI ou a pessoas reais.

| Arquivo | Origem | Indicadores exportados |
| --- | --- | --- |
| `overview.json` | `demo.indicators` | Validação: observações, defaults, não defaults e taxa |
| `eda.json` | `analysis.eda.analyze` | Treino: alvo, ausências de 19 atributos, 13 distribuições/histogramas, grupos PAY/limite e correlações |
| `comparison.json` | `compare_models`, incluindo `train_reference` | Validação: sete candidatos, AP, ROC-AUC, precisão, recall, positivos previstos, diferenças e seleção; referência também inclui Brier |
| `interpretation.json` | `permutation_report` | Validação: 19 fatores da referência, 20 permutações, semente 42, quedas de AP e quantis |
| `simulation.json` | `demo.explore_policies` → `simulate_policies` | Validação: contagens, taxas, exposição, perdas, receitas, margens hipotéticas e grade agregada para 11 limiares |
| `manifest.json` | Adaptador web | Catálogo, origem, partições, configurações, ambiente, hashes e verificações efetivamente executadas |

Na execução entregue, treino tem **240** registros; validação tem **80**, com
**33 defaults** e taxa **0,4125**. Os 400 registros gerados não são o denominador
da visão geral. Todos esses indicadores são **sintéticos**.

A comparação selecionou `tree_depth6` pela AP da validação, conforme o módulo
original. Permutação e simulação continuam usando `logistic_c1`, versão
`demo-logistic-synthetic-v1`, como a demonstração original. O vencedor não
substitui silenciosamente esse modelo. A seleção na validação não é desempenho
final independente.

Hipóteses da simulação: exposição constante 100 por registro artificial,
multiplicador 1, LGD 0,5, receita 0,1, unidade monetária hipotética e horizonte de
um mês hipotético. Limiares: 0, 0,1, ..., 1. A exposição não deriva de `LIMIT_BAL`;
margem antes de custos não é lucro e pode ser negativa. A grade agrega somente
contagens e somas de probabilidades entre aprovados.

Calibração e avaliação final permanecem `unavailable`, sem arquivos fictícios.
O modelo usa `identity`, sem ajuste de calibrador. Segmentos não calculados são
nulos com nota. Os sete tipos de resultado real também são `unavailable`, com
referências nulas e motivo. O teste reservado nunca é usado para seleção ou
avaliação nessa exportação.

## Processo, integridade e reprodução

1. Exigir novo ID, sem sobrescrever release ou auditoria existente.
2. Registrar HEAD, estado efetivo do Git e snapshots/hashes dos arquivos de código
   permitidos, incluindo adaptador, testes e validadores.
3. Executar os testes do adaptador e dos produtores usados; ler o JUnit realmente
   produzido. Registrar comando sanitizado, revisão, código de saída, contagem e
   testes ignorados. Falhas impedem a promoção do pacote.
4. Gerar, dividir, ajustar somente no treino e calcular agregados de desenvolvimento.
   Conferir as probabilidades da referência contra `_bundle` da demonstração.
5. Projetar somente os campos permitidos, sem arredondamento; anotar nulos e
   contextualizar textos. A EDA pública não copia os textos fixos UCI/Taiwan/2005.
6. Gerar em staging fora de `src/data/`, validar com os schemas TypeScript da
   tarefa 3, conferir integridade e paridade da grade com os montantes Python.
   Tolerância relativa `1e-10`; contagens coincidem exatamente.
7. Conferir que código/procedência não mudaram, conservar auditoria local e
   promover a pasta completa por rename. Falhas anteriores não deixam release parcial.

O manifesto entregue registra **88 testes Python aprovados**, sem ignorados,
incluindo os **11 testes novos** e os produtores usados. A suíte verifica paridade
dos campos com os originais, repetição independente, denominadores, privacidade,
bloqueio de sobrescrita e recusa de adulteração mesmo com checksum recalculado.
O verificador TypeScript confere a grade financeira; isso não introduz dashboards
ou controles. Fórmulas de treinamento, métricas e montantes permanecem nos módulos
Python originais. O adaptador apenas seleciona campos, agrega a grade e serializa.

Representações e hashes:

- JSON canônico v1: UTF-8 sem BOM, `sort_keys=True`, `indent=2`,
  `ensure_ascii=False`, `allow_nan=False`, LF final. Bytes e SHA-256 do catálogo
  correspondem aos arquivos públicos finais exatos.
- Entrada privada: objeto `{columns, rows}` na ordem do gerador, incluindo IDs
  artificiais necessários à divisão; somente seu hash é público.
- Partições privadas: `ordered-input-positions-v1`, hash da entrada, nome e posições
  ordenadas; somente hashes e agregados são públicos.
- Modelos: hash do pipeline completo ajustado, pickle protocolo 5 conservado
  somente na auditoria local ignorada pelo Git. Inclui transformadores e
  classificador; não é hash apenas dos parâmetros. Exportação/verificação não
  desserializam modelos: reajustam o código local.
- Política: objeto canônico com configuração fixa, hash do modelo e instante UTC
  real do snapshot. Não houve seleção econômica dessa regra.
- Código: snapshots/hashes dos caminhos permitidos. HEAD é a revisão-base quando
  há alterações locais. Ambiente registra Python, bibliotecas, Node, arquitetura
  e runtimes numéricos; cálculo limitado a uma thread.

Os cinco resultados e os hashes de entrada, partições, modelos e política são
reproduzíveis com o mesmo código, ambiente, ID e instante de snapshot registrado.
Novas exportações têm datas/revisões/verificações reais próprias: o manifesto
completo não deve ser idêntico entre execuções. Não se promete identidade binária
entre plataformas ou versões. `--verify` regenera em memória e compara os bytes
da release existente sem modificá-la.

## Privacidade e revisão

Somente os seis JSON permitidos entram em `web/src/data/releases/<id>/`. Não
incluem registros, identificadores individuais, demografia, posições, previsões
individuais, modelos serializados, caminhos absolutos, credenciais ou relatórios
originais completos. IDs de release/modelo/partição são referências agregadas.

`web/reports/export-evidence/<id>/` é auditoria **local**, ignorada pelo Git,
fora de `public/` e `src/data/`: entrada artificial, partições, modelos, política,
relatórios originais e snapshots de código. Não copiar para pacote, downloads ou
hospedagem. Nenhum registro privado externo foi lido; toda entrada vem do gerador.

A CLI sempre registra revisão `pending`, revisor/data nulos e o estado observado
de `working_tree_clean`. O candidato entregue registra árvore suja, coerente com
as alterações sem commit. `validateReleaseArtifacts` valida para revisão;
`loadRelease` confere os mesmos bytes integralmente e retorna `unavailable`, sem
payload, enquanto a revisão estiver pendente. O build valida candidatos sem
promovê-los à apresentação.

Essa extensão pré-publicação do perfil v1 mantém a exigência pública: somente
revisão `approved`, identificada/datada, e procedência limpa permitem disponibilidade.
A revisão técnica automatizada **não substitui sua aprovação humana**. Conferir
origem, campos, rótulos, hipóteses, denominadores, paridade e ausência de informação
individual antes de aprovar. Para publicação posterior, gerar novo candidato com
código revisado/commitado e árvore limpa e registrar a revisão real do responsável
no manifesto antes de publicar. Não alterar `working_tree_clean` manualmente para
contornar a exigência. Releases publicadas só se corrigem por novo ID.

Este exportador não aceita dados reais. Uma exportação real futura exige licença,
procedência e política próprias, mínimos de publicação e análise de reconstrução
por grupos, histogramas e diferenças entre limiares. A demonstração sintética
não substitui essas decisões.

## Reproduzir no Windows

Arquivos desta entrega:

- Novos: `web/exporters/export_synthetic.py`, `web/exporters/tests/test_export_synthetic.py`
  e `web/exporters/README.md`.
- Novos: `web/scripts/validate-release.ts`, `web/scripts/verify-export-parity.ts`
  e `web/tests/exported-release.test.ts`.
- Novos: os seis JSON relacionados acima em `web/src/data/releases/synthetic-demo-v1/`
  e este documento.
- Ajustados para candidatos pendentes: `web/src/types/results.ts`,
  `web/src/lib/schemas/results.ts`, `web/src/lib/data/releases.ts`,
  `web/scripts/validate-data.ts` e `web/tests/results.test.ts`.
- Documentação ajustada: `docs/contrato-resultados-web.md`, `web/README.md`,
  `web/src/data/README.md` e `web/src/lib/schemas/README.md`.

Os módulos em `src/credit_risk/`, os testes em `tests/`, `streamlit_app.py` e
`pyproject.toml` foram preservados, sem alterações. Nenhuma dependência foi instalada.

Validação da entrega: lint e typecheck aprovados, 21 testes Node aprovados,
88 testes Python pertinentes aprovados (zero ignorados), build Next.js aprovado
e reprodução em processo independente aprovada. O build verificou um pacote e
preservou o estado de revisão pendente. A inspeção dos seis JSON finais passou
pela lista positiva dos schemas e pela verificação de campos privados.

Na raiz, com a `.venv` existente e Node 24.15+ da linha 24:

```powershell
.\.venv\Scripts\python.exe web\exporters\export_synthetic.py --verify synthetic-demo-v1
.\.venv\Scripts\python.exe web\exporters\export_synthetic.py --release-id synthetic-demo-v2
```

O primeiro verifica o candidato entregue; o segundo gera novo candidato e
executa automaticamente a suíte Python pertinente e a paridade TypeScript.
Use ID inexistente. Nenhum comando instala pacotes; dependências faltantes exigem
autorização. A CLI usa temporários exclusivos em `web/reports/`, no workspace.

Para executar apenas os testes novos:

```powershell
$exportTestTemp = Join-Path (Get-Location) ("web/reports/pytest-" + [guid]::NewGuid().ToString("N"))
.\.venv\Scripts\python.exe -m pytest web/exporters/tests -q -p no:cacheprovider --basetemp="$exportTestTemp"
```

Dentro de `web/`, executar `npm.cmd run lint`, `npm.cmd run typecheck`,
`npm.cmd run test` e `npm.cmd run build`. Não há migrações, serviços externos,
credenciais, dependência obrigatória de PostgreSQL ou Python durante o build.
