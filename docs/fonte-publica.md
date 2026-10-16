# Fonte pública de crédito — tarefa 4

Tecnologias: documentação Markdown; Pandas na futura leitura do arquivo. Dificuldade: baixa. Estimativa: 3 horas.

## Fonte selecionada

Selecionar o conjunto **Default of Credit Card Clients**, do UCI Machine Learning Repository, para a implementação do MVP. A seleção documental está registrada aqui; a acessibilidade atual dos endereços, a licença vigente e o conteúdo do arquivo permanecem pendentes de conferência, pois esta entrega não executa operações nem acessa a rede.

| Item | Registro |
| --- | --- |
| Publicador | UCI Machine Learning Repository |
| Autores associados | I-Cheng Yeh e Che-hui Lien |
| Página oficial | https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients |
| Identificador persistente | https://doi.org/10.24432/C55S3H |
| Download oficial de referência | https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip |
| Arquivo esperado | default of credit card clients.xls, dentro do arquivo ZIP |
| Licença indicada no catálogo UCI | Creative Commons Attribution 4.0 International — CC BY 4.0 |
| Texto da licença | https://creativecommons.org/licenses/by/4.0/ |
| Uso previsto | Estudo educacional, transformação e avaliação de modelos, com atribuição à fonte, link à licença e indicação das alterações |
| População descrita | Clientes de cartão de crédito em Taiwan |
| Unidade de análise | Um cliente, com seis meses de atributos financeiros e um alvo binário |
| Dimensão esperada | 30.000 registros, 23 atributos explicativos, um identificador e um alvo |
| Moeda | Novo dólar taiwanês, NT$ |
| Histórico descrito | Abril a setembro de 2005 |
| Referência analítica | Fechamento de setembro de 2005 |
| Horizonte | Mês seguinte à referência, outubro de 2005, conforme interpretação da descrição mensal da fonte |
| Data de obtenção | Não obtido nesta entrega |
| Versão dos bytes e SHA-256 | Pendentes da obtenção do arquivo |
| Verificação atual de acesso e licença | Não executada |

Referência bibliográfica: Yeh, I.-C.; Lien, C.-h. The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Systems with Applications, 36(2), 2473–2480, 2009. DOI: https://doi.org/10.1016/j.eswa.2007.12.020.

A página oficial, o DOI e a descrição que acompanha o arquivo são as referências de procedência. Não substituir silenciosamente o arquivo por uma cópia de terceiros. A licença indicada deve ser confirmada na página oficial antes da ingestão. Não há declaração de verificação jurídica ou de disponibilidade atual nesta resposta.

## Alvo e disponibilidade temporal

O alvo original é `default payment next month`: 1 significa ocorrência de inadimplência no mês seguinte e 0 significa sua ausência. O nome interno previsto é `defaulted`. Não inverter as classes e não deduzir o alvo dos códigos de atraso.

A descrição pública não estabelece neste documento um critério operacional equivalente a atraso superior a 90 dias, baixa contábil ou definição regulatória brasileira. Preservar a terminologia da fonte e registrar essa limitação em relatórios e painéis.

Os atributos mensais abrangem abril a setembro de 2005; o alvo é apresentado como referente ao mês seguinte. Isso sustenta documentalmente a ordem entre histórico e desfecho, mas não fornece horários individuais de disponibilização. A decisão simulada pressupõe que os dados de setembro estejam disponíveis no fechamento desse mês. Essa hipótese precisa aparecer na avaliação e impede interpretar o resultado como um teste operacional de concessão.

Não existem múltiplas datas de referência por cliente no formato esperado. Os seis meses aparecem como colunas de uma única observação, sem seis alvos correspondentes. Portanto, não é possível realizar validação temporal entre safras nem reconstruir uma carteira longitudinal supervisionada apenas com esse arquivo.

Usar futuramente partições estratificadas reproduzíveis de treino, validação e teste, sem sobreposição de clientes. Elas avaliarão discriminação dentro dessa amostra histórica e não generalização temporal. Não converter os seis meses em linhas independentes com o mesmo alvo.

Para compatibilidade futura com `treated_records.reference_date`, a data `2005-09-30` poderá representar a referência comum da amostra, explicitamente marcada nos metadados como convenção derivada do período documentado. Ela não é uma data individual observada e não permite divisão temporal. Esta tarefa não modifica o banco.

## Dicionário de dados

Os nomes abaixo correspondem ao arquivo esperado. Algumas ferramentas podem apresentar os atributos como X1 a X23 e o alvo como Y. A futura ingestão deverá conferir cabeçalhos e ordem; divergências exigem revisão explícita.

Tipos indicam o contrato pretendido após leitura. Valores monetários devem manter sinal e unidade. Campos inteiros poderão exigir representação anulável caso a inspeção encontre ausências. Nenhuma ausência ou distribuição foi medida nesta entrega.

