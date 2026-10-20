-- Tarefa 16. Aplicação posterior pelo administrador no banco do projeto.
-- Não executar como usuário de aplicação ou de relatório.
-- A transação preserva a atomicidade do provisionamento.
BEGIN;

CREATE SCHEMA credit_bi;
REVOKE ALL ON SCHEMA credit_bi FROM PUBLIC;

-- Papel sem login e sem credenciais versionadas.
CREATE ROLE credit_bi_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
GRANT USAGE ON SCHEMA credit_bi TO credit_bi_reader;

CREATE VIEW credit_bi.carteira AS
SELECT
    run_id::text AS data_run_id,
    reference_date,
    CASE
        WHEN features ->> 'LIMIT_BAL' IS NULL THEN 'ausente'
        WHEN (features ->> 'LIMIT_BAL')::numeric < 100000 THEN 'abaixo_100000'
        WHEN (features ->> 'LIMIT_BAL')::numeric < 300000 THEN '100000_a_299999'
        ELSE '300000_ou_mais'
    END AS segment,
    'historico'::text AS nature,
    count(*) AS observations,
    sum(defaulted)::bigint AS defaults
FROM credit.treated_records
GROUP BY run_id, reference_date, 3;

-- A mesma observação pode ter previsões de execuções/modelos diferentes.
-- Os filtros de execução de previsão e modelo são obrigatórios no relatório.
CREATE VIEW credit_bi.desempenho AS
SELECT
    r.run_id::text AS data_run_id,
    p.run_id::text AS prediction_run_id,
    p.model_version,
    r.reference_date,
    'avaliacao_retrospectiva'::text AS nature,
    0.5::numeric AS threshold,
    count(*) AS observations,
    sum(r.defaulted)::bigint AS defaults,
    sum(p.probability) AS probability_sum,
    sum((p.probability - r.defaulted) * (p.probability - r.defaulted)) AS brier_sum,
    count(*) FILTER (WHERE r.defaulted = 0 AND p.probability < 0.5) AS tn,
    count(*) FILTER (WHERE r.defaulted = 0 AND p.probability >= 0.5) AS fp,
    count(*) FILTER (WHERE r.defaulted = 1 AND p.probability < 0.5) AS fn,
    count(*) FILTER (WHERE r.defaulted = 1 AND p.probability >= 0.5) AS tp
FROM credit.predictions AS p
JOIN credit.treated_records AS r ON r.id = p.record_id
GROUP BY r.run_id, p.run_id, p.model_version, r.reference_date;

-- Somente agregados revisados de simulate_policies. Sem registros individuais.
-- Esta tabela não é preenchida automaticamente por esta entrega.
CREATE TABLE credit_bi.cenarios (
    simulation_id uuid NOT NULL,
    data_run_id uuid NOT NULL REFERENCES credit.execution_runs(id),
    model_version text NOT NULL CHECK (length(trim(model_version)) > 0),
    dataset_version text NOT NULL CHECK (length(trim(dataset_version)) > 0),
    evaluation_partition text NOT NULL CHECK (
        evaluation_partition IN ('validacao', 'teste_final')
    ),
    source_label text NOT NULL CHECK (length(trim(source_label)) > 0),
    reference_date date NOT NULL,
    reference_date_basis text NOT NULL CHECK (
        reference_date_basis IN ('observada', 'convencao_documental', 'sintetica')
    ),
    scenario text NOT NULL CHECK (length(trim(scenario)) > 0),
    threshold numeric NOT NULL CHECK (threshold BETWEEN 0 AND 1),
    currency text NOT NULL CHECK (length(trim(currency)) > 0),
    horizon text NOT NULL CHECK (length(trim(horizon)) > 0),
    exposure_assumption text NOT NULL CHECK (length(trim(exposure_assumption)) > 0),
    observations bigint NOT NULL CHECK (observations > 0),
    approved bigint NOT NULL CHECK (approved >= 0),
    defaults bigint NOT NULL CHECK (defaults BETWEEN 1 AND observations - 1),
    approved_defaults bigint NOT NULL CHECK (approved_defaults >= 0),
    expected_loss numeric NOT NULL CHECK (
        expected_loss >= 0 AND expected_loss::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    expected_revenue numeric NOT NULL CHECK (
        expected_revenue >= 0 AND expected_revenue::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    nature text NOT NULL DEFAULT 'estimativa_hipotetica'
        CHECK (nature = 'estimativa_hipotetica'),
    PRIMARY KEY (simulation_id, scenario, threshold),
    CHECK (approved <= observations),
    CHECK (approved_defaults <= approved),
    CHECK (approved_defaults <= defaults),
    CHECK (defaults - approved_defaults <= observations - approved)
);

GRANT SELECT ON credit_bi.carteira, credit_bi.desempenho, credit_bi.cenarios
TO credit_bi_reader;
REVOKE ALL ON credit_bi.carteira, credit_bi.desempenho, credit_bi.cenarios FROM PUBLIC;

COMMIT;
