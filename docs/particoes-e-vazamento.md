# Separação de dados — tarefa 9

Tecnologias: Python, Pandas, NumPy, Scikit-learn e Pytest. Dificuldade: alta. Estimativa: quatro horas.

## API

`credit_risk.modeling.splitting.split_data(frame, dataset_version)` recebe registros tratados com os campos originais, incluindo ID e alvo. Não lê arquivos, acessa serviços, altera a entrada ou ajusta transformações. Retorna treino, validação, teste e metadados agregados.

Cada partição contém X com exclusivamente os 19 campos financeiros de FEATURES, y separado e positions com posições de entrada baseadas em zero. Índices originais duplicados não afetam a seleção. As posições permitem reconstruir as partições sobre a mesma entrada imutável; preservar sua ordem e a identidade dos bytes junto à versão declarada. A versão declarada não substitui checksum nem proveniência da ingestão.

ID, demografia, alvo e qualquer coluna adicional, incluindo variáveis futuras e metadados, não entram em X. A seleção utiliza os nomes originais aprovados; não detecta conteúdo futuro indevidamente colocado sob um nome permitido.

## Estratégias

Sem reference_date, ou com referência única, aplica duas divisões estratificadas reproduzíveis por cliente, com proporções solicitadas de 60%, 20% e 20% e semente 42. Todas as linhas de um cliente permanecem juntas. Identificadores devem ter tipo consistente e alvo constante por cliente nessa estratégia; conflitos causam erro. As proporções referem-se a clientes e podem diferir das proporções de linhas. Ordenação dos grupos é determinística; para reconstrução idêntica manter também a ordem da entrada.

Essa é a estratégia apropriada à referência comum da UCI. Os seis meses em colunas não constituem safras supervisionadas distintas. O resultado registra que a separação não mede generalização temporal. Sem datas de disponibilidade, registra também a hipótese documental de que os campos financeiros estavam disponíveis no fechamento de setembro de 2005. O chamador deve conferir essa hipótese na fonte aprovada antes do uso.

Com múltiplas referências, a função exige pelo menos três datas distintas, label_end_date e availability_columns: um dicionário que associa cada um dos 19 nomes financeiros à coluna com seu instante de disponibilidade. Datas são convertidas para UTC; datas sem fuso são interpretadas como UTC, portanto devem ser padronizadas pelo chamador. Ausências e datas inválidas interrompem a chamada. Disponibilidade posterior à referência é rejeitada, mesmo para valores financeiros ausentes. O horizonte do alvo deve terminar após a referência.

As fronteiras são escolhidas por frações da quantidade de datas distintas ordenadas. Uma mesma data nunca é dividida. Todos os registros de clientes presentes em mais de um período são excluídos. Linhas do treino cujo horizonte termina na fronteira da validação ou depois dela são expurgadas; o equivalente ocorre entre validação e teste. Não existe fallback após erro temporal. O teste não exige que seu horizonte já tenha terminado no relógio atual: o chamador continua responsável por fornecer desfechos históricos efetivamente observados.

Os metadados registram método, semente, versão, frações solicitadas, fronteiras UTC, atributos, exclusões e contagens por conjunto e classe. Cada conjunto deve conter ambas as classes após o expurgo; caso contrário, a função falha. Exclusões podem alterar representatividade e prevalência; não são silenciosamente compensadas com sorteios adicionais.

## Uso nas próximas etapas

Fixar e conservar as partições antes de qualquer exploração que oriente escolhas. Usar `frame.iloc[list(result.train.positions)]` como entrada da análise exploratória existente; ela espera também o alvo original. Relatórios exploratórios anteriores sobre toda a amostra não devem orientar seleção de modelos ou atributos; se já orientaram decisões, registrar essa contaminação na avaliação.

Imputação, codificação, escala, seleção estatística e demais parâmetros aprendidos deverão permanecer em pipelines ajustados exclusivamente no treino. Validação serve para escolhas de modelo e limiar; teste fica reservado à avaliação final. Esta entrega não treina modelos, não implementa pipelines nem bloqueia acesso posterior aos conjuntos pelo chamador.

As saídas em memória incluem posições e alvo e devem permanecer em ambiente restrito. Não publicar identificadores, linhas ou manifestos individuais no Git. Não há persistência automática, migração ou mudança no contrato de ingestão anterior.

## Validação e conclusão

Vetores não interativos para execução posterior, separadamente, sem shell, rede ou instalação:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_splitting.py"]

Os testes sintéticos verificam isolamento de clientes com linhas repetidas, cobertura sem perdas no fallback, reprodução, preservação da entrada, índices duplicados, seleção explícita dos atributos, cronologia, expurgo do horizonte, exclusão de clientes entre períodos, rejeição de atributos posteriores à decisão e falhas sem fallback silencioso.

Critérios de conclusão: testes aprovados, partições geradas sobre a versão local rastreável da fonte, revisão das hipóteses de disponibilidade e commit incremental confirmado. Nenhuma operação, validação, alteração local, commit ou publicação foi executada nesta resposta. Os arquivos e a mensagem de commit são propostas para aplicação posterior; compileall verifica sintaxe e não substitui os testes comportamentais.
