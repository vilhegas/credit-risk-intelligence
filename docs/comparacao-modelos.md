# Comparação com busca limitada — tarefa 11

Tecnologias: Python, Pandas, NumPy, Scikit-learn e Pytest. Dificuldade: alta. Estimativa: quatro horas.

## Uso e orçamento

A API `credit_risk.modeling.comparison.compare_models(split, seed=42)` recebe a saída rastreável de `split_data`. Retorna os modelos ajustados, o modelo selecionado e um relatório agregado com serialização estrita em `report_json()`. Não realiza operações de entrada e saída. Importar o módulo não treina modelos.

```python
from credit_risk.modeling.comparison import compare_models
from credit_risk.modeling.splitting import split_data

split = split_data(frame_tratado, "versao-rastreavel")
result = compare_models(split)
report_json = result.report_json()
performance_table = result.report["table"]
selected_model = result.selected
```

A busca fixa três regressões logísticas com C igual a 0,1, 1 e 10 e três árvores DecisionTreeClassifier com profundidades máximas 3, 6 e 10, todas com pelo menos dez observações por folha. Incluindo DummyClassifier, são sete ajustes. Não existem repetições adaptativas, paralelismo, busca de limiar ou ampliação automática do orçamento. As árvores possuem no máximo 1.024 folhas pela profundidade; o custo também depende do tamanho dos dados e do vocabulário categórico.

A referência C=1 e Dummy são reutilizados de `train_reference`. Os outros candidatos clonam o pipeline, removendo todo estado aprendido. Mantêm a seleção dos 19 atributos e o tratamento existente de ausências e categorias PAY. Escala numérica é mantida também nas árvores para preservar o processamento; não é necessária para a interpretação da árvore. Cada pipeline é ajustado exclusivamente no treino. Falhas de ajuste, probabilidades inválidas ou avisos de não convergência interrompem a comparação, sem descartar candidatos silenciosamente.

## Validação e seleção

A comparação usa uma única validação holdout já definida. Para `stratified_client`, preserva a separação estratificada por cliente. Para `temporal`, preserva a ordem, as fronteiras e o expurgo feitos por `split_data`. Não reconstrói folds, não embaralha períodos e não acessa `split.test`. Metadados incorretos não podem tornar seguras partições construídas manualmente; o contrato exige a saída original de `split_data`.

A tabela contém ROC-AUC, average precision, precisão, recall, quantidade de positivos previstos, parâmetros e diferenças de average precision frente a C=1 e Dummy. Inadimplência é a classe positiva. Precisão e recall usam probabilidade maior ou igual a 0,5; o limiar é fixado antes da comparação. Precisão sem positivos previstos é registrada como zero, acompanhada da contagem zero. Nenhuma política de concessão é otimizada nesta tarefa.

Seleciona-se a maior average precision, incluindo Dummy. Em empate exato, prefere-se C=1, depois Dummy e depois os demais candidatos na ordem declarada no relatório. Essa regra conserva a referência quando a busca não oferece ganho. Diferenças numéricas positivas pequenas não constituem evidência de significância estatística. Não são produzidos testes inferenciais nem alegações de superioridade final.

O modelo selecionado permanece ajustado somente no treino. A validação participa da seleção e suas métricas podem ser otimistas. O teste final continua reservado para outra etapa; não repetir escolhas após consultar seus resultados. A divisão estratificada da referência comum UCI não mede generalização temporal. As limitações da fonte e do modelo de referência continuam aplicáveis.

## Reprodução, validação e conclusão

O relatório registra versão da comparação, semente, orçamento, configurações, ordem de desempate, tamanhos, prevalências e metadados da divisão. Inclui o relatório existente da referência, com versões do ambiente. Conservar o JSON posteriormente em `artifacts/`, junto à identidade dos dados e do código; a API não grava resultados nem inclui previsões individuais. Reprodução exige os mesmos dados, partições, código e ambiente.

Vetores não interativos para execução posterior, separadamente e sem shell:

- `["python", "-m", "compileall", "."]`
- `["python", "-m", "pytest", "tests/test_comparison.py", "tests/test_reference.py", "tests/test_splitting.py"]`

Os testes sintéticos verificam reprodução, métricas calculadas independentemente, seleção por average precision, empate sem melhoria, isolamento do teste, preservação do treino e processamento ajustado independentemente em cada candidato. Também verificam falhas para método desconhecido, semente inválida e classe única na validação.

Critérios de conclusão: testes aprovados, tabela gerada sobre partições rastreáveis da fonte aprovada, escolha e limitações revisadas e commit incremental confirmado. Esta resposta contém somente arquivos completos propostos. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. Não há métricas observadas em dados reais. A mensagem de commit é uma proposta; compileall verifica sintaxe quando executado e não substitui os testes comportamentais.
