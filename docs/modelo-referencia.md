# Pipeline e modelo de referência — tarefa 10

Tecnologias: Python, Pandas, NumPy, Scikit-learn e Pytest. Dificuldade: média. Estimativa: quatro horas.

## Uso

A API `credit_risk.modeling.reference.train_reference(split, seed=42)` recebe a saída existente de `split_data`. Retorna `ReferenceResult`, com pipelines `logistic` e `dummy`, relatório agregado `report` e serialização JSON estrita por `report_json()`. Não acessa arquivos, banco, rede ou conjunto de teste. A importação não treina modelos.

Exemplo para execução posterior no ambiente preparado:

```python
from credit_risk.modeling.splitting import split_data
from credit_risk.modeling.reference import train_reference, default_probability

split = split_data(frame_tratado, "versao-rastreavel")
result = train_reference(split)
comparacao = result.report_json()
probabilidades = default_probability(result.logistic, split.validation.X)
```

O chamador deve conservar a entrada rastreável e as partições. A API verifica posições disjuntas e alinhamento de índices entre atributos e alvo; o isolamento de clientes e as regras temporais são responsabilidade de `split_data`. Não fornecer partições montadas manualmente sem essas garantias.

## Transformações e avaliação

Cada estimador possui seu próprio Pipeline. A adaptação determinística dos tipos anuláveis fica em FunctionTransformer. O ColumnTransformer seleciona exclusivamente os 19 atributos financeiros: valores monetários recebem imputação pela mediana e StandardScaler; PAY recebe imputação pela categoria mais frequente e OneHotEncoder. Categorias desconhecidas na validação são ignoradas pelo codificador. Códigos não documentados continuam categorias explícitas, sem interpretação ordinal. Colunas inteiramente ausentes no treino são preservadas com o comportamento de preenchimento de SimpleImputer e keep_empty_features=True; nenhuma estatística da validação é utilizada para recuperá-las.

ID, demografia, alvo e colunas adicionais são descartados pela seleção explícita. Todos os parâmetros aprendidos, incluindo medianas, frequências, vocabulários e escala, são ajustados somente em `train.X`. A validação usa apenas predict_proba. A regressão logística usa L2, C=1, solver lbfgs e até 2.000 iterações; aviso de não convergência interrompe a entrega do resultado. Não há ajuste automático de hiperparâmetros ou de limiares.

DummyClassifier usa strategy=prior: sua probabilidade constante é a prevalência observada no treino. Ambos os modelos são avaliados nas mesmas linhas de validação, exigindo ambas as classes em treino e validação. São registradas average precision, ROC-AUC e Brier score, além das prevalências, tamanhos, versões, configuração, semente e metadados da separação. As probabilidades são verificadas quanto a dimensão, finitude e intervalo entre zero e um.

A diferença de average precision e o indicador logistic_above_dummy descrevem exclusivamente a validação. Um resultado negativo permanece registrado. Não há declaração de superioridade final, seleção de modelo ou consulta ao teste. Matriz de confusão, métricas dependentes de limiar, curva de calibração e comparação final permanecem para a etapa de avaliação. O relatório fica em memória; o chamador pode conservá-lo posteriormente em artifacts/, sem versionar linhas individuais ou modelos com dados embutidos.

Reprodução pressupõe mesma entrada, partições, código e ambiente. A semente não garante identidade numérica entre versões, plataformas ou bibliotecas matemáticas diferentes. A amostra histórica e a referência comum não comprovam generalização temporal, causalidade, equidade ou adequação operacional.

## Validação e conclusão

Vetores não interativos para execução posterior, separadamente e sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_reference.py", "tests/test_splitting.py"]

Os testes sintéticos verificam reprodução, probabilidades válidas, baseline pela prevalência de treino, mediana aprendida somente no treino, categorias exclusivas da validação, colunas totalmente ausentes, preservação da entrada de treino, isolamento do teste e rejeição de alvos, sobreposição e valores não finitos.

Critérios de conclusão: testes aprovados, treinamento sobre partições rastreáveis da fonte aprovada, comparação de validação conservada e commit incremental confirmado. Esta resposta apresenta arquivos completos propostos. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. Não há métricas observadas sobre dados reais. A mensagem de commit é uma proposta; compileall verifica sintaxe quando executado e não substitui os testes comportamentais.
