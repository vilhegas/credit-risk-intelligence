# Consultas SQL e indicadores descritivos — tarefa 7

Tecnologias: PostgreSQL, SQLAlchemy, Python, Pandas e Pytest. Dificuldade: média. Estimativa: três horas.

## Uso e escopo

`credit_risk.analysis.indicators.describe_run(connection, run_id)` recebe uma conexão PostgreSQL existente e um UUID de execução de ingestão. Retorna quatro listas de dicionários: `volume`, `distribution`, `missing` e `segments`. As consultas SQL completas estão em `QUERIES`, no mesmo módulo. Não há conexão durante importação, alteração de tabelas ou gravação de resultados.

Todas as consultas filtram `credit.treated_records.run_id` por parâmetro vinculado. Nunca combinar versões da fonte implicitamente: o mesmo cliente pode existir em cargas diferentes. O chamador deve selecionar uma execução de dados, pois uma execução exclusivamente de modelagem pode não possuir registros tratados.

Para obter uma fotografia consistente entre as quatro consultas durante cargas concorrentes, o chamador deve configurar isolamento REPEATABLE READ antes de iniciar a transação. A função respeita a transação do chamador. O usuário credit_app já possui SELECT; não são necessárias migrações ou novas permissões.

## Definições

| Resultado | Definição |
| --- | --- |
| operations | Número de linhas na execução selecionada. Cada linha representa uma observação cliente/data, não um contrato ou uma transação bancária real. |
| subjects | Quantidade de chaves técnicas distintas dentro da execução. |
| reference_dates | Quantidade de datas de referência distintas. A data comum da UCI é uma convenção documental. |
| defaults | Soma do alvo binário defaulted, onde 1 indica inadimplência no mês seguinte conforme a fonte. |
| default_rate | Soma do alvo dividida pelo número de observações; proporção entre 0 e 1, sem ponderação monetária. |
| distribution | Contagem não nula, mínimo, máximo, média e percentis 25, 50 e 75 de LIMIT_BAL, BILL_AMT1 e PAY_AMT1. |
| missing | Contagem e proporção de ausências para cada um dos 19 atributos financeiros, com total de observações como denominador. |
| segments | Volume, inadimplentes e taxa por faixa de LIMIT_BAL em NT$: abaixo de 100.000; de 100.000 inclusive a 300.000 exclusive; 300.000 ou mais; ausente. |

Percentis usam `percentile_cont` no SQL e interpolação linear no Pandas. Distribuições ignoram ausências e preservam zeros e valores negativos. LIMIT_BAL é limite concedido, não exposição no momento da inadimplência; BILL_AMT1 e PAY_AMT1 representam fatura e pagamento de setembro de 2005. Não se somam essas medidas como se fossem operações independentes.

As faixas são fixas, descritivas e não constituem regras recomendadas de concessão. Grupos ausentes na amostra não geram linhas; cada grupo presente informa seu denominador. Não se utilizam atributos demográficos nem se atribui significado aos códigos PAY não documentados.

## Contrato e casos extremos

As consultas monetárias pressupõem atributos financeiros numéricos finitos ou JSON null/chave ausente, conforme o contrato de ingestão. Conteúdo incompatível causa erro de conversão; não é convertido silenciosamente em ausência. As ausências são reconhecidas por chave inexistente ou JSON null. Strings vazias e a string literal "null" não são ausências válidas nesse contrato.

A ingestão estrita atual não persiste ausências. O indicador pode retornar zero em todas as colunas nessa versão. A representação do tratamento independente ainda exige integração explícita antes de persistir categorias e pd.NA; esta entrega preserva essa limitação.

Uma execução sem registros retorna volume e inadimplentes iguais a zero, taxa global indisponível, três distribuições sem valores observados, 19 contagens de ausência iguais a zero com taxas indisponíveis e nenhuma linha de segmento. Uma variável inteiramente ausente tem distribuição indisponível e taxa de ausência igual a 1 quando há registros. SQL NULL retorna como None; proporções não são multiplicadas por 100. A função não distingue execução inexistente de execução sem registros.

## Validação e conclusão

O teste controlado compara os resultados SQL com cálculos Pandas independentes, incluindo limites exatos das faixas, fatura negativa, zero, chave ausente, JSON null, variável inteiramente ausente, execução vazia e isolamento entre versões. A amostra é exclusivamente sintética. As inserções ficam em uma transação revertida ao final; não há exclusão de tabelas ou registros.

Vetores não interativos para execução posterior, separadamente e sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_indicators.py"]
- ["python", "-m", "ruff", "check", "src/credit_risk/analysis/indicators.py", "tests/test_indicators.py"]

A integração exige TEST_DATABASE_URL e TEST_MIGRATION_DATABASE_URL de PostgreSQL exclusivo para testes, previamente provisionado. Aplica as migrações existentes antes da amostra. Sem ambas as variáveis, a comparação SQL/Pandas fica explicitamente ignorada, não aprovada.

Critérios de conclusão: comparação SQL/Pandas aprovada em PostgreSQL, definições revisadas e commit incremental confirmado. Esta resposta apresenta somente arquivos completos propostos. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. O comando de validação fornecido verifica sintaxe quando executado e não substitui a comparação com PostgreSQL. A mensagem de commit é uma proposta.
