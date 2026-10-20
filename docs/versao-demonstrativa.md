# Registro da versão demonstrativa — tarefa 18

Tecnologias: Markdown, Mermaid, Python, Pytest, Ruff e Git/GitHub. Dificuldade: baixa. Tempo previsto: 3 horas. Tempo realizado: não aferido. Versão proposta: 0.1.0.

Estado: documentação proposta. Nenhuma operação, alteração local, teste, inspeção de segredos, commit, tag ou publicação foi executado. A tarefa permanece pendente até a reunião das evidências de aceite.

## Reprodução desde clone limpo

1. Disponibilizar um clone limpo da revisão candidata em diretório separado, preservando o trabalho existente. Obter o clone é uma preparação externa; não integra os comandos de validação sem rede desta entrega.
2. Usar Python 3.11 ou 3.12 e ambiente isolado previamente preparado com o pacote candidato e dependências de desenvolvimento. Registrar executável, sistema e versões. Não utilizar inadvertidamente uma instalação editável apontando para outro checkout.
3. Confirmar que o clone não contém `.env`, dados ou artefatos herdados. A demonstração sintética não precisa desses arquivos nem de banco.
4. Executar separadamente os vetores abaixo, a partir da raiz do clone, conservando códigos de saída e resumo dos resultados.
5. Iniciar o Streamlit pelo vetor do README e revisar indicadores, previsão válida, JSON inválido, simulação com três limiares, limiares repetidos e ausência de aprovados. Confirmar fonte sintética e limitações visíveis.
6. Para aceite integral, preparar PostgreSQL exclusivo, fornecer as duas URLs de teste pelo ambiente e repetir a suíte com integração habilitada. Registrar testes ignorados e seus motivos; não interpretá-los como aprovados.
7. Registrar a revisão efetivamente validada. Qualquer alteração posterior relevante exige nova verificação correspondente.

Vetores não interativos, sem shell, downloads, instalações ou operações destrutivas:

```json
["python", "--version"]
```

```json
["python", "-m", "pip", "check"]
```

```json
["python", "-m", "compileall", "."]
```

```json
["python", "-m", "ruff", "check", "."]
```

```json
["python", "-m", "pytest"]
```

`pip check` verifica compatibilidade declarada dos pacotes instalados; não comprova lock ou identidade com o ambiente de origem. Compileall pode escrever caches. A revisão visual é complementar aos testes e não é executada pelo comando de validação da resposta.

## Revisão de segredos e conteúdo publicável

Revisar os arquivos rastreados e as diferenças candidatas. Conferir credenciais, URLs autenticadas, tokens, chaves privadas, dados brutos, identificadores, previsões individuais e artefatos com dados incorporados. Revisar também o histórico que será publicado; ignorar arquivos novos não remove conteúdo já rastreado ou previamente commitado.

Usar a ferramenta de detecção já aprovada e disponível no ambiente, quando existente, registrando nome, versão, escopo e resultado sem reproduzir segredos. A inspeção documental isolada não comprova ausência de segredos. Achados exigem tratamento antes da publicação; credenciais expostas requerem revogação pelo responsável.

Os seguintes vetores permitem inspeção local, sem alterar o repositório:

```json
["git", "status", "--short"]
```

```json
["git", "diff", "--check"]
```

```json
["git", "diff", "--stat"]
```

```json
["git", "ls-files"]
```

Esses comandos não são detectores de segredos. Resultados detalhados de inspeção devem permanecer em local restrito quando puderem conter material sensível.

## Registro incremental das etapas

A numeração abaixo segue as tarefas 1 a 18 identificadas na documentação fornecida. O roteiro inicial do MVP contém 11 macroetapas e permanece como planejamento histórico. Para todas as linhas, tempo realizado e hash do commit são não informados; as referências são evidências documentais disponíveis, não comprovantes de execução.

