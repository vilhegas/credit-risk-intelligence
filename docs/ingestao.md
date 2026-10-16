# Ingestão reproduzível — tarefa 5

Tecnologias: Python, Pandas, NumPy, xlrd, SQLAlchemy, PostgreSQL e Pytest. Dificuldade média; estimativa de quatro horas.

A função `credit_risk.ingestion.uci.ingest_uci(path, engine, provenance)` recebe um ZIP local, um Engine PostgreSQL e uma instância de `Provenance`. Não baixa arquivos nem executa migrações. O banco deve estar na revisão Alembic vigente, usando o usuário de aplicação descrito em `postgresql.md`.

Antes da importação, o responsável deve conferir as condições de uso e a sequência temporal no material oficial registrado em `fonte-publica.md`. Informar versão da fonte, data real de obtenção com fuso e referência da evidência consultada. As confirmações são declarações do responsável, não verificações automáticas da licença. Não inserir segredos nesses campos.

O contrato `uci-350-v1` aceita um ZIP contendo exclusivamente `default of credit card clients.xls`. O leitor usa xlrd 2.0.1, declarado nas dependências, lê a primeira planilha e considera a segunda linha como cabeçalho. Outros empacotamentos exigem revisão explícita do contrato. Nenhum membro é extraído em disco.

ZIP e XLS descompactado têm limite individual de 32 MiB; a leitura admite no máximo 100.000 registros. Esses limites restringem a entrada, mas não constituem isolamento de arquivos maliciosos. Conferem-se as 25 colunas na ordem documentada, campos numéricos inteiros finitos, ausência de nulos, ID positivo e único e alvo binário. Arquivos incompatíveis são rejeitados integralmente. Não há imputação, truncamento monetário ou exclusão silenciosa de linhas.

A contagem esperada de 30.000 registros gera um indicador de divergência, sem provocar exclusões. Códigos de pagamento e demografia não documentados são contados e preservados no contrato de leitura; sua interpretação permanece pendente da etapa de tratamento. Somente os 19 campos financeiros são persistidos como atributos. ID permanece exclusivamente como chave técnica; demografia não integra os atributos persistidos.

A execução registra origem, versão declarada, versão do contrato, nome e tamanho dos arquivos, SHA-256 do ZIP e do XLS, data de obtenção UTC, licença declarada, referência bibliográfica, versões de Pandas e NumPy e relatório de qualidade. A data de referência comum é 2005-09-30, explicitamente identificada como convenção. Os bytes devem continuar em `data/`, fora do Git.

A identidade da importação deriva da fonte, versão do contrato e SHA-256 do XLS. Recompactar o mesmo XLS ou alterar o nome do ZIP não cria outra carga. Alterar somente a versão declarada também reutiliza a execução original, preservando sua proveniência inicial. Conteúdos XLS diferentes constituem versões distintas; não se tenta deduplicar clientes entre versões históricas.

A inserção da execução usa `ON CONFLICT DO NOTHING` sobre sua chave primária. Execução e registros são gravados na mesma transação, em lotes de mil linhas. Uma falha reverte toda a carga. A restrição de unicidade do PostgreSQL também serializa importações concorrentes da mesma identidade. Uma reexecução válida retorna `reused=True`, sem inserir registros adicionais. Não são necessárias tabelas, privilégios ou migrações novos.

## Validação e conclusão

Após preparar o ambiente com as dependências declaradas, os vetores não interativos para execução posterior são:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_ingestion.py"]
- ["python", "-m", "ruff", "check", "src/credit_risk/ingestion/uci.py", "tests/test_ingestion.py"]

Os testes locais usam dados sintéticos e substituem a leitura Excel para testar validação, limites e checksums sem distribuir dados públicos. Não comprovam decodificação de um XLS real. O teste de integração exige TEST_DATABASE_URL e TEST_MIGRATION_DATABASE_URL para um PostgreSQL exclusivo, aplica migrações e verifica importação, proveniência, reexecução sem duplicatas e rejeição de alvo inválido. Sem essas variáveis, fica explicitamente ignorado. Não remove registros nem tabelas.

Critérios de conclusão: testes locais e integração aprovados; leitura do arquivo oficial conferida após confirmação documental; revisão das diferenças e commit incremental. Os testes de concorrência e de falha durante a persistência ainda não estão automatizados.

Esta entrega contém somente arquivos propostos. Nenhuma operação, alteração local, instalação, validação, consulta externa, commit ou publicação foi executada. O comando de validação fornecido verifica sintaxe quando executado; não substitui os testes. A mensagem de commit é uma proposta.
