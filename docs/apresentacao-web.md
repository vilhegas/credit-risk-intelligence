# Apresentação web: conteúdo e evidências

## Escopo e estado desta entrega

Este documento implementa a tarefa 1 do plano aprovado de 12 tarefas, junto com [o contrato de resultados](contrato-resultados-web.md). A entrega é documental: não cria frontend, exportadores, resultados, infraestrutura ou evidências de execução dos testes Python.

Referência para as próximas execuções, mantendo entregas e commits independentes:

| Tarefa | Entrega prevista |
| --- | --- |
| 1 | Conteúdo, evidências e contratos públicos — estes dois documentos |
| 2 | Fundação Next.js, TypeScript e Tailwind em `web/` |
| 3 | Carregamento e validação dos resultados |
| 4 | Exportação e revisão de evidências publicáveis |
| 5 | Sistema visual e navegação responsiva |
| 6 | Visão geral para recrutadores |
| 7 | Análise exploratória |
| 8 | Modelos e interpretação |
| 9 | Simulação de políticas |
| 10 | Metodologia e rastreabilidade |
| 11 | Qualidade integrada e automação do frontend |
| 12 | Documentação de publicação manual na Vercel e aceite |

O código Python existente será preservado. Novos adaptadores e frontend serão planejados em `web/`. A publicação consumirá agregados revisados, sem exigir PostgreSQL, Docker ou execução de Python na Vercel. Não haverá previsão individual na primeira versão web; essa funcionalidade permanece na demonstração Streamlit.

## Como interpretar as evidências

Nesta revisão, “implementado” significa que há código inspecionado para a funcionalidade. Um teste existente demonstra o comportamento que se pretende verificar, mas sua presença não comprova aprovação. Uma descrição documental também não comprova execução. Resultados publicáveis exigem artefatos e procedência conforme o contrato.

| Categoria | Situação constatada | Tratamento público |
| --- | --- | --- |
| Implementação | Módulos Python e Streamlit presentes | Descrever capacidades com referência ao código |
| Demonstração sintética | Gerador e serviços implementados; nenhum novo cálculo executado nesta entrega | Identificar dados artificiais; publicar números somente após exportação verificada |
| Resultados reais | Não foram encontrados artefatos de resultados reais versionados; o README não confirma avaliação final real | Exibir “Resultado real ainda indisponível” |
| Metadados documentais da fonte | População, dimensão esperada, período e licença indicados em `fonte-publica.md` | Apresentar como descrição da fonte, sem confundir com medidas da execução local |
| Testes | Suíte presente, sem execução nesta tarefa | Informar cobertura existente; não afirmar aprovação ou percentual de cobertura |
| Frontend e publicação | Etapas futuras | Não anunciar site ou deployment concluído |

O escopo dessas constatações é o material versionado inspecionado. Não se presume que arquivos locais ignorados, caches ou uma execução anterior não registrada constituam evidência publicável.

## Mapa de afirmações e evidências

Os caminhos de código abaixo são relativos à raiz do repositório; os links abrem as implementações ou documentos correspondentes.