| Tarefa | Entrega | Tecnologias | Dificuldade | Previsto | Evidência disponível e conclusão pendente |
| --- | --- | --- | --- | --- | --- |
| 1 | Escopo | Markdown, Git | Baixa | 3 h | `escopo-mvp.md`; revisão e commit não confirmados |
| 2 | Estrutura | Python, setuptools, Pytest, Ruff | Baixa | 3 h | `arquitetura-e-desenvolvimento.md`, teste de importação; instalação e verificações pendentes |
| 3 | PostgreSQL | PostgreSQL, Docker Compose, SQLAlchemy, Alembic | Média | 4 h | `postgresql.md`; migração em banco vazio e permissões pendentes |
| 4 | Fonte pública | Markdown, Pandas | Baixa | 3 h | `fonte-publica.md`; licença, bytes e disponibilidade pendentes |
| 5 | Ingestão | Pandas, NumPy, xlrd, PostgreSQL | Média | 4 h | `ingestao.md`; leitura real e integração pendentes |
| 6 | Qualidade | Pandas, NumPy, Pytest | Média | 4 h | `qualidade-dados.md`; testes e relatório rastreável pendentes |
| 7 | Indicadores SQL | PostgreSQL, SQLAlchemy, Pandas | Média | 3 h | `indicadores-descritivos.md`; conciliação SQL/Pandas pendente |
| 8 | Exploração | Pandas, NumPy, SciPy, HTML/SVG | Média | 4 h | `analise-exploratoria.md`; execução e revisão dos agregados pendentes |
| 9 | Partições | Pandas, NumPy, Scikit-learn | Alta | 4 h | `particoes-e-vazamento.md`; manifesto real e testes pendentes |
| 10 | Referência | Scikit-learn, Pandas, Pytest | Média | 4 h | `modelo-referencia.md`; treino rastreável e baseline pendentes |
| 11 | Comparação | Scikit-learn, NumPy, Pytest | Alta | 4 h | `comparacao-modelos.md`; tabela e escolha verificadas pendentes |
| 12 | Calibração | Scikit-learn, NumPy, Pytest | Alta | 4 h | `calibracao-e-limiares.md`; política congelada verificável pendente |
| 13 | Interpretação | Pandas, NumPy, Scikit-learn | Alta | 4 h | `interpretacao-e-segmentos.md`; relatórios rastreáveis pendentes |
| 14 | Simulação | NumPy, Pandas, Pytest | Alta | 4 h | `simulacao-politicas.md`; hipóteses revisadas e execução pendentes |
| 15 | Interface | Streamlit, Scikit-learn, Pandas | Média | 4 h | `demonstracao-interativa.md`, `streamlit_app.py`; navegação e testes pendentes |
| 16 | Power BI | PostgreSQL, M, DAX, Power BI Desktop | Média | 4 h | `power-bi.md`; montagem, permissões e conciliação pendentes |
| 17 | Avaliação final | Python, Scikit-learn, GitHub Actions, PostgreSQL | Média | 3 h | `avaliacao-final.md`; workflow aprovado e avaliação real pendentes |
| 18 | Documentação e versão | Markdown, Mermaid, Git/GitHub | Baixa | 3 h | README, arquitetura e ficha propostas; clone limpo, revisão e publicação pendentes |

Ao encerrar cada etapa, acrescentar registro com tempo realizado, revisão validada, comando, código de saída, resumo, localização da evidência e hash confirmado do commit. Não inferir horas reais a partir das estimativas nem preencher resultados fictícios.

## Publicação no GitHub

Após aplicar e revisar os arquivos propostos, reunir as evidências de reprodução e segurança. Selecionar explicitamente os arquivos documentais, preservando mudanças anteriores e o histórico. Criar um commit incremental com a mensagem proposta e registrar seu hash real.

Com remoto e acesso configurados, publicar o commit e registrar uma release demonstrativa associada à revisão validada. Usar `v0.1.0` somente se essa tag estiver disponível e corresponder ao conteúdo revisado; não mover uma tag existente. Publicação e comandos de escrita não são executados nem fazem parte da validação desta resposta.

As notas da release devem informar: interface sintética local, funcionalidades disponíveis, dependências, instruções do README, verificações efetivamente executadas, testes ignorados, ausência de métricas reais confirmadas e pendências do Power BI. Não anunciar conclusão do MVP ou superioridade preditiva sem as respectivas evidências.

## Evidências de aceite

| Evidência | Estado atual |
| --- | --- |
| URL do repositório e revisão candidata | Não informadas |
| Execução em clone limpo e ambiente registrado | Não executada |
| Compileall, Ruff e Pytest com códigos de saída | Não executados |
| Integração PostgreSQL habilitada | Não confirmada |
| Fluxo Streamlit revisado | Não executado |
| Inspeção de segredos e histórico, com escopo registrado | Não executada |
| Tempos realizados por etapa | Não aferidos |
| Hashes dos commits incrementais | Não informados |
| Tag, revisão e URL da release no GitHub | Não registradas |

Critério de conclusão: preencher as evidências reais, resolver falhas impeditivas e registrar a versão demonstrativa no GitHub. A avaliação final real e a montagem do Power BI devem permanecer explicitamente identificadas como pendências caso não integrem a demonstração publicada.
