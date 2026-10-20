# Credit Risk Intelligence

Plataforma educacional de análise e previsão de inadimplência, com arquitetura modular, avaliação de modelos e simulação de políticas de crédito.

**Versão demonstrativa proposta: 0.1.0**, correspondente à versão declarada em `pyproject.toml`. Publicação no GitHub, execução desde clone limpo e verificações de segurança permanecem pendentes. Nenhum comando foi executado na preparação desta documentação.

## Demonstração local

A interface Streamlit utiliza exclusivamente 400 registros sintéticos gerados localmente. Oferece indicadores, previsão de um registro financeiro e comparação de três políticas. Não exige PostgreSQL, arquivos UCI ou Power BI. O modelo é ajustado somente no treino artificial; exploração e simulações usam validação, mantendo o teste reservado.

Pré-requisitos: Python 3.11 ou 3.12, pacote instalado e dependências declaradas em `pyproject.toml` disponíveis no ambiente. O extra `dev` é necessário para Pytest e Ruff. Um clone isolado não satisfaz esses requisitos. A preparação do ambiente deve ocorrer separadamente; os comandos abaixo não instalam nem baixam componentes.

Executar a partir da raiz do projeto, como vetor de argumentos sem shell:

```json
["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address", "127.0.0.1"]
```

Abrir `http://127.0.0.1:8501`. O processo permanece ativo enquanto a interface estiver em uso. Não inserir informações pessoais nos formulários.

## Tecnologias e componentes

| Componente | Tecnologias |
| --- | --- |
| Ingestão e tratamento | Python, Pandas, NumPy, xlrd |
| Persistência | PostgreSQL, SQLAlchemy, Psycopg, Alembic, Docker Compose |
| Exploração | Pandas, NumPy, SciPy, HTML/SVG |
| Modelagem | Scikit-learn, pipelines, regressão logística, árvores e DummyClassifier |
| Políticas | NumPy e Pandas, com hipóteses financeiras explícitas |
| Apresentação | Streamlit e especificação Power BI com SQL, M e DAX |
| Qualidade e versionamento | Pytest, Ruff, Git e GitHub Actions |

O painel Power BI ainda exige montagem e validação no Desktop. A avaliação final sobre dados reais não possui resultados confirmados. A documentação descreve contratos e implementações propostas; sua existência não comprova execução bem-sucedida.

## Documentação

- [Arquitetura demonstrativa](docs/arquitetura-demonstrativa.md): componentes e fronteiras de integração.
- [Reprodução e publicação](docs/versao-demonstrativa.md): procedimento de aceite, histórico das etapas e pendências.
- [Catálogo da demonstração e ficha do modelo](docs/ficha-demonstracao.md): origem sintética, uso previsto e limitações.
- [Fonte pública e dicionário](docs/fonte-publica.md): contrato UCI, condições de uso e 25 campos esperados.
- [Escopo e critérios de aceite](docs/escopo-mvp.md).
- [PostgreSQL](docs/postgresql.md), [ingestão](docs/ingestao.md) e [qualidade](docs/qualidade-dados.md).
- [Exploração](docs/analise-exploratoria.md), [partições](docs/particoes-e-vazamento.md), [referência](docs/modelo-referencia.md) e [comparação](docs/comparacao-modelos.md).
- [Calibração](docs/calibracao-e-limiares.md), [interpretação](docs/interpretacao-e-segmentos.md), [simulação](docs/simulacao-politicas.md) e [avaliação final](docs/avaliacao-final.md).
- [Streamlit](docs/demonstracao-interativa.md) e [Power BI](docs/power-bi.md).

## Verificação posterior

Executar separadamente em ambiente previamente preparado, sem shell:

```json
["python", "-m", "compileall", "."]
```

```json
["python", "-m", "ruff", "check", "."]
```

```json
["python", "-m", "pytest"]
```

A compilação verifica sintaxe e pode criar caches ignorados pelo Git. Não substitui testes, revisão documental ou busca de segredos. Os testes de integração exigem PostgreSQL exclusivo e as duas URLs de teste configuradas no ambiente. Testes ignorados por falta de configuração não comprovam integração.

## Uso e limitações

Uso exclusivo para estudo e portfólio. Resultados sintéticos não demonstram desempenho bancário. A fonte pública histórica descreve uma população específica e não comprova validade atual, brasileira ou temporal. Exclusão de demografia não garante equidade. Simulações não estimam efeitos causais; margens hipotéticas excluem custos e não representam lucro.

Não versionar dados brutos, previsões individuais, modelos serializados, credenciais ou relatórios com dados importados. O `.gitignore` não protege arquivos já rastreados. Consulte o procedimento de publicação antes de registrar a versão demonstrativa.
