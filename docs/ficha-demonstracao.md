# Catálogo e ficha do modelo demonstrativo

## Catálogo de dados

| Item | Demonstração sintética | Fluxo público UCI |
| --- | --- | --- |
| Origem | Gerador determinístico local de `credit_risk.presentation.demo` | Default of Credit Card Clients, conforme `fonte-publica.md` |
| Volume | 400 registros artificiais antes da divisão | 30.000 registros esperados, não conferidos nesta entrega |
| Unidade | Registro financeiro artificial | Cliente da carteira histórica |
| Período | Artificial, sem datas observadas | Abril a setembro de 2005; alvo do mês seguinte conforme contrato documental |
| Moeda | Inteiros e montantes hipotéticos | NT$, conforme documentação da fonte |
| Preditores | 19 atributos financeiros do contrato existente | Os mesmos 19 candidatos financeiros |
| Alvo | Binário artificial; 1 representa inadimplência sintética | `default payment next month`; 1 indica inadimplência |
| Identificadores e demografia | Não solicitados nos formulários | Excluídos dos preditores |
| Versão | Constante `DATASET_VERSION` exibida na interface | Versão declarada, contrato e hashes registrados na ingestão |
| Proveniência | Código do gerador e revisão do repositório | Data real de obtenção, ZIP/XLS e respectivos SHA-256 |
| Condições de uso | Não redistribui registros UCI | CC BY 4.0 indicada no catálogo existente; confirmação documental pendente |
| Estado | Fluxo descrito e testes fornecidos; execução não confirmada | Aquisição, licença atual e conteúdo não verificados nesta entrega |

Os valores literais de `DATASET_VERSION` e `MODEL_VERSION` não foram fornecidos no material desta tarefa. A interface os apresenta a partir do módulo existente; registrar seus valores observados no aceite sem inventá-los.

O dicionário completo dos 25 campos originais e as ambiguidades de PAY estão em `fonte-publica.md`. Os preditores incluem LIMIT_BAL, PAY_0 e PAY_2 a PAY_6, BILL_AMT1 a BILL_AMT6 e PAY_AMT1 a PAY_AMT6. ID, SEX, EDUCATION, MARRIAGE, AGE e o alvo não integram os preditores.

## Ficha do modelo

| Item | Registro |
| --- | --- |
| Nome | Modelo da demonstração local de risco de crédito |
| Responsável | Responsável pelo repositório; identificação de manutenção pendente |
| Versão do pacote proposta | 0.1.0 |
| Implementação | `credit_risk.presentation.demo`, reutilizando o pipeline existente |
| Tipo de saída | Probabilidade entre 0 e 1 para um registro financeiro artificial |
| Treinamento | Somente treino gerado por `split_data` sobre dados sintéticos |
| Exploração e políticas | Validação sintética; teste reservado não consultado pelo fluxo descrito |
| Persistência | Modelo em memória no processo; sem carregamento de estimadores externos |
| Uso previsto | Demonstrar engenharia, validação de entradas e comparação de políticas |
| Uso excluído | Concessão real, avaliação de pessoas, estimativas de desempenho bancário e produção |
| Desempenho confirmado | Nenhum resultado observado ou teste executado nesta entrega |
| Comparação real com baseline | Pendente de avaliação rastreável conforme `avaliacao-final.md` |

A especificação do pipeline de referência está em `modelo-referencia.md`: imputação e escala monetária, imputação e codificação categórica de PAY, regressão logística e baseline Dummy. A comparação adicional inclui árvores. Não há alegação de que o modelo da interface seja o vencedor de um experimento real ou represente a Policy calibrada da tarefa 12.

## Contrato da interface

O formulário exige exatamente os 19 campos financeiros. Valores monetários devem ser inteiros finitos no intervalo de menos a mais um bilhão. PAY utiliza categorias textuais documentadas, incluindo representações explícitas de códigos não documentados. Ausências, campos extras e chaves repetidas são rejeitados. Esses limites protegem a interface; não são regras bancárias.

A política aprova quando p < limiar; igualdade implica recusa. Três limiares distintos são comparados com exposição constante, LGD e receita hipotéticas. Sem aprovados, inadimplência entre aprovados fica indisponível.

## Limitações

- Dados artificiais podem conter relações produzidas pelo próprio gerador; seu desempenho não estima generalização para dados públicos ou reais.
- Probabilidade emitida não constitui comprovação de calibração, equidade ou estabilidade temporal.
- A amostra UCI representa clientes existentes de uma população histórica específica; não representa solicitantes recusados ou novos clientes sem histórico.
- Retirar atributos demográficos não elimina proxies ou discriminação indireta.
- Alterar exposição no simulador não altera automaticamente risco, comportamento ou composição da população.
- LIMIT_BAL não equivale automaticamente à exposição no default. Margens excluem custos e não representam lucro.
- A aplicação não possui autenticação, infraestrutura operacional ou garantias regulatórias. O servidor demonstrativo permanece local.
- Dependências diretas fixadas e sementes não substituem lock transitivo, registro do ambiente e evidências de reprodução.

Qualquer futura divulgação de métricas deve identificar dados, partição, denominadores, modelo, política e revisão do código. Resultados negativos devem ser preservados. Não selecionar novamente modelo ou limiar após consultar o teste final.
