# Escopo e critérios de aceite do MVP

## 1. Objetivo

Construir uma demonstração reproduzível de análise e previsão de inadimplência, com exploração de dados, avaliação de modelos e simulação de políticas de crédito. O projeto tem finalidade educacional e de portfólio; não será utilizado para decisões reais sobre pessoas.

Esta etapa entrega apenas a definição do escopo. Não inclui implementação de pipelines, treinamento, dashboards ou publicação.

## 2. Público-alvo

- Analistas de risco interessados em padrões de inadimplência e comparação de políticas.
- Profissionais de dados interessados em qualidade, modelagem e avaliação reproduzível.
- Avaliadores de portfólio interessados em evidências de engenharia de software e análise aplicada.

## 3. Problema preditivo

- Unidade de análise: um cliente de uma carteira de crédito por data de referência.
- Momento da decisão: fechamento do mês de referência, após a disponibilidade das informações daquele mês.
- Decisão simulada: conceder ou manter um limite hipotético para o período seguinte em uma carteira existente.
- Horizonte: o mês imediatamente seguinte à data de referência.
- Alvo: variável binária, sendo 1 a ocorrência de inadimplência no mês seguinte e 0 sua ausência, conforme definição documentada pela fonte.
- Saída: probabilidade estimada de inadimplência entre 0 e 1.

O conceito de inadimplência deverá reproduzir a definição da base selecionada. Não será presumida equivalência com atraso superior a 90 dias. A aplicação a novos solicitantes, sem histórico na carteira, está fora do escopo.

## 4. Dados permitidos e elegibilidade

Usar uma única base pública anonimizada que contenha histórico financeiro anterior ao desfecho e alvo compatível com o horizonte definido. Dados sintéticos poderão ser usados apenas em testes, identificados explicitamente.

Antes da ingestão, registrar em catálogo: origem, endereço da fonte, licença ou condições de uso, data de obtenção, versão ou hash do arquivo, população, período, unidade de análise, definição do alvo e limitações de representatividade. A fonte ainda será selecionada; esta etapa não declara disponibilidade nem autorização de uma base específica.

A seleção será aceita somente se houver evidência documental da compatibilidade do alvo e da sequência temporal entre atributos e desfecho. Se essa evidência não existir, a fonte será rejeitada.

Não coletar nomes, documentos, contatos, endereços ou outros identificadores pessoais diretos. Identificadores técnicos serão excluídos dos preditores. Atributos demográficos serão excluídos dos preditores no MVP; sua eventual utilização em análises agregadas exigirá justificativa documentada. Essa exclusão não constitui garantia de ausência de vieses.

## 5. Funcionalidades essenciais

### F01 — Ingestão e qualidade

Importar arquivo local da fonte selecionada usando Python e Pandas, validar esquema, tipos, domínio do alvo, duplicidades e valores ausentes, e persistir dados tratados em PostgreSQL. Manter rastreabilidade entre versão dos dados e execução. Dados brutos não deverão ser versionados no Git.

### F02 — Análise exploratória

Apresentar volume de registros, prevalência de inadimplência, distribuição de variáveis, ausência de dados e taxas de inadimplência por faixas financeiras. Informar tamanho dos grupos e evitar interpretações causais.

### F03 — Modelagem e avaliação

Comparar um baseline DummyClassifier, regressão logística e um modelo de árvores do Scikit-learn. Executar imputação, codificação e demais transformações dentro de pipelines ajustados exclusivamente no treino.

Reservar conjuntos de treino, validação e teste. Quando houver datas suficientes, utilizar divisão temporal. Caso contrário, utilizar divisão estratificada reproduzível e declarar que ela não mede generalização temporal. Um mesmo cliente não poderá aparecer em conjuntos distintos quando houver múltiplos registros por cliente.

Selecionar modelo, hiperparâmetros e limiar usando apenas treino e validação. Consultar o teste somente para a avaliação final da versão escolhida.

### F04 — Simulação de políticas

Simular aprovação quando a probabilidade estimada for menor que um limiar configurável. Comparar pelo menos três limiares definidos antes da avaliação final e apresentar taxa de aprovação, inadimplência observada entre aprovados e quantidade de inadimplentes recusados.

Quando não houver aprovados, apresentar a taxa de inadimplência entre aprovados como indisponível, sem divisão por zero. A simulação utilizará os desfechos históricos da amostra e não representará um experimento causal ou resultado esperado em produção.

### F05 — Visualização

Disponibilizar exploração interativa em Streamlit e exportações agregadas em CSV para Power BI. Os painéis deverão identificar fonte, período, versão do modelo, tamanho da amostra e limitações. O fluxo principal deverá funcionar sem licença do Power BI.

## 6. Métricas e regras de avaliação

- Métrica principal: average precision, calculada pelo Scikit-learn, com inadimplência como classe positiva.
- Métricas complementares: ROC-AUC, precisão, recall, F1, matriz de confusão, Brier score e curva de calibração.
- Referências obrigatórias: prevalência do alvo e desempenho do DummyClassifier nos mesmos conjuntos.
- Políticas: taxa de aprovação, taxa observada de inadimplência entre aprovados e proporção de inadimplentes recusados.

