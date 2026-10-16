# PostgreSQL e segurança básica — tarefa 3

Tecnologias: PostgreSQL 16, Docker Compose, SQLAlchemy, Psycopg, Alembic e Pytest. Dificuldade média; estimativa de quatro horas. Esta entrega antecipa a persistência prevista no roteiro do MVP, sem alterar a seleção futura da fonte.

## Preparação local

Usar as dependências já declaradas no pyproject.toml. Copiar .env.example para .env e preencher senhas distintas, fortes e locais. Docker Compose lê .env; Python e Alembic usam variáveis do processo e não carregam esse arquivo automaticamente.

Configurar MIGRATION_DATABASE_URL com o administrador e DATABASE_URL com credit_app, no formato postgresql+psycopg://USUARIO:SENHA_CODIFICADA@127.0.0.1:5432/credit_risk. Codificar caracteres especiais dos componentes da URL. Não imprimir URLs, incluí-las em commits ou armazená-las nos metadados das execuções.

Vetores de argumentos para execução posterior, separadamente e sem shell:

- ["docker", "compose", "config", "--quiet"]
- ["docker", "compose", "up", "-d", "--wait"]
- ["python", "-m", "alembic", "upgrade", "head"]
- ["python", "-m", "pytest"]
- ["python", "-m", "compileall", "."]

A inicialização requer a imagem já disponível quando não houver acesso autorizado à rede. O script de inicialização é interpretado pelo contêiner e deve ser salvo com finais de linha LF. Ele só roda quando o volume está vazio. Alterar .env não altera senhas de um volume existente; a rotação deve ser feita pelo administrador, sem remover dados.

## Modelo e acesso

execution_runs registra versão do conjunto, configuração e horário UTC do servidor. treated_records contém chave técnica anonimizada, data de referência, atributos financeiros tratados e alvo binário. predictions referencia o registro e a execução de previsão, permitindo prever registros produzidos em outra execução. Probabilidades usam NUMERIC e devem estar entre zero e um. Chaves estrangeiras, campos obrigatórios e unicidade impedem referências inexistentes e duplicações no mesmo contexto.

A aplicação recebe somente CONNECT no banco, USAGE no esquema credit e SELECT/INSERT nas três tabelas. Não recebe criação, alteração, exclusão ou acesso à tabela de controle Alembic. UUIDs são gerados pelo chamador, sem privilégios em sequências. Novas tabelas exigem concessões explícitas em novas migrações.

O usuário de bootstrap da imagem PostgreSQL é administrador e deve ser usado apenas para provisionamento e migrações. Sua URL nunca deve alimentar a aplicação. A porta publicada aceita conexões somente no loopback do host. Este ambiente local não configura TLS nem infraestrutura de produção.

O módulo persistence não conecta durante importação. Usar engine.begin() para transações atômicas e engine.dispose() ao encerrar o processo. save_run e get_run usam parâmetros vinculados; a aplicação não deve concatenar valores em SQL. hide_parameters reduz exposição de parâmetros em erros do SQLAlchemy, mas não substitui uma política de logs.

## Dados e segredos

O .gitignore existente já exclui .env, variantes, data/ e artifacts/. O arquivo .env.example contém somente nomes e campos vazios. Não incluir dados pessoais, credenciais, atributos sensíveis ou dados brutos em configuration/features. A validação de elegibilidade e qualidade desses documentos será implementada na ingestão. Dumps e exportações devem ficar em data/ ou artifacts/; arquivos já rastreados precisam de revisão explícita.

## Aceite e testes

Provisionar um segundo PostgreSQL exclusivo com o mesmo script de inicialização e configurar TEST_DATABASE_URL para credit_app e TEST_MIGRATION_DATABASE_URL para seu administrador. Nunca apontar essas URLs para um banco compartilhado ou com dados reais. Os testes aplicam a migração, repetem upgrade head, verificam conexão, persistência após commit, consultas parametrizadas, privilégios e restrições. Eles inserem apenas dados sintéticos; o teste de persistência mantém um pequeno conjunto para confirmar o commit. Demais casos usam rollback e savepoints. Nenhum teste remove tabelas ou bancos.

Sem ambas as URLs, os testes de integração ficam explicitamente ignorados; isso não comprova o aceite. Para comprovar migração em banco vazio, executar a suíte em uma instância exclusiva recém-provisionada. A aplicação não deve executar metadata.create_all(), pois isso contornaria as migrações e suas concessões.

Critérios de conclusão: upgrade em banco vazio e repetição aprovados, testes de conexão/persistência/restrições/permissões aprovados e revisão das diferenças sem segredos. Nenhuma operação, validação, alteração efetiva, criação de commit ou publicação foi executada nesta resposta. O comando de validação fornecido verifica apenas sintaxe; os demais critérios permanecem pendentes de execução. A mensagem de commit é uma proposta para aplicação posterior.
