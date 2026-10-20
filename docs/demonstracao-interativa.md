# Demonstração interativa — tarefa 15

Tecnologias: Python, Pandas, NumPy, Scikit-learn, Streamlit e Pytest. Dificuldade: média. Estimativa: quatro horas.

## Execução local

Com o pacote e as dependências de desenvolvimento já disponíveis no ambiente, executar o vetor não interativo, sem shell:

`["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.address", "127.0.0.1"]`

Abrir http://127.0.0.1:8501 no navegador local. A configuração versionada limita o endereço ao loopback, desativa estatísticas de uso e oculta detalhes de exceções. Não publicar este servidor como serviço de produção.

## Fluxo

A aplicação oferece indicadores agregados com gráfico, previsão de um registro financeiro em formulário JSON e comparação de três políticas com tabela e gráfico de aprovação. A tela informa fonte, período artificial, versões, denominador e limitações.

O gerador determinístico cria 400 registros inteiramente sintéticos. O pipeline existente é ajustado exclusivamente no treino produzido por split_data; indicadores e simulações utilizam a validação. O conjunto de teste não é consultado. O modelo é mantido em memória no processo, sem treinamento repetido a cada interação. Essa demonstração não mede desempenho sobre a fonte UCI nem substitui os relatórios anteriores.

Os 19 atributos do exemplo são obrigatórios. Campos adicionais e repetidos são rejeitados. Valores monetários devem ser inteiros finitos entre menos e mais um bilhão; esses limites são proteções da interface, não regras de elegibilidade bancária. Faturas negativas continuam permitidas. PAY aceita strings -1, 1 a 9 e as categorias explícitas nao_documentado:-2 e nao_documentado:0, sem atribuir significado aos códigos não documentados. A interface não aceita ausências nesta versão.

A simulação reutiliza simulate_policies e sua regra p < limiar, com exposição constante artificial, LGD e receita explicitamente informadas. Limiares repetidos recebem mensagem clara. Sem aprovados, a taxa entre aprovados permanece indisponível. Margens excluem custos e não representam lucro. Consultar também simulacao-politicas.md.

## Artefatos e privacidade

O único modelo confiável nesta entrega é construído pelo código local versionado. Não existe upload, caminho configurável de modelo, pickle, joblib ou desserialização de estimadores externos. Assim, nenhum artefato externo recebe confiança implícita por extensão ou localização.

Não são solicitados identificadores, demografia, credenciais ou conexões ao banco. Entradas permanecem na sessão Streamlit durante seu uso; não são gravadas em arquivos, cache de previsão ou logs pela aplicação. Mensagens de validação exibem somente nomes de campos fixos e regras, sem repetir valores enviados. Exceções inesperadas recebem mensagens genéricas, sem exibição de traceback pela interface. Não inserir informações pessoais no formulário.

## Validação e conclusão

Vetores para execução posterior, separadamente, sem shell, instalações ou rede:

- ["python", "-m", "compileall", "."]
- ["python", "-m", "pytest", "tests/test_demo.py"]

Os testes propostos cobrem fluxo dos serviços, probabilidades, agregados, ausência de aprovados, entradas inválidas, campos adicionais, duplicados, limites financeiros, mensagens sem valores privados e navegação Streamlit com submissão dos dois formulários.

Critérios de conclusão: testes aprovados e fluxo local revisado com dados demonstrativos, incluindo erros de entrada. Esta resposta fornece exclusivamente arquivos completos propostos. Nenhum comando, teste, alteração, commit ou envio ao GitHub foi executado. A mensagem de commit é uma proposta; compileall verifica sintaxe e não substitui os testes comportamentais.