| Campo original | Alias | Tipo lógico | Significado e domínio documentado | Disponibilidade | Uso no MVP |
| --- | --- | --- | --- | --- | --- |
| ID | — | Inteiro | Identificador técnico da observação | Referência da amostra | Rastreabilidade; excluir dos preditores |
| LIMIT_BAL | X1 | Numérico monetário | Limite de crédito concedido em NT$ | Referência da amostra; sem data individual de alteração | Preditor financeiro, sob hipótese de disponibilidade na referência |
| SEX | X2 | Categoria inteira | 1: masculino; 2: feminino, segundo a classificação da fonte | Referência da amostra | Excluir dos preditores |
| EDUCATION | X3 | Categoria inteira | 1: pós-graduação; 2: universidade; 3: ensino médio; 4: outros | Referência da amostra | Excluir dos preditores |
| MARRIAGE | X4 | Categoria inteira | 1: casado; 2: solteiro; 3: outros | Referência da amostra | Excluir dos preditores |
| AGE | X5 | Inteiro, anos | Idade | Referência da amostra | Excluir dos preditores |
| PAY_0 | X6 | Categoria inteira ordinal parcial | Situação de pagamento em setembro de 2005 | Setembro de 2005 | Preditor financeiro |
| PAY_2 | X7 | Categoria inteira ordinal parcial | Situação de pagamento em agosto de 2005 | Agosto de 2005 | Preditor financeiro |
| PAY_3 | X8 | Categoria inteira ordinal parcial | Situação de pagamento em julho de 2005 | Julho de 2005 | Preditor financeiro |
| PAY_4 | X9 | Categoria inteira ordinal parcial | Situação de pagamento em junho de 2005 | Junho de 2005 | Preditor financeiro |
| PAY_5 | X10 | Categoria inteira ordinal parcial | Situação de pagamento em maio de 2005 | Maio de 2005 | Preditor financeiro |
| PAY_6 | X11 | Categoria inteira ordinal parcial | Situação de pagamento em abril de 2005 | Abril de 2005 | Preditor financeiro |
| BILL_AMT1 | X12 | Numérico monetário | Valor da fatura em setembro de 2005, NT$ | Setembro de 2005 | Preditor financeiro |
| BILL_AMT2 | X13 | Numérico monetário | Valor da fatura em agosto de 2005, NT$ | Agosto de 2005 | Preditor financeiro |
| BILL_AMT3 | X14 | Numérico monetário | Valor da fatura em julho de 2005, NT$ | Julho de 2005 | Preditor financeiro |
| BILL_AMT4 | X15 | Numérico monetário | Valor da fatura em junho de 2005, NT$ | Junho de 2005 | Preditor financeiro |
| BILL_AMT5 | X16 | Numérico monetário | Valor da fatura em maio de 2005, NT$ | Maio de 2005 | Preditor financeiro |
| BILL_AMT6 | X17 | Numérico monetário | Valor da fatura em abril de 2005, NT$ | Abril de 2005 | Preditor financeiro |
| PAY_AMT1 | X18 | Numérico monetário | Valor pago em setembro de 2005, NT$ | Setembro de 2005 | Preditor financeiro |
| PAY_AMT2 | X19 | Numérico monetário | Valor pago em agosto de 2005, NT$ | Agosto de 2005 | Preditor financeiro |
| PAY_AMT3 | X20 | Numérico monetário | Valor pago em julho de 2005, NT$ | Julho de 2005 | Preditor financeiro |
| PAY_AMT4 | X21 | Numérico monetário | Valor pago em junho de 2005, NT$ | Junho de 2005 | Preditor financeiro |
| PAY_AMT5 | X22 | Numérico monetário | Valor pago em maio de 2005, NT$ | Maio de 2005 | Preditor financeiro |
| PAY_AMT6 | X23 | Numérico monetário | Valor pago em abril de 2005, NT$ | Abril de 2005 | Preditor financeiro |
| default payment next month | Y | Inteiro binário | 1: inadimplência no próximo mês; 0: ausência | Posterior à referência | Alvo; nunca preditor |

São 19 preditores financeiros candidatos: limite, seis situações de pagamento, seis faturas e seis pagamentos. A numeração original contém `PAY_0` e `PAY_2`, sem `PAY_1`; preservar os nomes para evitar deslocamento de meses.

### Códigos e ambiguidades

