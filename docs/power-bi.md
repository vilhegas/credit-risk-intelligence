# Painel Power BI — tarefa 16

Tecnologias: PostgreSQL, Power Query M, DAX e Power BI Desktop. Dificuldade média. Estimativa: quatro horas.

## Entrega e limites

Esta entrega fornece provisionamento SQL, consultas M, medidas DAX e especificação de montagem do relatório. Preserva os módulos e contratos anteriores. Não contém PBIX/PBIT nem relatório visual já montado. Nenhuma operação, validação, alteração local, commit ou publicação foi executada. A montagem e os testes no Desktop permanecem necessários para concluir a tarefa.

O fluxo principal Streamlit permanece disponível sem Power BI. O painel usa Importação e atualização manual; não exige publicação no serviço Power BI.

## Preparar o acesso

Após as migrações existentes, o administrador aplica `powerbi/sql/provisionar.sql` uma única vez no banco correto, usando cliente PostgreSQL. O script cria o esquema credit_bi, duas views agregadas, uma tabela de cenários e o papel credit_bi_reader. Não deve ser aplicado novamente: objetos existentes provocam erro e a transação é revertida. Ele é um provisionamento explícito separado do Alembic; não altera revisões nem permissões anteriores.

Criar pelo administrador um login exclusivo para o relatório, com senha definida fora do Git e sem privilégios administrativos. Conceder a esse login somente CONNECT no banco e associação a credit_bi_reader com herança habilitada. Não associar credit_app, papéis de escrita, propriedade ou outros grupos. Conferir privilégios herdados e concessões a PUBLIC no ambiente existente. O papel leitor não recebe acesso às tabelas credit, atributos JSON, identificadores ou configurações das execuções. As views usam os privilégios de seu proprietário; esse proprietário deve ser o administrador responsável pelo provisionamento, nunca o login do painel.

O login precisa apenas consultar credit_bi. Não recebe INSERT, UPDATE, DELETE, CREATE ou privilégios futuros automáticos. As exportações locais importadas pelo Desktop continuam contendo agregados e devem ser conservadas em ambiente autorizado.

No Desktop, selecionar PostgreSQL, informar servidor e banco e escolher Importação. Informar o login exclusivo na janela de autenticação do conector. Nunca inserir senha ou URL com credenciais em M, DAX, documentação ou controle de versão. Para o ambiente Compose existente, usar a porta local configurada; acesso remoto exige infraestrutura própria previamente aprovada.

## Fontes e contratos

Carteira agrupa os registros tratados por execução de ingestão, data de referência e faixa de LIMIT_BAL. Cada observação é um cliente/data conforme o contrato existente, não um contrato bancário. Inadimplentes são a soma do alvo 1. Nenhuma taxa pré-calculada é somada ou recebe média simples.

Desempenho agrupa previsões persistidas por execução dos dados, execução da previsão, modelo e data. O alvo histórico é comparado com probabilidades estimadas. O limiar fixo é 0,5: p >= 0,5 significa recusa. TN, FP, FN e TP seguem a convenção anterior. Brier é soma dos erros quadráticos dividida pelo total, ponderado corretamente entre datas.

Esta tabela não fornece AP, AUC nem comprovação de avaliação independente. Não persistir previsões de treino ou desenvolvimento como se fossem teste final. A origem, partição e identidade do calibrador devem ser registradas no relatório de avaliação associado à execução. Não rotular estas métricas como teste final sem essa evidência. O limiar fixo não representa automaticamente a Policy selecionada na tarefa 12.

Cenarios recebe exclusivamente agregados revisados da tarefa 14. Não há integração automática: o publicador responsável insere as linhas mediante parâmetros vinculados, em uma única transação por simulation_id. Usar um UUID novo por relatório e não reutilizá-lo para outro modelo, amostra, partição, moeda ou horizonte. Não conceder escrita ao leitor do Power BI.

Mapear observations para o tamanho da amostra efetivamente simulada; approved para aprovados; defaults para inadimplentes dessa amostra; approved_defaults para inadimplentes aprovados; expected_loss e expected_revenue para os montantes esperados do simulador. Conferir esses valores contra o JSON original antes da publicação. Não usar o total da ingestão quando a simulação contém somente validação. Informar dataset_version, model_version, evaluation_partition, source_label, reference_date, reference_date_basis, currency, horizon e exposure_assumption a partir da execução rastreável, sem inventar dados. A data única deste contrato representa a referência comum da amostra; não dividir uma linha multissafra em datas fictícias. Congelar pelo menos três limiares distintos e publicar todas as alternativas do relatório.

A tabela permanece vazia até essa publicação explícita. O painel deve mostrar ausência de cenários, sem preencher zeros fictícios. Montantes são estimativas hipotéticas; LIMIT_BAL não é EAD observada. Margem exclui custos e não representa lucro. A tabela não armazena hashes ou artefatos de reprodução: conservar o relatório original em artifacts/, associado ao simulation_id por um registro local de publicação.

## Modelo no Desktop

Criar as sete consultas de `powerbi/consultas.pq` separadamente, com os nomes indicados nos comentários. O arquivo é uma coleção de blocos para o Editor Avançado, não uma única expressão M. Desativar a carga de FonteBI. Carregar as outras seis consultas.

Criar relações 1:* de Execucoes[data_run_id] para data_run_id de Carteira, Desempenho e Cenarios. Criar relações 1:* de Datas[reference_date] para reference_date dessas mesmas três tabelas. Usar direção única das dimensões para os fatos e relações ativas. Não relacionar fatos diretamente nem ativar detecção automática adicional.

As dimensões são derivadas da carteira: publicações de cenários devem referenciar execução e data existentes nela. Conferir isso antes de carregar. Desabilitar Data/hora automática. Não criar tendência mensal para a referência comum UCI: os seis meses de atributos não são seis safras de avaliação.

