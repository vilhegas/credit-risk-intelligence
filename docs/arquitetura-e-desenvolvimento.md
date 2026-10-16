# Arquitetura e desenvolvimento incremental

## Objetivo desta entrega

Estruturar o pacote Python, declarar dependências e configurar Pytest e Ruff, preservando o README e o documento de escopo existentes. Não há implementação de ingestão, treinamento, banco ou painéis nesta etapa.

## Organização

O projeto utiliza layout src e o pacote credit_risk:

| Módulo | Responsabilidade |
| --- | --- |
| ingestion | Ler fontes locais elegíveis e registrar proveniência. |
| preprocessing | Validar esquema, tipos, alvo e qualidade dos dados. |
| analysis | Produzir exploração e indicadores agregados. |
| modeling | Separar amostras, ajustar pipelines e avaliar modelos. |
| simulation | Comparar limiares e indicadores das políticas. |
| presentation | Apresentar resultados em Streamlit e exportar agregados. |

O fluxo previsto é ingestão, tratamento, análise/modelagem, simulação e apresentação. Transformações aprendidas dos dados deverão permanecer dentro dos pipelines de modelagem e ser ajustadas somente no treino. A apresentação consome resultados; os módulos analíticos não devem depender da interface.

Importar os módulos não deve carregar dados, abrir conexões, iniciar interfaces ou treinar modelos. PostgreSQL, migrações Alembic e Docker Compose serão implementados na etapa de persistência. Power BI consumirá exportações e não será uma dependência Python.

## Ambiente e dependências

Utilizar Python 3.11 ou 3.12 em ambiente virtual isolado. O pyproject.toml declara versões exatas das dependências diretas e das ferramentas de desenvolvimento. O backend de construção também tem versão fixa.

Para preparar o ambiente em uma etapa autorizada, instalar este projeto com o extra dev. Essa preparação exige pacotes disponíveis localmente ou acesso autorizado a um índice. Nenhuma instalação é executada ou incluída no comando de validação desta entrega.

As dependências transitivas ainda não possuem arquivo de lock com hashes. Portanto, as versões diretas estão fixadas, mas a reprodução integral do ambiente permanece pendente de resolução e registro verificados. Não há alegação de instalação reproduzida nesta resposta.

## Validação local

Depois de instalar o pacote com o extra dev, executar separadamente os seguintes vetores de argumentos, sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest"]
- ["python", "-m", "ruff", "check", "."]
- ["python", "-m", "ruff", "format", "--check", "."]

O teste inicial verifica a importação dos sete pacotes e a presença de sua documentação. Ele verifica a estrutura instalada; não constitui teste de pipelines futuros. A compilação verifica sintaxe e não substitui Pytest ou Ruff. Compileall poderá criar arquivos de cache quando executado; esses arquivos estão ignorados pelo Git.

## Ciclo diário

1. Revisar o estado e as diferenças do Git, incluindo alterações preexistentes. Não descartar, sobrescrever ou incluir trabalho alheio sem revisão.
2. Escolher uma funcionalidade pequena e registrar tecnologias, dificuldade, esforço estimado e critérios de conclusão, seguindo docs/escopo-mvp.md.
3. Implementar somente essa funcionalidade, com documentação e testes proporcionais ao comportamento entregue.
4. Executar as validações pertinentes e registrar comandos, códigos de saída, resultados e limitações. Não declarar aprovação sem execução confirmada.
5. Revisar as diferenças e selecionar explicitamente os arquivos da entrega. Conferir ausência de dados brutos, artefatos e segredos; o gitignore não protege arquivos já rastreados.
6. Criar um commit incremental com mensagem descritiva e registrar seu hash após confirmação. Não reescrever o histórico anterior.
7. Enviar ao GitHub somente quando houver remoto configurado, credenciais e autorização. Nunca registrar credenciais no repositório. Se o envio não ocorrer, registrar a pendência sem declarar publicação.

## Etapa 2

- Tecnologias: Python, setuptools, Pytest, Ruff e Git.
- Dificuldade: baixa.
- Estimativa: 3 horas.
- Entrega: arquitetura modular, configuração de dependências, teste de importação e processo de desenvolvimento documentado.
- Critérios de conclusão: instalação confirmada em ambiente isolado, versões transitivas registradas para reprodução, testes e verificações aprovados, revisão das diferenças e commit incremental confirmado.

Esta resposta fornece os arquivos propostos. Nenhum comando, teste, instalação, alteração no repositório, commit ou envio ao GitHub foi executado. Os critérios que dependem dessas operações permanecem pendentes. A automação com GitHub Actions poderá ser adicionada em uma entrega posterior, após a validação do ambiente.
