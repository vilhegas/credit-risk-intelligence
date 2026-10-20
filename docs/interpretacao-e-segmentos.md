# Interpretação e avaliação por segmentos — tarefa 13

Tecnologias: Python, Pandas, NumPy, Scikit-learn e Pytest. Dificuldade: alta. Estimativa: quatro horas.

## Contrato

O módulo `credit_risk.modeling.interpretation` acrescenta APIs independentes, sem modificar treinamento, calibração, dados ou relatórios anteriores. Não acessa arquivos, banco ou rede e não ajusta estimadores.

`permutation_report(model, X, y, dataset_version=..., repeats=20, seed=42)` recebe um modelo já ajustado compatível com `default_probability` e os atributos da avaliação. Seleciona exclusivamente FEATURES, os 19 atributos financeiros originais. Calcula a queda de average precision ao permutar cada coluna, preservando conjuntamente sua representação dentro do pipeline. Retorna importância média, desvio padrão amostral e quantis 2,5% e 97,5% entre permutações. Esses quantis descrevem aleatoriedade da permutação, não incerteza populacional. Valores negativos são preservados. A ordenação decrescente identifica fatores associados à capacidade preditiva, sem indicar direção de efeito ou causalidade. Atributos correlacionados podem ocultar importância; combinações permutadas podem ser pouco plausíveis.

A interpretação refere-se ao modelo fornecido, antes da calibração externa de Policy. Não confundir essa importância com a importância da política calibrada. Para interpretar outra cadeia de previsão, fornecer explicitamente um estimador compatível que represente essa cadeia congelada.

`segment_report(y, probability, segments, dataset_version=..., threshold=...)` recebe probabilidades finais e um limiar já congelado. Para usar a entrega anterior, calcular `policy.probabilities(probabilidades_base)` e fornecer `policy.threshold`. Não aplicar a calibração duas vezes. A API não seleciona limiares nem altera a política.

As entradas são posicionais. Séries Pandas fornecidas em conjunto devem ter índices idênticos; arrays exigem alinhamento garantido pelo chamador. Usar uma observação independente por cliente. A API não recebe identificadores e não detecta repetição de clientes ou vazamento entre conjuntos.

## Segmentação e resultados

Definir segmentos financeiros antes da avaliação: por exemplo, as faixas de LIMIT_BAL já documentadas na exploração. Fornecer rótulos textuais e representar ausências com um rótulo explícito. A função avalia uma segmentação por chamada. Não fornecer identificadores individuais como segmentos. Atributos demográficos permanecem fora dos preditores e não são introduzidos nesta entrega.

Por padrão, um segmento exige pelo menos 100 observações e 20 registros de cada classe. Os limites são configuráveis, devem ser registrados previamente e não garantem poder estatístico ou representatividade. Grupos insuficientes exibem contagens e motivo, com métricas indisponíveis; grupos de classe única também são insuficientes. Essas contagens não constituem anonimização para publicação.

O relatório compara AP, ROC-AUC e Brier com a amostra global. As diferenças são observadas, sem teste de significância; o global contém os próprios segmentos. AP depende da prevalência, informada pelas contagens. Brier, probabilidade média e curva de calibração com denominadores permitem examinar calibração. Intervalos vazios são omitidos; fronteiras internas pertencem ao intervalo inferior.

A classificação usa p >= limiar para recusa e inadimplência como classe positiva. A matriz segue [[TN, FP], [FN, TP]]. São informados falsos positivos, falsos negativos, recall, precisão, aprovação e inadimplência entre aprovados, sempre com numerador e denominador. Sem denominador, valor e intervalo ficam indisponíveis. As proporções recebem intervalos de Wilson de 95%, pontuais e sob hipótese de observações independentes. Não há intervalos populacionais para AP, AUC, Brier ou diferenças entre grupos; não concluir superioridade estatística a partir dessas diferenças.

`report_json(report)` serializa os relatórios agregados como JSON estrito em memória. Conservar posteriormente os resultados em artifacts/, junto à identidade do modelo, política, hashes dos dados, partições, código e ambiente. A versão declarada não substitui rastreabilidade.

## Uso e interpretação responsável

Usar desenvolvimento reservado para diagnósticos que possam orientar alterações. Se a validação já orientou seleção de modelos ou políticas, registrar esse reaproveitamento e possível otimismo. No teste final, congelar previamente modelo, política, segmentos e parâmetros do relatório; não fazer novas escolhas após consultar os resultados.

As saídas identificam fatores preditivos associados, diferenças descritivas de desempenho, calibração e erros, e limitações. Não demonstram efeito de alterar atributos ou políticas. Sem dados demográficos adequados, representatividade e desenho específico, não permitem concluir equidade ou ausência de discriminação. As limitações históricas da fonte continuam aplicáveis.

## Validação e estado

Vetores não interativos para execução posterior, separadamente e sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_interpretation.py"]

Os testes sintéticos cobrem matriz, Brier, fronteiras da calibração, intervalos conhecidos, supressão de grupos insuficientes, classe única, ausência de aprovados, contratos inválidos, alinhamento, reprodução, preservação da entrada e importância de um fator preditivo conhecido.

Critérios de conclusão: testes aprovados, relatórios gerados sobre dados rastreáveis, fatores e diferenças revisados com suas limitações e commit incremental confirmado. Esta entrega fornece somente arquivos completos propostos. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. Não existem resultados observados sobre dados reais nesta resposta. A mensagem de commit é uma proposta; compileall verifica sintaxe e não substitui os testes comportamentais.
