# Análise exploratória reproduzível — tarefa 8

Tecnologias: Python, Pandas, NumPy, SciPy, HTML/SVG e Pytest. Dificuldade: média. Estimativa: quatro horas.

## Entrada e execução

O módulo `credit_risk.analysis.eda` adiciona exploração independente, sem alterar ingestão, consultas SQL ou dados persistidos. Não exige PostgreSQL, novas dependências, downloads ou serviços externos.

A API `analyze(frame, dataset_version)` recebe os registros aceitos por `treat_frame`, com os nomes originais. A CLI recebe um CSV local UTF-8 com as 25 colunas originais na ordem de `COLUMNS` e aplica o tratamento existente antes da exploração. Esse CSV deve ser uma exportação rastreável de uma fonte previamente aprovada. A CLI não lê ZIP/XLS nem recebe diretamente os registros JSONB do banco. Não enviar categorias já tratadas à CLI: ela espera o contrato bruto.

Executar posteriormente, no ambiente preparado, com vetor de argumentos sem shell:

`["python", "-m", "credit_risk.analysis.eda", "data/uci.csv", "--dataset-version", "uci-350:versao-local", "--output", "artifacts/eda/execucao-001"]`

O diretório final deve ser novo. A execução falha se ele já existir, preservando resultados anteriores. Uma falha de escrita pode deixar uma saída incompleta; a conclusão exige os dois arquivos. Os artefatos ficam fora do Git conforme o gitignore existente.

## Resultados

- `summary.json`: JSON estrito com versão analítica, versão declarada dos dados, SHA-256 dos bytes CSV, versões de Python/Pandas/NumPy, qualidade agregada, volume aceito e limitações.
- `report.html`: relatório autossuficiente em português, com gráficos SVG de contagens do alvo, ausências, histogramas monetários e taxas por grupo. A seção expansível contém todas as estatísticas e correlações. Abrir localmente em navegador; não há recursos remotos.

Não são exportados identificadores, demografia ou linhas individuais. Grupos pequenos são apresentados com denominadores para estudo local; esta entrega não estabelece anonimização para divulgação pública.

## Definições e escolhas

A prevalência é a média do alvo binário entre registros aceitos. São apresentadas as duas classes, inclusive contagens zero, e a razão entre quantidade minoritária e majoritária. Sem registros, taxas e essa razão ficam indisponíveis. Uma única classe é indicada explicitamente e não impede a descrição.

Os 13 atributos monetários recebem contagem observada, mínimo, quartis com interpolação linear, mediana, máximo, média, desvio padrão amostral e histogramas de dez intervalos de mesma largura. Ausências são ignoradas nesses cálculos e contabilizadas separadamente nos 19 atributos financeiros. Zeros, valores negativos e extremos são preservados. Variáveis totalmente ausentes não geram barras; estatísticas ficam nulas. Histogramas de variáveis constantes usam os limites determinados pelo NumPy.

Padrões são taxas por categoria de cada PAY e pelas faixas fixas de LIMIT_BAL: abaixo de 100.000, de 100.000 inclusive a 300.000 exclusive, 300.000 ou mais e ausente. Cada grupo informa observações, inadimplentes e taxa. Categorias PAY não documentadas permanecem explícitas, sem inventar significado ou distância ordinal. As faixas não são recomendações de concessão.

Pearson e Spearman são calculados para cada par entre atributos monetários e alvo. O alvo recebe o nome `defaulted` somente na tabela de correlações. Cada par informa sua própria quantidade de observações completas. Menos de três pares ou qualquer variável constante produz correlação indisponível. Não são calculados valores-p nem selecionadas associações por significância. PAY não participa da matriz numérica.

O relatório é determinístico para os mesmos bytes de entrada, versão declarada, código e ambiente. Não utiliza sorteio ou horário de execução. O SHA-256 identifica o CSV, não substitui os hashes e as evidências documentais da ingestão. Registros rejeitados não entram nas estatísticas; suas contagens e motivos agregados ficam registrados, tornando visível a seleção introduzida pelo tratamento. A API isolada pressupõe que o chamador já aplicou esse tratamento.

## Interpretação e limitações

Associação não demonstra causalidade: uma taxa maior por faixa ou código PAY não demonstra que alterar limite ou comportamento causaria uma mudança no desfecho. Confundimento, seleção, fatores não medidos e dependências entre atributos podem explicar padrões. Não se estima efeito de políticas.

A fonte descreve clientes existentes em Taiwan em 2005. Não se presume representatividade atual ou brasileira, nem generalização temporal com uma única referência. O instante de disponibilidade dos atributos é uma hipótese; o conceito de inadimplência segue a fonte. Limite não equivale automaticamente a exposição. Excluir demografia não garante ausência de vieses. Grupos pequenos têm taxas instáveis; não há inferência populacional ou intervalos de confiança nesta entrega.

Ao iniciar modelagem, fixar partições antes da exploração que orientará escolhas e restringir essa exploração ao treino. Não usar resultados do teste para escolher atributos, modelos ou limiares. Este módulo não cria partições e não impede que um chamador forneça dados inadequados.

## Validação e conclusão

Vetores não interativos para execução posterior, separadamente:

- `["python", "-m", "compileall", "."]`
- `["python", "-m", "pytest", "tests/test_eda.py"]`

Os testes sintéticos verificam estatísticas conhecidas, correlações, denominadores, fronteiras das faixas, códigos não documentados, ausências, alvo inválido, amostra vazia, classe única, preservação da entrada e escape HTML. A execução integral é repetida em dois diretórios e os bytes dos artefatos são comparados; também verifica rejeição auditada e proteção contra sobrescrita.

Critérios de conclusão: testes aprovados, execução integral sobre a versão local aprovada da fonte, revisão dos agregados e limitações e commit incremental confirmado. Esta resposta fornece somente arquivos completos propostos. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. Não há resultados observados sobre dados reais nesta entrega. A mensagem de commit é uma proposta; compileall verifica sintaxe quando executado e não substitui os testes.
