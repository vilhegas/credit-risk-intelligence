# Contrato público de resultados web

## Finalidade e status

Versão normativa proposta: `credit-risk-web-v1`. Este contrato orienta as tarefas 3 e 4 do [plano de apresentação](apresentacao-web.md). Não é um schema já implementado e não altera APIs Python. Os produtores existentes retornam formatos distintos; um futuro adaptador em `web/` deverá validar, selecionar e contextualizar suas saídas, preservando os cálculos.

O frontend consumirá somente JSON UTF-8 estrito, com números finitos. Não aceitar comentários, chaves duplicadas, `NaN`, infinitos, números em strings ou versões desconhecidas. Objetos terão campos permitidos explicitamente; extensões exigem atualização do contrato e dos validadores. Contagens devem ser inteiros não negativos seguros em JavaScript. Arredondamento é apenas visual.

## Organização prevista

```text
web/src/data/releases/<release_id>/
  manifest.json
  overview.json
  eda.json
  comparison.json
  calibration.json
  interpretation.json
  final-evaluation.json
  simulation.json
```

O manifesto lista apenas arquivos realmente presentes. Tipos indisponíveis constam no catálogo do manifesto com motivo, sem arquivo de resultado fictício. Os nomes acima são reservados por tipo; downloads públicos serão uma seleção revisada desses agregados. Importar um JSON no bundle não o torna privado.

### Manifesto de release

| Campo | Tipo / regra |
| --- | --- |
| `schema_version` | Literal `credit-risk-web-v1` |
| `release_id` | Identificador textual único, sem caminhos, imutável após publicação |
| `generated_at_utc` | Instante real da exportação, ISO 8601 UTC; não é data da fonte |
| `producer` | Objeto com `code_revision` (hash Git completo), `working_tree_clean` (deve ser verdadeiro para publicação), `exporter_version`, `environment` (versões efetivamente usadas de Python e bibliotecas) |
| `datasets` | Lista de descritores de dados definidos abaixo; IDs exclusivos |
| `models` | Lista de modelos: `model_id`, `dataset_id`, `model_version`, `family`, `features`, `configuration`, `partition_sha256`, `model_sha256`, `calibration_method` (`identity` ou `sigmoid`) |
| `policies` | Lista de políticas: `policy_id`, `model_id`, `policy_sha256`, `threshold`, `configuration`, `frozen_at_utc`; pode ser vazia quando não há política congelada |
| `results` | Lista de entradas de catálogo por tipo e contexto, inclusive indisponíveis |
| `validation` | Referências sanitizadas às verificações efetivamente executadas: comando, revisão, código de saída, resumo e testes ignorados; não declarar sucesso não observado |
| `publication_review` | Data UTC real, responsável pela revisão, escopo, referência da política de privacidade e decisão `approved` necessária para publicação |
| `limitations` | Lista não vazia de limitações editoriais aplicáveis à release |

Uma entrada de `results` contém `result_id`, `kind`, `dataset_id`, `partition_id`, `model_id` e `policy_id` (estes dois podem ser nulos para resultados sem modelo/política), `availability` (`available` ou `unavailable`) e `reason` (texto obrigatório quando indisponível; nulo caso contrário). Para `available`, exige `path`, `sha256` e `bytes`; para `unavailable`, esses três campos são nulos. `kind` pertence a `overview`, `eda`, `comparison`, `calibration`, `interpretation`, `final_evaluation` ou `simulation`.

Em entradas `unavailable`, referências a dados, partições, modelos ou políticas ainda não produzidos também são nulas. Não criar descritores com hashes ou volumes fictícios para representar uma análise pendente. Assim, uma release apenas documental pode conter listas vazias de datasets, modelos e políticas e um catálogo de resultados indisponíveis. Identificadores não nulos devem sempre resolver para descritores existentes; IDs de resultados são exclusivos. `bytes` é inteiro positivo para arquivos disponíveis.

`path` deve ser relativo à pasta da release, sem `..`, URL, caminho absoluto ou arquivo fora da lista permitida. `sha256` é o hash hexadecimal minúsculo de 64 caracteres dos bytes exatos do arquivo. O manifesto não inclui o próprio hash em seu conteúdo; seu vínculo é a revisão de publicação no Git. Um checksum detecta alteração de bytes, mas não comprova procedência científica ou autenticidade por si só.

### Descritor de dados

