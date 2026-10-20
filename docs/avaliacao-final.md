# Automação e avaliação final — tarefa 17

Tecnologias: Python, NumPy, Scikit-learn, Pytest, Ruff, GitHub Actions e PostgreSQL. Dificuldade média. Estimativa: três horas.

## Automação

O workflow executa Ruff e a suíte completa, incluindo os testes sintéticos existentes de persistência, ingestão e indicadores. As duas URLs de integração são obrigatórias: ausência, bancos diferentes ou falha de conexão interrompem o job. Os testes existentes aplicam as migrações usando o administrador e verificam o acesso com o usuário de aplicação.

O runner deve ser efêmero, exclusivo e previamente preparado com Python compatível, pacote e dependências de desenvolvimento nas versões declaradas. PostgreSQL deve estar previamente provisionado, com credit_app e um banco vazio exclusivo por job. Configurar TEST_DATABASE_URL e TEST_MIGRATION_DATABASE_URL nos segredos do repositório. Nunca usar banco real ou compartilhado. O workflow não instala pacotes, baixa imagens ou provisiona serviços. O checkout usa a infraestrutura normal do GitHub; a execução remota do workflow exige conectividade do runner.

Não habilitar execução de contribuições externas em runners persistentes. A limpeza do ambiente efêmero pertence ao provisionador. Não há operação destrutiva de limpeza no workflow. O lint integral pode revelar pendências anteriores; elas devem ser corrigidas antes de declarar o pipeline aprovado.

## Protocolo final

Antes de acessar o teste, conservar o modelo base ajustado somente no treino, o Dummy ajustado no mesmo treino, a Policy, a ordem das partições e a configuração do ambiente. Registrar hashes SHA-256 reais dos dados, manifesto das partições, modelo e política, revisão do código e instante UTC de congelamento. Não desserializar modelos de origem desconhecida.

Usar exclusivamente a partição de teste original de split_data. Produzir probabilidades do modelo escolhido e aplicar policy.probabilities uma única vez. Produzir as probabilidades do Dummy congelado nas mesmas linhas. Passar os três vetores alinhados a evaluate_once, juntamente com policy.threshold e frozen_manifest. Não refazer seleção, calibração, treinamento ou busca de limiar nessa etapa.

O diretório output_directory deve ser único para o experimento, por exemplo artifacts/final/experimento-001. A função cria esse diretório exclusivamente e grava RESERVED.json antes das métricas. Uma repetição no mesmo diretório falha, inclusive após falha parcial. Preservar reservas incompletas e investigar a causa sem consultar resultados para alterar decisões. O bloqueio é local: outro diretório ou outra cópia dos dados permite nova execução. A governança do experimento deve impedir esse contorno.

A API recebe previsões prontas, não comprova seu vínculo com os hashes nem detecta clientes repetidos ou desalinhamento semântico. A revisão do manifesto e das partições é obrigatória. Não inserir identificadores, URLs de banco ou segredos no manifesto. O relatório contém agregados, configuração e limitações, sem previsões individuais.

## Relatório e incerteza

report.json registra AP, ROC-AUC e Brier do modelo e do baseline; prevalência; diferença pareada de AP; precisão, recall, F1, matriz [[TN, FP], [FN, TP]], aprovação, inadimplência entre aprovados e curva de calibração. A regra é recusar quando p >= limiar. Sem denominador, a métrica fica nula. A curva usa dez intervalos uniformes, com fronteiras internas atribuídas ao intervalo inferior.

A comparação de superioridade é estritamente descritiva: AP maior que a do baseline. Resultado igual ou inferior permanece registrado. Não trocar o modelo após um resultado negativo.

O bootstrap pareado reamostra as mesmas posições para modelo e baseline. Usa percentis pontuais de 95%, semente e orçamento explícitos; registra replicações de classe única descartadas e denominadores válidos por métrica. Pressupõe observações independentes por cliente. Não representa incerteza do treinamento, correção por seleção, dependência temporal ou garantia de cobertura em amostras pequenas. O teste reservado não deve orientar novas escolhas após a leitura dos intervalos.

## Validação e estado

Vetores posteriores, separados, não interativos e sem shell:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "ruff", "check", "."]
- ["python", "-m", "pytest"]

Os novos testes verificam métricas conhecidas, fronteira do limiar, ausência de aprovados, resultado negativo, reprodução do bootstrap, JSON estrito e proteção contra sobrescrita. Seus hashes são valores artificiais identificados como teste.

Estado do relatório final real: pendente. Não foram fornecidos artefatos congelados verificáveis, previsões ou dados do teste reservado. Nenhuma operação foi executada nesta resposta; não há métricas reais, aprovação do pipeline, commit ou publicação confirmados. Os arquivos fornecem a implementação proposta. Conclusão exige pipeline aprovado e execução única documentada sobre os artefatos reais, preservando inclusive resultados negativos e sem reajuste orientado pelo teste.
