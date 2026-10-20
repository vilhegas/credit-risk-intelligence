# Simulador de políticas — tarefa 14

Tecnologias: Python, NumPy, Pandas e Pytest. Dificuldade: alta. Estimativa: quatro horas.

## Contrato e uso

`credit_risk.simulation.policies.simulate_policies` recebe alvo binário, probabilidades finais e exposições individuais alinhadas por posição. Séries Pandas devem ter índices idênticos. Arrays exigem alinhamento garantido pelo chamador. Não há leitura, escrita, conexão, treinamento ou escolha automática da melhor política.

Informar pelo menos três limiares distintos entre zero e um, cenários explícitos e metadados de dados, modelo, moeda, horizonte e hipótese da exposição. Todos os montantes devem usar a mesma moeda e horizonte, sem conversão implícita. Exposição deve ser não negativa e finita; LGD deve estar entre zero e um. Multiplicador de exposição e taxa de receita devem ser não negativos e finitos. Valores booleanos, ausências e vetores incompatíveis são rejeitados. A avaliação exige ambas as classes; amostras vazias ou de classe única causam ValueError.

```python
from credit_risk.simulation.policies import Scenario, report_json, simulate_policies

report = simulate_policies(
    y=[0, 1, 0, 1],
    probability=[0.05, 0.2, 0.4, 0.8],
    exposure=[100, 200, 300, 400],
    thresholds=[0.1, 0.3, 0.6],
    scenarios=[
        Scenario('base_sintetica', 1, 0.5, 0.1),
        Scenario('estresse_sintetico', 1.2, 0.8, 0.05),
    ],
    dataset_version='sintetica-v1',
    model_version='modelo-fixo-v1',
    currency='NT$',
    horizon='um mês',
    exposure_assumption='Valores sintéticos; não derivados do limite UCI.',
)
serialized = report_json(report)
```

Para integrar com Policy, fornecer `policy.probabilities(probabilidades_base)` uma única vez. A lista de limiares compara alternativas à política congelada; incluir nela `policy.threshold` quando pertinente. A API não reajusta calibração nem altera Policy. Congelar cenários e limiares no desenvolvimento antes da avaliação final. Explorar alternativas após consultar o teste impede usar esse mesmo teste como avaliação independente da escolha resultante.

## Cálculos

Aprovar quando p < limiar; igualdade implica recusa. Limiar zero recusa todos. Limiar um ainda recusa p=1. Cada cenário usa EAD_i = exposição_i × multiplicador, LGD proporcional constante e taxa r constante.

Para os aprovados:

- Perda esperada: soma de p_i × EAD_i × LGD.
- Receita esperada: soma de (1 − p_i) × EAD_i × r.
- Margem esperada antes de custos: receita esperada menos perda esperada.
- Perda de cenário com desfecho histórico: soma de y_i × EAD_i × LGD.
- Receita de cenário com desfecho histórico: soma de (1 − y_i) × EAD_i × r.

A receita pressupõe recebimento somente sem inadimplência; não inclui receita parcial em default. LGD representa a proporção perdida após recuperação pressuposta, sem estimar recuperação a partir da base. Os cálculos históricos também usam hipóteses: não são perdas ou receitas realizadas observadas. Margens excluem captação, operação, tributos, capital e desconto temporal; não representam lucro nem capital regulatório. Não usar custos de falsos positivos/negativos da calibração como substitutos de exposição ou LGD.

Cada linha informa população, aprovados, recusados, inadimplentes aprovados e recusados e suas taxas. Aprovação divide aprovados pelo total. Inadimplência entre aprovados divide inadimplentes aprovados pelos aprovados e fica None sem aprovados. Recall divide inadimplentes recusados pelo total de inadimplentes. Sem aprovados, montantes somados são zero. O relatório contém apenas agregados e configurações; `report_json` produz JSON estrito em memória. Excesso da representação numérica monetária causa erro.

## Hipóteses e limitações

A fonte UCI contém clientes existentes historicamente aprovados. Seus desfechos não representam os solicitantes historicamente recusados. Esse viés de seleção impede extrapolar os resultados para toda a população candidata; nenhum resultado de recusados é imputado. As recusas simuladas possuem desfechos porque eram integrantes da carteira histórica, não porque se observou o resultado de negar crédito.

Probabilidades, população e desfechos permanecem fixos entre cenários. Alterar exposição não altera automaticamente a probabilidade de inadimplência no simulador. A mudança de risco, comportamento, demanda e composição da carteira não é modelada. Comparações são descritivas e não estimam efeito causal das políticas.

A UCI não fornece EAD, recuperação e custos suficientes para resultados econômicos observados. LIMIT_BAL não equivale automaticamente a exposição. Qualquer aproximação deve ser fornecida e justificada explicitamente em exposure_assumption; os cenários desta entrega são hipotéticos. As expectativas dependem da validade e calibração das probabilidades, além dessas hipóteses. Não há garantia operacional, regulatória, de equidade ou de generalização temporal.

Conservar posteriormente o relatório em artifacts/ junto à identidade do modelo, calibrador, partições, hashes dos dados, código e ambiente. As versões declaradas não comprovam essa rastreabilidade. Usar uma observação independente por cliente; a API não recebe identificadores e não detecta clientes repetidos.

## Validação e conclusão

Vetores não interativos para execução posterior, separadamente, sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_simulation.py"]
- ["python", "-m", "ruff", "check", "src/credit_risk/simulation/policies.py", "tests/test_simulation.py"]

Testes sintéticos verificam fórmulas conhecidas, igualdade no limiar, aprovação total e nula, exposição zero, LGD zero e um, receita zero, margem negativa, escala dos cenários, alinhamento, preservação da entrada, reprodução, JSON estrito e contratos inválidos.

Critérios de conclusão: testes aprovados, hipóteses revisadas, comparação de três limiares sobre dados rastreáveis e commit incremental confirmado. Esta resposta fornece somente arquivos completos propostos. Nenhuma operação, validação, alteração, commit ou publicação foi executada. Compileall verifica sintaxe quando executado e não substitui os testes comportamentais. A mensagem de commit é uma proposta.