Adicionar as medidas de `powerbi/medidas.dax`, uma por vez, às tabelas indicadas. Formatar taxas como porcentagem e Brier com quatro casas decimais. Desabilitar sumarização padrão de limiar e identificadores. Não usar medidas implícitas de taxas nos visuais. As medidas bloqueiam totais que misturariam execuções ou alternativas incompatíveis. DIVIDE deixa resultados sem denominador em branco; não substituir por zero.

## Páginas e interação

Em todas as páginas, adicionar segmentadores de Execucoes[data_run_id], com seleção única obrigatória, e Datas[reference_date]. Sincronizar somente esses dois segmentadores entre páginas. Adicionar caixa de texto com fonte, versão dos dados, período e convenção de data da execução selecionada, obtidos da proveniência revisada. Atualizar esse texto ao trocar a execução; não publicar uma seleção cuja proveniência não esteja identificada.

Página Carteira — título 'Carteira histórica'. Adicionar cartões Observacoes historicas, Inadimplentes historicos e Taxa historica. Criar colunas com Carteira[segment] no eixo e Observacoes historicas no valor; outro gráfico usa Taxa historica com observações e inadimplentes nas dicas. Segmentador de faixa afeta apenas esta página. A faixa não está disponível nos fatos de desempenho e cenários.

Página Desempenho — título 'Avaliação retrospectiva de probabilidades estimadas'. Adicionar seleção única de prediction_run_id e model_version. Criar cartões Observacoes avaliadas, Brier, Probabilidade media estimada, Taxa observada avaliacao, Precisao limiar fixo e Recall limiar fixo. Uma tabela apresenta reference_date, tn, fp, fn e tp, sem totais entre modelos. Exibir texto 'Limiar fixo 0,5; avaliação não certificada como teste final'. A contagem avaliada pode ser menor que a carteira: não declarar cobertura integral sem conferência.

Página Cenarios — título 'Cenários hipotéticos'. Adicionar seleção única de simulation_id e scenario. Exibir model_version, dataset_version, evaluation_partition, source_label, reference_date_basis, currency, horizon e exposure_assumption em uma tabela de contexto. Gráfico de linhas usa threshold no eixo e Aprovacao simulada no valor. Outro usa Perda estimada hipotetica e Margem estimada antes de custos. Cada ponto fornece o contexto de um limiar à medida. Adicionar tabela por threshold com aprovação e inadimplência histórica entre aprovados simulados; desativar totais. Não somar políticas alternativas. Cartões monetários exigem selecionar um único limiar no gráfico, ou um segmentador de limiar específico para os cartões; configurar esse segmentador para não filtrar os gráficos comparativos.

Em Editar interações, garantir que execução e data filtrem todos os visuais da página, que seleção de faixa filtre os cartões históricos e que o gráfico de limiar filtre os cartões de cenários. Títulos devem distinguir histórico, avaliação retrospectiva e estimativa hipotética. Incluir nota visível: 'Uso educacional. Sem inferência causal, garantia de equidade ou validade operacional'.

## Conciliação e atualização manual

Aplicar os mesmos filtros no Desktop e em `powerbi/sql/conciliar.sql`. Os parâmetros são vinculados pelo cliente SQL, não concatenados. Contagens devem coincidir exatamente; comparar taxas e Brier com tolerância absoluta de 0,000001, pois M converte numerais para ponto flutuante. Para montantes, comparar na precisão de exibição adotada e registrar diferenças de arredondamento.

A primeira consulta compara totais da view com a tabela de origem, com divergências esperadas iguais a zero. A segunda calcula desempenho diretamente das previsões e alvos. A terceira confere um ponto de cenário; conferir também esse ponto contra o JSON do simulador, pois consultar apenas a tabela publicada não valida seu conteúdo original.

Para atualização manual: finalizar as cargas e publicações; interromper novas gravações durante a atualização e a conferência; no Desktop selecionar Página Inicial > Atualizar; aguardar todas as consultas; revisar mensagens; repetir a conciliação e registrar horário UTC, filtros e resultados em artifacts/. As consultas importadas não compartilham automaticamente uma transação PostgreSQL: sem janela estável, os fatos podem refletir instantes diferentes. Um erro de atualização não deve ser tratado como dados atuais.

Salvar o relatório local em artifacts/powerbi/, já ignorado pelo Git. Não publicar PBIX com dados importados ou credenciais. O código M, as medidas e esta especificação ficam versionados; o arquivo visual montado exige revisão separada.

## Critérios de aceite

- Login exclusivo consegue SELECT apenas nos agregados autorizados e falha ao consultar credit.treated_records ou escrever em credit_bi.cenarios; verificar isso em ambiente exclusivo de testes, sem mutações em dados reais.
- Totais globais, por faixa e por data coincidem com SQL para a execução selecionada; outra execução não altera os resultados.
- Seleções de previsão e modelo isolam métricas, e a soma TN+FP+FN+TP coincide com observações avaliadas.
- Pelo menos três limiares aparecem na comparação publicada. Sem aprovados, inadimplência entre aprovados fica em branco; sem cenários, a página não inventa resultados.
- Filtros e interações são exercitados no Desktop, inclusive seleção vazia, mudança de execução e cartões sem contexto único.
- Atualização manual e conciliação são registradas; relatório visual montado e revisado; commit incremental confirmado posteriormente.

O vetor de validação da resposta é ["python", "-m", "compileall", "."]. Quando executado, verifica apenas sintaxe Python e não valida SQL, M, DAX, permissões ou interação visual. Esses critérios permanecem pendentes; não há alegação de painel já validado ou commit realizado.