| Campo | Tipo / regra |
| --- | --- |
| `dataset_id`, `dataset_version` | Textos não vazios; identidade e versão efetivas |
| `origin` | `real` ou `synthetic`; indisponibilidade é independente da origem |
| `source` | Título, publicador, referência e URL pública quando aplicável; para sintético, caminho do gerador, semente e configuração |
| `license` | Registro de atribuição, URL e data da conferência para fonte real; para sintético, descrição de geração local e condições de publicação revisadas |
| `obtained_at_utc` | Data real de obtenção para fonte real; nulo para gerador local |
| `source_hashes` | Lista `{role, sha256}`; fonte real exige ZIP e XLS e, se usado, CSV derivado; sintético exige hash de uma representação determinística da entrada e descrição dessa representação |
| `population`, `observation_unit` | Textos que delimitam a população e a unidade; não afirmar um cliente único sem verificação |
| `reference_period`, `horizon`, `currency` | Descrição explícita; moeda e período observado podem ser nulos quando não se aplicam, com justificativa em `limitations` |
| `target` | Nome original, `positive_class: 1`, significado e hipótese de disponibilidade dos atributos |
| `quality` | Contagens de entrada/aceites/rejeições, versão do tratamento e referência do relatório agregado revisado, ou nulo com justificativa quando esse fluxo não foi aplicado |
| `partitions` | Lista de descritores de partição |
| `limitations` | Lista não vazia, coerente com a origem |

Cada partição contém `partition_id`, `role` (`full`, `train`, `validation`, `calibration`, `selection` ou `test`), `observations`, `class_counts` com chaves `0` e `1`, `method`, `partition_sha256` e `used_for`. Este último lista os usos efetivos, como exploração ou seleção. O hash identifica um manifesto restrito com composição e ordem das linhas; esse manifesto não é publicado. Registrar sementes, fronteiras e exclusões quando aplicáveis. Subdivisões de desenvolvimento devem referenciar a partição de origem e a verificação de disjunção.

Todos os hashes de procedência usam SHA-256 e identificam uma representação documentada, com formato e regra de serialização registrados no exportador. Para modelos, conservar o artefato restrito ou uma representação completa de seu estado ajustado; hash apenas de hiperparâmetros não identifica o modelo treinado. Para políticas, conservar a configuração congelada efetiva. Modelos, datasets e políticas sem evidência suficiente não recebem descritores de objetos verificados.

Os nomes de versão dos módulos não estabelecem origem: `uci-350-eda-v1` pode calcular sobre uma entrada sintética. `origin` deve resultar da entrada rastreada, nunca de um prefixo de versão. Da mesma forma, “real” qualifica a origem dos dados; uma simulação sobre dados reais ainda tem hipóteses econômicas artificiais.

## Envelope de cada resultado disponível

| Campo | Regra |
| --- | --- |
| `schema_version`, `release_id`, `result_id`, `kind` | Devem coincidir com o manifesto |
| `dataset_id`, `partition_id`, `model_id`, `policy_id` | Referências ao catálogo; nulos somente quando não aplicáveis |
| `origin` | Igual à origem do dataset |
| `source_contract` | Versão do produtor Python e símbolo utilizado; adaptações identificadas |
| `observations` | Número efetivo de observações daquele resultado, conciliado com sua partição |
| `payload` | Conteúdo tipado conforme as seções seguintes |
| `metric_notes` | Notas por caminho de métrica nula, suprimida ou com convenção especial de cálculo |
| `limitations` | Lista com contexto necessário à interpretação |

Para relatórios que abrangem várias partições, `partition_id` identifica a partição principal avaliada; o payload referencia explicitamente as demais. Exemplo: comparação avalia validação e registra contexto do treino; calibração avalia seleção e registra o subconjunto usado para ajustar o calibrador. Nunca somar esses volumes para fabricar o denominador de uma métrica.

Uma ausência de resultado não é uma métrica nula. `unavailable` significa que o artefato não foi produzido ou aprovado. Dentro de um resultado disponível, `null` significa ausência matemática, informação não calculada ou supressão, sempre com motivo em `metric_notes`. Zero só representa um valor efetivamente calculado. Falha de carregamento ou integridade é erro; não autoriza fallback silencioso para demonstração sintética.

Taxas e probabilidades são frações entre 0 e 1, convertidas em porcentagens somente na apresentação. A classe positiva é inadimplência; uma classificação positiva recusa o registro na política. Matrizes usam `[[TN, FP], [FN, TP]]`: linhas são classes reais 0/1 e colunas são classes previstas 0/1. Aprovação é `(TN + FN) / N`, inadimplência entre aprovados é `FN / (TN + FN)` e recall de inadimplentes é `TP / (TP + FN)`, respeitando as convenções de denominador zero de cada produtor. Contagens por classe somam a população da partição; bins de calibração publicados sem supressão somam a população avaliada. Nenhuma dessas regras autoriza divulgar células protegidas pela política de privacidade.