| ID | Afirmação pública permitida | Evidência | Limite da afirmação |
| --- | --- | --- | --- |
| A01 | O projeto implementa ingestão local de ZIP/XLS com validação e metadados de procedência | [ingestion/uci.py](../src/credit_risk/ingestion/uci.py): `read_archive`, `Provenance`, `ingest_uci`; [testes](../tests/test_ingestion.py) | Não comprova obtenção da fonte real nem carga em banco |
| A02 | O tratamento preserva ausências, registra rejeições, duplicatas, conflitos e códigos não documentados | [quality.py](../src/credit_risk/preprocessing/quality.py): `treat_frame`; [testes](../tests/test_quality.py) | Não equivale a anonimização ou integração automática com a ingestão |
| A03 | Há consultas SQL agregadas por execução | [indicators.py](../src/credit_risk/analysis/indicators.py): `describe_run`; [testes](../tests/test_indicators.py) | Exigem PostgreSQL; o site poderá usar exportações locais alternativas |
| A04 | A exploração calcula distribuições, ausências, taxas por grupos e correlações | [eda.py](../src/credit_risk/analysis/eda.py): `analyze`, `main`; [testes](../tests/test_eda.py) | Associações descritivas; não há conclusão real sem artefato |
| A05 | A separação implementa isolamento por cliente e opção temporal sob condições explícitas | [splitting.py](../src/credit_risk/modeling/splitting.py): `split_data`; [testes](../tests/test_splitting.py) | A referência temporal única da fonte UCI não demonstra generalização entre safras |
| A06 | Os pipelines de referência usam 19 atributos financeiros, imputação, escala, codificação categórica, regressão logística e Dummy | [reference.py](../src/credit_risk/modeling/reference.py): `build_pipeline`, `train_reference`; [FEATURES](../src/credit_risk/ingestion/uci.py); [testes](../tests/test_reference.py) | Ajuste no treino; métricas do relatório são de validação, não do teste final |
| A07 | A comparação avalia três configurações logísticas, três árvores e Dummy em holdout | [comparison.py](../src/credit_risk/modeling/comparison.py): `CANDIDATES`, `compare_models`; [testes](../tests/test_comparison.py) | Seleção por AP de validação, incluindo Dummy; não há validação cruzada nem superioridade final comprovada |
| A08 | Há seleção de calibração sigmoid ou identidade e de limiar sujeito a restrições | [calibration.py](../src/credit_risk/modeling/calibration.py): `select_policy`, `Policy`; [testes](../tests/test_calibration.py) | Calibração e seleção recebem clientes disjuntos; reutilizar seleção para calibração e limiar pode gerar otimismo |
| A09 | A interpretação inclui permutação de atributos e avaliação por segmentos | [interpretation.py](../src/credit_risk/modeling/interpretation.py): `permutation_report`, `segment_report`; [testes](../tests/test_interpretation.py) | Não é SHAP, explicação causal ou comprovação de equidade; suficiência estatística não garante privacidade |
| A10 | A simulação compara limiares com hipóteses explícitas de exposição, LGD e receita | [policies.py](../src/credit_risk/simulation/policies.py): `simulate_policies`; [testes](../tests/test_simulation.py) | Margem antes de custos não é lucro; cenários não estimam efeito causal |
| A11 | Há avaliação final de previsões congeladas com bootstrap pareado e reserva de diretório | [final_evaluation.py](../src/credit_risk/modeling/final_evaluation.py): `evaluate_once`; [testes](../tests/test_final_evaluation.py) | Reserva é local; hashes declarados não atestam o vínculo entre modelo, dados e previsões |
| A12 | O Streamlit oferece indicadores, previsão financeira e comparação de políticas sintéticas | [streamlit_app.py](../streamlit_app.py); [demo.py](../src/credit_risk/presentation/demo.py); [testes](../tests/test_demo.py) | Implementação presente; execução e desempenho real não confirmados nesta tarefa |
| A13 | Há integração Power BI especificada em SQL, M e DAX | [power-bi.md](power-bi.md) e arquivos em `powerbi/` | Montagem e validação no Desktop pendentes; não há painel validado comprovado |
| A14 | Existem testes e workflow de validação | [tests/](../tests/), [workflow](../.github/workflows/validation.yml), [README](../README.md) | Workflow exige runner próprio e PostgreSQL; testes ignorados não são integração aprovada |

### Particularidades da demonstração sintética

`demonstration_frame` gera 400 registros antes da divisão, com semente 42. As constantes presentes no código são `demo-synthetic-v1` e `demo-logistic-synthetic-v1`. São identificadores de implementação, não resultados observados.

`_bundle` divide os dados, ajusta a regressão logística no treino e produz probabilidades na validação. `indicators` e `explore_policies` usam essa validação. Portanto, nenhum cartão deve usar 400 como seu denominador sem conferir a população correspondente. A demonstração não utiliza automaticamente o vencedor de `compare_models` nem a política calibrada de `select_policy`.

As seis colunas PAY compartilham o vetor artificial de atraso do gerador, e o alvo é sorteado a partir de uma probabilidade definida nesse código. Associações encontradas nessa base refletem sua construção; não são descobertas sobre clientes reais. Não atribuir datas observadas, moeda NT$ ou representatividade UCI a esses dados.

## Estrutura editorial e interação

