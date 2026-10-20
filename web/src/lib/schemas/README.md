# Perfil executável de credit-risk-web-v1

Os validadores implementam uma lista positiva de campos sem dependências externas.
São funções que recebem `unknown`, verificam estrutura e invariantes e retornam
tipos TypeScript somente após a aprovação. Não usam coerção, defaults ou remoção
silenciosa de campos. Erros são exceções; indisponibilidade é um estado tipado.

O contrato editorial está em `docs/contrato-resultados-web.md` na raiz. Este
arquivo detalha a representação concreta escolhida para campos que aquele
documento descreve semanticamente. Alterar esta representação exige revisar
contrato, tipos, validadores, testes e produtor em conjunto.

- Origem sintética: `source` tem `generator`, `seed`, `configuration` e
  `representation` da entrada determinística; `license` tem `generation` e
  `publication_conditions`. A obtenção é nula.
- Origem real: `source` tem `title`, `publisher`, `reference`, `url` HTTPS
  pública; `license` tem `attribution`, `url`, `checked_at_utc`. A obtenção UTC
  e os hashes com papéis `zip` e `xls` são obrigatórios.
- `target`: `name`, `positive_class: 1`, `meaning`, `availability_assumption`.
- `quality`, quando presente no descritor: `input_rows`, `accepted_rows`,
  `rejected_rows`, `treatment_version`, `report_reference`. Quando nulo,
  justificar a ausência nas limitações. O overview usa a projeção mínima de
  `defaults`, `non_defaults`, `default_rate`; detalhes de qualidade não são
  copiados indiscriminadamente do relatório original.
- `producer.environment` é um mapa de versões e exige a chave `python`.
  `validation` é uma lista não vazia com `command`, `revision`, `exit_code`,
  `summary`, `skipped_tests`; registrar falhas e testes ignorados fielmente.
- `publication_review`: `reviewed_at_utc`, `reviewer`, `scope`, `privacy_policy`
  (referência da política aprovada) e `decision: approved`. Para grupos reais,
  essa política deve documentar os mínimos de publicação e a revisão de
  reconstrução; metadados e checksums não substituem a revisão humana.
  Na tarefa 4, candidatos podem usar `decision: pending` com data/revisor nulos e
  registrar o estado efetivo de `working_tree_clean`. A validação pública padrão
  continua exigindo aprovação e árvore limpa. `validateReleaseArtifacts` confere
  candidatos para revisão; `loadRelease` retorna indisponibilidade sem métricas
  enquanto a revisão estiver pendente. O exportador nunca inventa aprovação.
- `source_contract` usa `símbolo.qualificado@versão` da lista positiva em
  `results.ts`/`analysis.ts`. O símbolo nunca determina a origem. Adaptações
  são as projeções abaixo; alterações adicionais exigem novo perfil revisado.
  `describe_run` ainda não possui versão própria no Python e permanece fora da
  lista até a tarefa 4 definir e revisar uma versão do adaptador conciliado.
- UTC aceita somente instantes reais com `Z`, segundos e até três casas de
  milissegundos. Hashes são hexadecimais minúsculos completos.

## Projeções de payload

`analysis.ts` exporta os esquemas e seus tipos inferidos, reexportados por
`src/types/results.ts`. Os nomes dos campos preservam os produtores, exceto as
projeções explícitas para remover estruturas livres e caminhos privados:

- EDA seleciona somente `target`, `missing`, `distributions`, `patterns` e
  `correlations`. Os 19 atributos financeiros, 13 distribuições e sete grupos
  de variáveis são obrigatórios. Este perfil aceita grupos completos; se a
  revisão de privacidade exigir supressão de contagens, manter o resultado
  indisponível até um perfil de cobertura/supressão ser revisado.
- Comparação contém `reference` e `comparison`, anuláveis com nota, pelo menos
  um presente. Em referência, configurações são descrições sanitizadas;
  `train_partition_id` substitui a cópia de metadados livres da divisão.
  Na comparação, parâmetros dos candidatos são descrições sanitizadas;
  preservam-se sete candidatos, tabela, diferenças, volumes e seleção.
  `reference_report`, `split_metadata`, ambiente e orçamento não são duplicados
  no payload: rastreabilidade vem do manifesto e descritores relacionados.
- Calibração preserva curvas e tabela; a política contém os oito escalares da
  API. `calibration_partition_id` e `disjointness_verification` registram a
  partição e referência da verificação externa, sem publicar chaves de clientes.
  `selection_observations` deve ser o denominador principal. O ganho precisa ser
  estritamente maior que o mínimo para selecionar sigmoid, conforme o Python.
- Interpretação contém `permutation` e `segments`, anuláveis com nota, pelo
  menos um presente. Mantém métricas, diferenças, suficiência e Wilson. Segmentos
  insuficientes exigem métricas nulas e motivo. Quedas negativas são válidas.
- Avaliação final substitui a cópia irrestrita de `manifest` por `frozen`, com
  hashes, ambiente, revisão, data e referências `alignment_verification`,
  `calibration_once_verification`, `reserved_test_verification`.
  `restricted_manifest_sha256` identifica o original restrito; o checksum do
  JSON público permanece no catálogo, sem alegar identidade entre as cópias.
- Simulação contém `report` e `interactive_grid` explicitamente anulável.
  A grade exige `parity_verification`, referência à futura evidência de
  conciliação Python/TypeScript, além dos campos descritos no contrato.
  Cenários aceitam receita maior que um; margens negativas são preservadas.

Campos nulos de payload exigem nota não vazia no caminho pontuado, incluindo
índices de arrays, por exemplo `payload.metrics.precision` ou
`payload.correlations.0.pearson`. O campo estrutural `reason: null` de segmentos
suficientes não exige nota. Null não representa um artefato inteiro indisponível.

A tolerância numérica é `1e-10` (absoluta para taxas; relativa, com piso 1, para
valores calculados). Contagens coincidem exatamente. Valores são preservados,
sem arredondamento ou recálculo substitutivo. A grade nunca gera novas métricas
durante carregamento. A tarefa 4 demonstra paridade do candidato sintético contra
os produtores Python originais; consulte `docs/evidencias-web.md`. Isso não
substitui revisão humana ou comprova desempenho real.

Arquivos têm limite de 10 MiB e JSON tem profundidade máxima de 100. O loader
rejeita arquivos e diretórios simbólicos, caminhos arbitrários, arquivos extras,
bytes/hash divergentes e releases solicitadas ausentes. Não busca rede, não
treina modelos e não executa análises Python.