## Payloads e produtores

### Visão geral e qualidade

`overview` contém `defaults`, `non_defaults` e `default_rate`, derivados da mesma população de `observations`. Exige `defaults + non_defaults = observations`; a taxa é `defaults / observations`, ou nula para população vazia. A origem pode ser `demo.indicators`, o resumo EDA ou uma exportação conciliada de `describe_run`, declarada em `source_contract`.

Operações, sujeitos e datas de referência de `describe_run` têm significados diferentes. Não renomear operações como clientes sem unicidade comprovada. Na demonstração, o denominador vem da validação retornada por `_bundle`, não do total gerado.

O bloco opcional de qualidade seleciona contagens de `QualityResult.report`: `input_rows`, `accepted_rows`, `rejected_rows`, duplicatas, conflitos, ausências, códigos não documentados e rejeições por motivo. Exigir entrada = aceites + rejeições. Motivos podem se sobrepor; não somá-los como se fossem linhas exclusivas. Ausências de entrada usam entrada como denominador; ausências após tratamento usam aceites. Remover campos demográficos do pacote público e revisar contagens pequenas.

### Exploração (`eda`)

Produtor: `analysis.eda.analyze`, versão `uci-350-eda-v1`. Preservar os campos selecionados `target`, `missing`, `distributions`, `patterns` e `correlations`, com as estruturas retornadas pela API:

- `target`: contagens `0`/`1`, taxa, razão minoria/maioria e presença das duas classes.
- `missing`: por atributo financeiro, `count` e `rate`, denominador igual a `observations`.
- `distributions`: `observed`, mínimo, quartis, mediana, máximo, média, desvio amostral e `histogram` com `lower`, `upper`, `count`. São 13 atributos monetários. Histograma usa dez intervalos quando há valores, último intervalo inclui a borda direita; soma das barras = `observed`.
- `patterns`: listas `{group, observations, defaults, default_rate}` por PAY e por faixa de LIMIT_BAL. Faixas: abaixo de 100000, de 100000 inclusive a 300000 exclusive, 300000 ou mais, e ausente. Categorias PAY não documentadas mantêm seu rótulo, sem significado inventado.
- `correlations`: `{left, right, observations, pearson, spearman}`. Valores entre -1 e 1 ou nulos; menos de três pares completos ou variável constante produz indisponibilidade. PAY não entra na matriz numérica.

Cada grupo publicado identifica seu denominador. Sem supressão, grupos de uma variável cobrem a população avaliada. Havendo supressão, registrar cobertura e não exigir soma pública que permita reconstruir células ocultadas. Para EDA orientadora de modelagem, usar treino já fixado; exploração de base completa deve ser identificada e ter seu uso registrado. Textos UCI fixos no produtor não servem como procedência de uma entrada sintética.

### Modelos (`comparison`)

Produtores: `modeling.reference.train_reference` (`uci-350-reference-v1`) e `modeling.comparison.compare_models` (`credit-comparison-v1`). O payload contém `reference` (relatório agregado de referência) e `comparison` (relatório agregado da comparação), cada um anulável com motivo se não executado; pelo menos um deve existir. Não preencher Brier da comparação com valor de outro modelo: esse campo existe na referência, não nas linhas atuais da comparação.

Preservar configurações, lista de atributos, semente, volumes, prevalências, tabela de candidatos, AP, ROC-AUC, precisão, recall, positivos previstos, diferenças de AP, candidato selecionado e critério de desempate, conforme disponíveis no respectivo relatório. A referência e a comparação avaliam validação. Os seis candidatos e Dummy não representam sete resultados já medidos neste repositório.

AP, ROC-AUC, Brier, precisão e recall ficam entre 0 e 1; diferenças de AP podem ser negativas. Precisão sem positivos previstos é zero na comparação atual (`zero_division=0`): preservar essa convenção e explicá-la. Não substituir por nulo sem registrar uma transformação contratual. Não reconstruir matriz de confusão a partir de métricas arredondadas.

### Calibração (`calibration`)

