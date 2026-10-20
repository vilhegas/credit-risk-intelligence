# Calibração e limiares — tarefa 12

Tecnologias: Python, NumPy, Scikit-learn e Pytest. Dificuldade: alta. Estimativa: quatro horas.

## Contrato de desenvolvimento

O módulo `credit_risk.modeling.calibration` recebe probabilidades já produzidas pelo modelo escolhido, sem refazer a comparação anterior. Não acessa arquivos, banco ou rede. Nenhuma API de seleção recebe o teste final.

Antes dos ajustes, separar o desenvolvimento em treino do modelo, calibração e seleção. O modelo base e suas transformações devem ser ajustados exclusivamente no treino. Produzir probabilidades fora da amostra para calibração e seleção com esse mesmo modelo congelado. Na estratégia temporal, preservar cronologia, clientes disjuntos e expurgo dos horizontes. Não subdividir aleatoriamente uma validação temporal.

A validação usada pela comparação anterior já participou da escolha do modelo. Sua subdivisão posterior não cria uma avaliação independente: registrar esse reaproveitamento e seu possível otimismo. Para maior independência, planejar as subdivisões antes da comparação ou usar desenvolvimento adicional. Nunca utilizar teste para resolver essa limitação.

`select_policy` exige alvos, probabilidades e chaves técnicas alinhadas de calibração e seleção. As chaves permitem rejeitar clientes compartilhados entre esses dois conjuntos, mas não comprovam isolamento em relação ao treino, disponibilidade temporal ou procedência. Essas garantias continuam sendo responsabilidade do chamador. Não publicar chaves individuais.

Informar explicitamente `thresholds`, `false_negative_cost`, `false_positive_cost`, `min_approval_rate`, `min_default_recall`, `minimum_brier_gain` e `development_version`. Não há custos ou restrições comerciais presumidos. Todas as amostras avaliadas devem conter ambas as classes.

## Calibração

`calibration_report` calcula Brier score e curva uniforme com dez intervalos por padrão. Informa contagens por intervalo ocupado; intervalos vazios são omitidos. Valores exatamente na fronteira interna pertencem ao intervalo inferior, conforme a implementação do Scikit-learn. Probabilidades zero e um são aceitas.

O candidato sigmoid usa regressão logística regularizada sobre o logit das probabilidades, com truncamento fixo em 0,000001 e 0,999999 apenas para esse cálculo. Seus coeficientes são ajustados exclusivamente na amostra de calibração. O Brier original e o calibrado são comparados na seleção. Adota-se sigmoid somente se a redução de Brier superar estritamente o ganho mínimo declarado; em empate conserva-se identidade. A regra é descritiva e não constitui teste de significância. O relatório mantém ambas as curvas.

## Política congelada

Aprovar quando p < limiar e recusar quando p >= limiar. Inadimplência é a classe positiva. A matriz usa linhas reais e colunas previstas na ordem 0, 1: [[TN, FP], [FN, TP]]. FN representa inadimplente aprovado; FP representa adimplente recusado.

Custo total = FN × custo de FN + FP × custo de FP. Acertos têm custo zero neste contrato. Os custos são escalares não negativos em unidades hipotéticas declaradas; não representam lucro, exposição, perda esperada ou capital regulatório.

Cada limiar explícito é avaliado na seleção após a escolha da calibração. São elegíveis os que satisfazem simultaneamente aprovação mínima e recall mínimo dos inadimplentes. Escolhe-se o menor custo total; em empate, o menor limiar. Ausência de candidato elegível causa ValueError, sem relaxar restrições. Sem aprovados, a inadimplência entre aprovados é None.

A função retorna uma `Policy` imutável com limiar, custos, restrições e coeficientes, além de relatório agregado serializável como JSON estrito. `policy.report_json()` permite conservar a configuração posteriormente em artifacts/. A API não grava o artefato. Preservar também identidade do modelo base, hashes dos dados, partições, código e ambiente: a versão declarada isoladamente não garante reprodução.

Para avaliação final posterior, passar a mesma Policy e probabilidades do mesmo modelo base a `evaluate_policy`. Essa função apenas calcula métricas; não altera parâmetros. Não reajustar modelo ou calibrador depois de congelar a política sem reiniciar sua validação. As restrições atendidas na seleção não são garantidas no teste ou em outra população.

## Validação e estado

Vetores não interativos para execução posterior, separadamente e sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_calibration.py"]

Os testes sintéticos cobrem Brier conhecido, fronteiras e denominadores da curva, matriz e custos conhecidos, ausência de aprovados, restrições inviáveis, desempate, seleção de sigmoid com ganho observado, reprodução e imutabilidade da política.

Critérios de conclusão: testes aprovados, curvas e política geradas sobre desenvolvimento rastreável, custos e restrições revisados, configuração congelada conservada e commit incremental confirmado. Esta entrega contém somente arquivos propostos. Nenhuma operação, validação, alteração, commit ou publicação foi executada. Não há resultados observados em dados reais. O comando compileall verifica sintaxe quando executado e não substitui os testes comportamentais.