Registrar sementes, tamanhos das partições, versões das dependências e configuração de cada execução. Garantir ambas as classes nas partições de avaliação; caso contrário, interromper a avaliação e registrar a insuficiência dos dados.

O modelo será considerado superior ao baseline somente se sua average precision no teste for maior que a do baseline. Se isso não ocorrer, o resultado negativo será documentado, sem alegação de superioridade. A conclusão técnica do MVP exige avaliação correta e reproduzível, não um ganho mínimo arbitrário de desempenho.

## 7. Exclusões

- Uso operacional, concessão real, integração bancária e consultas a bureaus.
- Dados privados, pessoais identificáveis ou obtidos sem condições de uso verificadas.
- Previsão em tempo real, autenticação de usuários e operação multicliente.
- Estimativas de lucro, perda esperada ou capital regulatório sem exposição, recuperação e custos documentados.
- Inferência causal, certificação regulatória e alegação de equidade ou validade para outras populações.
- Monitoramento de produção, retreinamento automático e infraestrutura de alta disponibilidade.

## 8. Critérios de aceite verificáveis

| ID | Evidência exigida |
| --- | --- |
| A01 | Catálogo da fonte preenchido, com condições de uso e definição do alvo verificadas. |
| A02 | Dicionário de dados contendo tipos, significado, disponibilidade temporal e elegibilidade de cada preditor. |
| A03 | Relatório de qualidade com contagens de entradas, exclusões, duplicidades e valores ausentes. |
| A04 | Partições reproduzíveis, sem sobreposição de clientes e sem atributos posteriores à decisão. |
| A05 | Baseline e dois modelos avaliados nas mesmas partições, com pipelines ajustados somente no treino. |
| A06 | Relatório final com métricas, comparação com baseline, configuração, limitações e resultado da hipótese de superioridade. |
| A07 | Simulação de pelo menos três limiares, com denominadores e tratamento de conjuntos sem aprovados. |
| A08 | Dashboard Streamlit navegável e CSV agregado acompanhado de instruções de uso no Power BI. |
| A09 | Testes automatizados de esquema, alvo, separação das partições, probabilidades e cálculos da simulação; verificações de estilo aprovadas. |
| A10 | Instruções reproduzíveis de execução, migrações do banco e histórico de commits incrementais sem dados brutos nem segredos. |

## 9. Etapas diárias propostas

Cada etapa corresponde a uma entrega incremental. As estimativas são de esforço e poderão ocupar mais de um dia conforme a disponibilidade.

| Etapa | Entrega | Tecnologias | Dificuldade | Horas | Conclusão |
| --- | --- | --- | --- | --- | --- |
| 1 | Escopo do MVP | Markdown, Git | Baixa | 3 | Documento com público, alvo, horizonte, decisão, requisitos, exclusões, métricas e aceite. |
| 2 | Estrutura e verificações | Python, Pytest, Ruff, GitHub Actions | Baixa | 3 | Projeto importável e verificações automatizadas configuradas. |
| 3 | Seleção da fonte e catálogo | Pandas, Markdown | Média | 4 | A01 e A02 atendidos. |
| 4 | Ingestão e qualidade | Pandas, NumPy, Pytest | Média | 4 | A03 atendido e validações testadas. |
| 5 | Persistência | PostgreSQL, SQLAlchemy, Alembic, Docker Compose | Média | 4 | Migração e carga reproduzíveis. |
| 6 | Exploração | Pandas, NumPy, SciPy | Média | 4 | Relatório exploratório com taxas, distribuições e limitações. |
| 7 | Partições e baseline | Scikit-learn, Pytest | Média | 4 | A04 atendido e baseline registrado. |
| 8 | Modelos e avaliação | Scikit-learn | Alta | 6 | A05 e A06 atendidos. |
| 9 | Políticas de crédito | Pandas, NumPy, Pytest | Média | 4 | A07 atendido. |
| 10 | Visualização | Streamlit, Power BI | Média | 5 | A08 atendido. |
| 11 | Integração e documentação | Pytest, Ruff, GitHub Actions, Git | Média | 4 | A09 e A10 atendidos. |

## 10. Processo de entrega e conclusão desta etapa

Cada implementação futura deverá preservar o trabalho anterior, registrar a funcionalidade entregue, executar verificações apropriadas e produzir um commit incremental. Publicação no GitHub dependerá de ambiente e acesso configurados; um commit ou envio só poderá ser declarado após sua execução confirmada.

A etapa 1 é atendida pela entrega deste documento. Nenhuma operação, validação executada, alteração efetiva no repositório ou publicação no GitHub é declarada nesta resposta. O comando de validação fornecido verifica a compilação dos arquivos Python existentes; a aceitação deste documento depende da conferência de seu conteúdo.