Produtor: `select_policy`, versão `credit-calibration-v1`. Preservar `before`, `sigmoid_candidate`, ganho de Brier observado, ganho mínimo, método selecionado, `policy`, `threshold_table`, `selected`, desempate e volumes de calibração/seleção. `sigmoid_candidate` não é automaticamente o calibrador escolhido.

Registrar partições disjuntas e o uso da seleção compartilhada para escolher calibração e limiar. Custos de falsos negativos/positivos são hipóteses de seleção, sem equivalência automática a perda monetária. As curvas usam intervalos uniformes, omitindo vazios e atribuindo fronteiras internas ao intervalo inferior. Cada ponto contém bin, contagem, probabilidade média e taxa observada.

### Interpretação (`interpretation`)

O payload contém `permutation` e `segments`, anuláveis com motivo; pelo menos um deve existir. Produtores: `permutation_report` (`permutation-v1`) e `segment_report` (`segments-v1`).

Permutação preserva AP de referência, observações, repetições, semente e fatores com `feature`, `mean_ap_decrease`, `permutation_std`, `permutation_quantiles_025_975`. Quedas negativas são válidas. Quantis entre permutações não são intervalos populacionais nem direção causal.

Segmentos preservam limiar, critérios de suficiência, métricas globais e linhas com contagens, `sufficient`, `metrics`, diferenças e motivo. Defaults atuais: mínimo de 100 observações e 20 por classe, configuráveis na API. Esses critérios controlam cálculo estatístico, não autorização de publicação. Taxas estruturadas do produtor incluem numerador, denominador, valor e Wilson 95%; não aplicar Wilson a AP, AUC ou Brier. Segmentos insuficientes não recebem métricas inventadas.

### Avaliação final (`final_evaluation`)

Produtor: `evaluate_once`, versão `final-evaluation-v1`. Preservar métricas do modelo e baseline, diferença de AP, matriz, limiar congelado, calibração, comparação descritiva e `uncertainty`: método, semente, orçamento, reamostragens descartadas e intervalos com seus denominadores válidos. Não prometer intervalos para métricas que o produtor não inclui.

O manifesto congelado exige hashes de dados, partições, modelo e política, revisão, ambiente e instante real do congelamento. Uma cópia pública deve ser sanitizada antes da exportação. Caso a sanitização altere os bytes/estrutura do manifesto, não apresentar seu hash como se verificasse a cópia pública: distinguir referência ao original restrito do checksum do artefato público.

O teste deve ser o reservado original, acessado após congelamento. Registrar verificação externa de alinhamento e aplicação única da calibração. O bloqueio por diretório de `evaluate_once` não impede repetição em outro diretório. Não repetir avaliação para selecionar melhor resultado; manter inclusive desempenho inferior ao baseline.

### Simulação (`simulation`)

Produtor: `simulate_policies`, versão `credit-policy-v1`. O payload contém `report` com metadados, cenários, limiares, observações, defaults, linhas agregadas e limitações da API; opcionalmente, `interactive_grid` para o modo web. Hipóteses, moeda e horizonte devem estar visíveis independentemente da origem real ou sintética.

Para cada cenário/limiar, preservar aprovados, recusados, defaults aprovados/recusados, taxas, exposição aprovada, perdas, receitas e margens. Regras:

- Aprovar se `p < threshold`; igualdade recusa. Limiar 1 ainda recusa `p = 1`.
- Pelo menos três limiares distintos, finitos, ordenados e entre 0 e 1.
- `approved + rejected = observations`; defaults aprovados + recusados = defaults totais.
- Taxa entre aprovados é nula sem aprovados; montantes somados são zero nesse caso.
- LGD entre 0 e 1; multiplicador de exposição, exposição e receita não negativos e finitos. A API geral não limita receita a 1; a interface pode adotar limite mais estrito, documentado.
- Perda esperada = soma de `p × EAD × LGD`; receita esperada = soma de `(1-p) × EAD × r`, apenas nos aprovados. Margem = receita menos perda e pode ser negativa.
- Cenário com desfecho histórico substitui `p` por `y`, ainda sob hipóteses de EAD, LGD e receita; não é resultado financeiro realizado.

`interactive_grid` é uma extensão futura do exportador, não uma saída atual do Python. Restrita a exposição constante por registro, contém `exposure_mode: constant`, `observations`, `defaults`, `probability_stage` (`raw` ou `calibrated`, coerente com o modelo), e linhas `{threshold, approved, approved_defaults, approved_probability_sum}`. Exigir `0 <= approved_probability_sum <= approved`, contagens coerentes e limiares únicos. Para exposição ajustável `e` e multiplicador `m`, recalcular:

