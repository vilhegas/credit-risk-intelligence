# Tratamento e qualidade — tarefa 6

Tecnologias: Python, Pandas, NumPy e Pytest. Dificuldade média. Estimativa: quatro horas.

## API e preservação

`credit_risk.preprocessing.quality.treat_frame(frame)` recebe um DataFrame com as 25 colunas na ordem de `COLUMNS` e devolve `QualityResult`, contendo registros aceitos, registros rejeitados e relatório agregado. Não acessa banco, rede ou arquivos. A entrada não é alterada. O responsável continua mantendo o ZIP e XLS originais na camada bruta, conforme o contrato de ingestão.

As saídas usam `source_position`, a posição da linha na entrada baseada em zero, independentemente dos rótulos originais do índice. As rejeições contêm os valores originais e todos os motivos encontrados. Devem permanecer na camada restrita de dados, fora do Git e dos painéis. Para vincular essas posições aos bytes de origem, manter o SHA-256 do XLS e a identificação da execução junto aos resultados.

## Regras determinísticas

- Cabeçalho incompatível, células não escalares ou excesso de linhas interrompem a chamada com ValueError. Uma entrada vazia com cabeçalho correto produz resultados vazios e relatório.
- Espaços externos são removidos de números textuais. Valores nulos e os textos vazios, NA, N/A, null, none e nan, sem distinção de maiúsculas, representam ausência.
- Campos numéricos usam Int64 anulável. Valores não numéricos, booleanos, complexos, infinitos, fracionários ou fora do intervalo inteiro seguro rejeitam a linha. Não há inferência de separadores locais.
- ID deve ser positivo; ID e alvo não podem estar ausentes. O alvo admite exclusivamente 0 e 1.
- Ausências nos atributos permanecem ausentes. Não há imputação, normalização estatística, tratamento de outliers, ajuste por frequência ou transformação aprendida antes da separação dos dados.
- SEX, EDUCATION, MARRIAGE e os campos PAY usam strings anuláveis. Códigos documentados são representados como strings numéricas. Outros códigos são preservados explicitamente como `nao_documentado:<codigo>`, com contagem no relatório. PAY -2 e 0 não recebem interpretação inventada nem são confundidos com ausência. O tipo string evita aprender um vocabulário global de categorias.
- Faturas negativas, zeros e valores extremos dentro do contrato são preservados. Não se presume domínio adicional para idade, limite ou pagamentos nesta etapa.
- Entre linhas sem erros de conteúdo, repetições idênticas após normalização conservam a primeira posição e rejeitam as demais. Se um ID apresenta qualquer divergência entre essas linhas, todas as suas linhas candidatas são rejeitadas como conflito. Linhas já inválidas continuam rejeitadas por seus próprios motivos.
- Linhas financeiras iguais com IDs diferentes permanecem distintas. Não se deduplicam clientes entre versões da fonte.

O relatório identifica a versão `uci-350-quality-v1`, entradas, aceites, rejeições, duplicatas removidas, linhas com IDs conflitantes, ausências, células inválidas e códigos não documentados por coluna. As contagens de ausências de entrada e códigos abrangem toda a entrada; as ausências finais abrangem apenas os aceites. Uma linha pode ter vários motivos, portanto a soma das contagens por motivo pode superar o total de rejeições. `report_json()` gera JSON estrito em memória, sem escrever arquivos.

## Integração incremental

A ingestão existente `uci-350-v1` mantém sua validação estrita e sua identidade de carga. Esta entrega acrescenta uma API de tratamento independente: não relaxa silenciosamente a leitura de arquivos nem modifica cargas históricas. A API pode consumir um DataFrame da ingestão aprovada ou uma leitura bruta local fornecida por um chamador, respeitando as mesmas exigências documentais de procedência. A ingestão estrita continuará rejeitando ausências antes dessa API caso seja usada como ponto de entrada.

As categorias agora são strings e as ausências são pd.NA; portanto, a saída não deve ser enviada diretamente ao conversor `int` da ingestão existente. A persistência dessa representação exigirá integração explícita e identidade própria de execução em etapa posterior. Nenhuma migração ou alteração de dados persistidos faz parte desta entrega.

A seleção dos 19 preditores financeiros continua sendo `FEATURES`; ID, alvo e demografia não integram essa lista. A presença de demografia na cópia tratada serve à rastreabilidade do contrato e não autoriza seu uso em modelos ou painéis. Codificação, imputação e demais transformações aprendidas deverão ser ajustadas exclusivamente no treino.

## Validação e conclusão

Vetores de argumentos para execução posterior, individualmente e sem shell, usando o ambiente já preparado:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_quality.py", "tests/test_ingestion.py"]
- ["python", "-m", "ruff", "check", "src/credit_risk/preprocessing/quality.py", "tests/test_quality.py"]

Os testes sintéticos cobrem preservação da entrada, tipos, ausências, categorias não documentadas, rejeições auditáveis, duplicatas, conflitos, entradas vazias, erros estruturais e serialização determinística do relatório. Os testes de integração preexistentes continuam dependendo das URLs de PostgreSQL exclusivo e podem ser ignorados quando elas não estiverem configuradas.

Critérios de conclusão: testes aprovados, relatório gerado para a versão local rastreável da fonte e diferenças revisadas antes do commit incremental. Esta resposta fornece somente arquivos propostos. Nenhuma operação, validação, alteração de arquivo, commit ou publicação foi executada; a aprovação dos testes e a geração de relatório sobre dados reais permanecem pendentes. A mensagem de commit é uma proposta.
