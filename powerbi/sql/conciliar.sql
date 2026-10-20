-- Consultas somente de leitura. Vincular os parâmetros pelo cliente SQL.
-- :data_run_id, :prediction_run_id e :simulation_id são UUIDs.
-- :model_version e :scenario são textos; :threshold é numérico.
-- Executar as consultas da mesma conferência na mesma fotografia do banco.

-- Totais da carteira: cada coluna de divergência deve ser zero.
WITH origem AS (
    SELECT count(*) AS observations, coalesce(sum(defaulted), 0) AS defaults
    FROM credit.treated_records WHERE run_id = CAST(:data_run_id AS uuid)
), painel AS (
    SELECT coalesce(sum(observations), 0) AS observations,
           coalesce(sum(defaults), 0) AS defaults
    FROM credit_bi.carteira WHERE data_run_id = CAST(:data_run_id AS text)
)
SELECT origem.observations, origem.defaults,
       origem.observations - painel.observations AS observation_difference,
       origem.defaults - painel.defaults AS default_difference,
       origem.defaults::numeric / nullif(origem.observations, 0) AS default_rate
FROM origem CROSS JOIN painel;

-- Comparar os resultados com a página Desempenho para os mesmos filtros.
SELECT count(*) AS observations,
       sum((p.probability - r.defaulted) * (p.probability - r.defaulted))
           / nullif(count(*), 0) AS brier,
       avg(p.probability) AS mean_probability,
       avg(r.defaulted::numeric) AS default_rate,
       count(*) FILTER (WHERE r.defaulted = 0 AND p.probability < 0.5) AS tn,
       count(*) FILTER (WHERE r.defaulted = 0 AND p.probability >= 0.5) AS fp,
       count(*) FILTER (WHERE r.defaulted = 1 AND p.probability < 0.5) AS fn,
       count(*) FILTER (WHERE r.defaulted = 1 AND p.probability >= 0.5) AS tp
FROM credit.predictions AS p
JOIN credit.treated_records AS r ON r.id = p.record_id
WHERE r.run_id = CAST(:data_run_id AS uuid)
  AND p.run_id = CAST(:prediction_run_id AS uuid)
  AND p.model_version = :model_version;

-- Conferência de um ponto do gráfico de cenários, sem somar alternativas.
SELECT observations, approved, defaults, approved_defaults,
       approved::numeric / nullif(observations, 0) AS approval_rate,
       approved_defaults::numeric / nullif(approved, 0) AS approved_default_rate,
       expected_loss, expected_revenue,
       expected_revenue - expected_loss AS expected_margin
FROM credit_bi.cenarios
WHERE data_run_id = CAST(:data_run_id AS uuid)
  AND simulation_id = CAST(:simulation_id AS uuid)
  AND scenario = :scenario
  AND threshold = :threshold;