```text
EAD constante = e × m
perda esperada = approved_probability_sum × EAD × LGD
receita esperada = (approved - approved_probability_sum) × EAD × r
perda de cenário histórico = approved_defaults × EAD × LGD
receita de cenário histórico = (approved - approved_defaults) × EAD × r
```

Os controles selecionarão apenas limiares exportados, sem interpolação apresentada como exata. Validar paridade com o Python em fixtures e tolerância numérica registrada. Não aplicar essa fórmula a exposições individuais variáveis nem publicar vetores individuais para obter interatividade. A grade também passa pela revisão de privacidade, pois diferenças entre limiares podem revelar grupos pequenos.

## Procedência e integridade

1. Conferir fonte, atribuição e condições de uso antes de produzir resultados reais. A dimensão esperada de 30000 registros no documento da UCI não substitui contagem da entrada, dos aceites ou das partições.
2. Registrar bytes de origem, hashes, transformações, composição e ordem das partições em evidência restrita. Versões textuais e sementes isoladas não garantem reprodução.
3. Relacionar cada métrica à origem, população, partição, modelo, calibração, política, horizonte e unidade pertinentes. Não misturar artefatos de execuções diferentes pelo nome do arquivo.
4. Congelar escolhas antes do teste. Exportação e build não treinam, recalibram, selecionam ou reavaliam automaticamente o teste final.
5. Gerar JSON estrito, calcular hashes dos arquivos finais e verificar referências, versões, domínios e invariantes. Para taxas e montantes, definir e registrar tolerâncias numéricas na implementação; contagens devem coincidir exatamente.
6. Validar metadados contra o relatório original. Hashes declarados são checáveis, mas o vínculo semântico com previsões exige revisão externa.
7. Interromper build em resultado disponível inválido, arquivo ausente, hash divergente, referência incompatível ou versão desconhecida. Uma indisponibilidade explicitamente catalogada permite construir a página com estado informativo.
8. Preservar releases anteriores; corrigir com nova release identificada. Não editar uma execução já apresentada como congelada.

## Privacidade e publicação

O pacote público usa lista positiva de campos. Excluir IDs, chaves de sujeitos, posições de origem, linhas aceitas/rejeitadas, atributos ou previsões individuais, demografia, ZIP/XLS/CSV brutos, modelos serializados, credenciais, URLs autenticadas, caminhos privados e logs com entradas. Hash de identificador não torna um registro publicável.

Agregação não garante anonimização. Antes de publicar dados reais, exigir revisão registrada de grupos pequenos, extremos, combinações de filtros, histogramas, totais complementares e diferenças entre limiares/releases. A política deve fixar um tamanho mínimo público e eventuais mínimos por desfecho com justificativa; não se define aqui um número universal como garantia. Sem política aprovada, resultados segmentados reais e grades reais permanecem indisponíveis.

Quando necessário, agrupar categorias ou suprimir células e complementos que permitam reconstrução. Valores suprimidos são nulos com motivo; denominadores e contagens sensíveis também devem ser protegidos. A supressão pode tornar uma visualização indisponível. Manter o cálculo original restrito e registrar transformação pública, cobertura e limitações, sem alterar silenciosamente conclusões. Os mínimos de `segment_report` não substituem essa revisão.

Dados sintéticos devem ser identificados em toda visualização e exportação, com gerador e versão. Mesmo nesse caso, remover identificadores técnicos desnecessários. A primeira versão não receberá dados pessoais, uploads ou registros financeiros de visitantes, nem precisará armazenar entradas de simulação.

## Checklist de aceite dos futuros artefatos

- Origem e disponibilidade distintas e corretas; nenhum número preenchido para demonstrar layout.
- Referências resolvidas e hashes conferidos sobre os bytes finais.
- Contagens, taxas, unidades, partições e convenções de nulos conciliadas com o produtor.
- Métricas negativas, segmentos insuficientes e limitações preservados.
- Comparação e seleção identificadas como desenvolvimento; teste final com congelamento e governança registrados.
- Privacidade e atribuição aprovadas, sem dados individuais ou reconstrução evidente por células complementares.
- Paridade Python/JSON e, quando aplicável, Python/TypeScript registrada com comandos e resultados reais.
- Conteúdo e downloads exibem origem, contexto e limitações; ausência e erro são estados distintos.

Nesta tarefa, o checklist define obrigações futuras. Não houve geração de artefatos analíticos, cálculo de métricas, execução da suíte Python ou aprovação de publicação.