A descrição dos campos PAY informa -1 como pagamento em dia, 1 como atraso de um mês, 2 como atraso de dois meses, sucessivamente até 8, e 9 como atraso de nove meses ou mais. Códigos adicionais, como -2 e 0, encontrados em versões conhecidas dessa base não têm significado estabelecido pela descrição resumida aqui. Não presumir que representem ausência, atraso ou pagamento em dia. Preservar o valor bruto, contabilizar ocorrências e definir o tratamento documentado na etapa de qualidade. Não tratar toda a escala como distância numérica uniforme.

Códigos de EDUCATION fora de 1 a 4 e de MARRIAGE fora de 1 a 3 devem ser registrados como não descritos, sem inventar categorias. Esses campos continuam excluídos dos preditores. O uso futuro em análises agregadas exige justificativa específica conforme o escopo do MVP.

Valores negativos de fatura não devem ser apagados ou truncados automaticamente: podem refletir créditos ou ajustes, cuja interpretação depende da documentação. Outliers e zeros também exigem análise antes de qualquer exclusão. Não há política de limpeza implementada nesta etapa.

## Limitações e adequação ao MVP

- Amostra histórica de uma população específica; não representa automaticamente clientes atuais, solicitantes brasileiros ou todas as instituições de Taiwan.
- Carteira de clientes existentes: o histórico financeiro não estará disponível para novos solicitantes sem relacionamento. A simulação se restringe ao cenário definido no escopo.
- Uma única referência temporal impede medir mudanças macroeconômicas, deterioração temporal e estabilidade entre safras.
- A definição operacional detalhada de inadimplência e os instantes individuais de disponibilidade não estão estabelecidos nesta documentação.
- A exclusão de demografia não garante ausência de vieses: atributos financeiros podem funcionar como proxies.
- Não há documentação suficiente de custos, recuperação e exposição no momento do desfecho para estimar lucro, perda esperada ou capital regulatório. O limite não deve ser tratado automaticamente como exposição no default.
- A simulação retrospectiva de limiares não estima causalmente o efeito de uma nova política.
- O identificador técnico não deve ser divulgado em painéis nem usado para tentar reidentificar pessoas.

## Contrato para a próxima etapa

A ingestão deverá consumir um arquivo local obtido da fonte oficial e registrar procedência, data de obtenção em UTC, nome do arquivo, tamanho, SHA-256 do ZIP e do XLS, licença confirmada, referência bibliográfica e versão do contrato. Não preencher hashes ou datas com valores fictícios. Manter os arquivos brutos em `data/`, já ignorado pelo Git.

O formato esperado é Excel legado `.xls`. A leitura por Pandas normalmente requer o mecanismo `xlrd`, ausente das dependências atuais. A próxima tarefa deverá resolver e documentar essa dependência, ou uma conversão local rastreável, antes de prometer uma ingestão executável. Nenhum pacote é instalado ou acrescentado nesta entrega documental.

Conferir o cabeçalho real, pois a planilha pode apresentar uma linha de aliases antes dos nomes dos campos. Verificar os 25 campos esperados, unicidade de ID, alvo restrito a 0 e 1, tipos, valores ausentes, duplicidades e códigos não documentados. A dimensão esperada é uma referência para investigar divergências, não autorização para descartar linhas até alcançar uma contagem.

A lista de preditores deverá ser explícita e conter somente os 19 campos financeiros indicados. Excluir ID, alvo, demografia e metadados. Transformações aprendidas permanecerão em pipelines ajustados somente no treino.

## Critérios de conclusão e estado da entrega

| Critério | Evidência e estado |
| --- | --- |
| Fonte identificada | Catálogo, página oficial, DOI e endereço de download registrados |
| Licença identificada | CC BY 4.0 indicada; confirmação atual na fonte oficial pendente |
| Fonte acessível | Endereço registrado; acesso e download não verificados |
| Campos necessários identificados | Dicionário dos 25 campos e seleção dos 19 preditores registrados |
| Compatibilidade do horizonte | Sequência mensal descrita, hipótese de fechamento e limitações registradas; conferência do material original pendente |
| Validação temporal | Impossibilidade entre safras documentada; divisão estratificada prevista |
| Rastreabilidade dos bytes | Obtenção, data e hashes pendentes |

A seleção está proposta para implementação, mas A01 não está comprovado integralmente sem a conferência da fonte e das condições de uso. A02 está documentado como contrato esperado, sujeito à conferência do arquivo original. Se a licença ou a sequência entre atributos e desfecho não forem confirmadas, interromper a ingestão e revisar a seleção conforme `docs/escopo-mvp.md`.

Esta resposta fornece exclusivamente o conteúdo proposto deste documento. Nenhuma operação, leitura de arquivo local, consulta externa, validação, alteração no repositório, commit ou publicação no GitHub foi executada. A mensagem de commit é uma proposta. O comando de compilação fornecido verifica a sintaxe dos arquivos Python existentes quando executado; não verifica esta documentação, a licença ou a acessibilidade da fonte.