| Rota planejada | Pergunta do visitante | Conteúdo e evidências | Ausência de resultado |
| --- | --- | --- | --- |
| `/` | Qual problema foi tratado e o que foi construído? | Equilíbrio aprovação/risco, fluxo do projeto, capacidades A01–A14, indicadores referenciados | Resumir o estágio do projeto sem cartões fictícios |
| `/analise-exploratoria` | Como os dados foram examinados? | Qualidade, alvo, distribuições, grupos PAY/limite e correlações; A02–A04 | Explicar análise disponível no código e motivo da indisponibilidade dos números |
| `/modelos` | Como as decisões técnicas foram avaliadas? | Pipelines, baseline, comparação, calibração, permutação, segmentos e avaliação final; A05–A09, A11 | Separar método implementado de desempenho não confirmado |
| `/simulacao` | Como limiares e hipóteses alteram os indicadores? | Controles sobre grade de limiares e exposição constante, LGD e receita; A10 | Desabilitar cálculo sem pacote válido; nunca substituir por resultados inventados |
| `/metodologia` | Como reproduzir e avaliar criticamente o trabalho? | Fonte, partições, ambiente, evidências, arquitetura e limitações | Exibir pendências e condições para reprodução |

A visão geral deve permitir uma leitura breve e oferecer aprofundamento nas demais páginas. Toda conclusão quantitativa deve apontar para o artefato, a partição e as métricas que a sustentam. Resultados negativos permanecem apresentados. Filtros devem representar apenas dimensões disponíveis nos agregados; histogramas não permitem reconstruir registros ou aplicar filtros individuais exatos.

Origem, partição, unidade e limitações devem acompanhar cartões, tabelas, gráficos e downloads. A identificação sintética não pode depender apenas de tooltip ou da página de metodologia. A interface futura deverá oferecer teclado, foco visível, contraste, tabelas alternativas aos gráficos, responsividade e estados distintos de ausência legítima e erro de carregamento.

## Regras de comunicação

- Utilizar “implementa”, “calcula” ou “permite comparar” para capacidades do código; reservar “obteve” e “demonstrou” para execuções documentadas.
- Não anunciar AUC, AP, economia, lucro, melhoria, precisão, tamanho de amostra tratada ou modelo vencedor sem evidência correspondente.
- Não tratar AP como área trapezoidal sob a curva precisão-recall; preservar a definição `average_precision_score` da implementação.
- Identificar validação usada para escolha; não apresentá-la como estimativa final independente.
- Não inferir ausência de vieses da exclusão de demografia. Não anunciar validade brasileira, atual, temporal, regulatória ou operacional.
- Explicar que a fonte histórica descreve clientes existentes; recusados simulados não representam solicitantes historicamente recusados.
- Não converter limite em exposição automaticamente; não apresentar montantes de cenário com desfechos históricos como perdas realizadas.
- Não criar um resultado “real” pela mera troca do rótulo de uma demonstração sintética.

## Conciliação com documentação anterior

O README e [versao-demonstrativa.md](versao-demonstrativa.md) registram pendências de execução; elas não devem ser convertidas em aceite pelo site. [fonte-publica.md](fonte-publica.md) contém a observação histórica de ausência de `xlrd`, mas a dependência já está declarada em [pyproject.toml](../pyproject.toml). [ficha-demonstracao.md](ficha-demonstracao.md) registra ausência dos valores literais das versões, hoje legíveis em `demo.py` e citados acima. Esses documentos históricos não foram alterados nesta tarefa.

`eda.render_html` e `eda.LIMITATIONS` contêm contexto específico da UCI. Um futuro exportador que usar `analyze` sobre dados sintéticos deverá fornecer contexto editorial correto e registrar essa adaptação; não copiar automaticamente o texto UCI para a demonstração. As estatísticas calculadas continuam vinculadas à entrada efetivamente usada.

## Aceite documental e próximos passos

A tarefa 1 entrega inventário, mapa de afirmações, estrutura editorial e contrato normativo. Schemas executáveis, exportadores, cálculo de resultados, testes do frontend e publicação pertencem às tarefas posteriores. A revisão desta entrega deve conferir referências locais, correspondência com símbolos do código e ausência de números apresentados como resultados sem execução. Nenhuma aprovação dos testes Python é alegada.

Na tarefa 4, somente agregados selecionados e revisados poderão entrar no pacote público. Isso estabelece uma exceção delimitada à orientação geral do README de não versionar relatórios com dados importados: relatórios originais, dados e previsões continuam restritos; o pacote web sanitizado depende de revisão explícita de procedência e privacidade conforme o contrato. Não copiar relatórios completos para `public/`.
