"""Consultas descritivas PostgreSQL, restritas a uma execução de dados."""

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from credit_risk.ingestion.uci import FEATURES

# Somente consultas constantes; valores externos usam parâmetros vinculados.
QUERIES = {
    "volume": """
        SELECT count(*) AS operations,
               count(DISTINCT subject_key) AS subjects,
               count(DISTINCT reference_date) AS reference_dates,
               coalesce(sum(defaulted), 0) AS defaults,
               avg(defaulted::double precision) AS default_rate
        FROM credit.treated_records
        WHERE run_id = :run_id
    """,
    "distribution": """
        WITH amounts AS (
            SELECT v.variable, v.amount
            FROM credit.treated_records AS r
            CROSS JOIN LATERAL (VALUES
                ('LIMIT_BAL', (r.features ->> 'LIMIT_BAL')::double precision),
                ('BILL_AMT1', (r.features ->> 'BILL_AMT1')::double precision),
                ('PAY_AMT1', (r.features ->> 'PAY_AMT1')::double precision)
            ) AS v(variable, amount)
            WHERE r.run_id = :run_id
        ), variables(variable) AS (
            VALUES ('LIMIT_BAL'), ('BILL_AMT1'), ('PAY_AMT1')
        )
        SELECT v.variable, count(a.amount) AS observed,
               min(a.amount) AS minimum, max(a.amount) AS maximum,
               avg(a.amount) AS mean,
               percentile_cont(0.25) WITHIN GROUP (ORDER BY a.amount) AS q25,
               percentile_cont(0.50) WITHIN GROUP (ORDER BY a.amount) AS median,
               percentile_cont(0.75) WITHIN GROUP (ORDER BY a.amount) AS q75
        FROM variables AS v
        LEFT JOIN amounts AS a ON a.variable = v.variable
        GROUP BY v.variable
        ORDER BY v.variable
    """,
    "missing": """
        WITH records AS (
            SELECT features FROM credit.treated_records WHERE run_id = :run_id
        ), variables AS (
            SELECT unnest(CAST(:features AS text[])) AS variable
        )
        SELECT v.variable,
               (SELECT count(*) FROM records) AS operations,
               (SELECT count(*) FROM records AS r
                WHERE r.features ->> v.variable IS NULL) AS missing,
               (SELECT avg((r.features ->> v.variable IS NULL)::integer)
                FROM records AS r) AS missing_rate
        FROM variables AS v
        ORDER BY v.variable
    """,
    "segments": """
        WITH classified AS (
            SELECT defaulted,
                   CASE
                       WHEN features ->> 'LIMIT_BAL' IS NULL THEN 'ausente'
                       WHEN (features ->> 'LIMIT_BAL')::double precision < 100000
                           THEN 'abaixo_100000'
                       WHEN (features ->> 'LIMIT_BAL')::double precision < 300000
                           THEN '100000_a_299999'
                       ELSE '300000_ou_mais'
                   END AS segment
            FROM credit.treated_records
            WHERE run_id = :run_id
        )
        SELECT segment, count(*) AS operations,
               sum(defaulted) AS defaults,
               avg(defaulted::double precision) AS default_rate
        FROM classified
        GROUP BY segment
        ORDER BY segment
    """,
}


def describe_run(connection: Connection, run_id: UUID) -> dict[str, list[dict]]:
    """Lê agregados sem abrir conexão, gravar dados ou controlar a transação.

    O chamador fornece uma conexão PostgreSQL e uma execução de ingestão.
    Para consistência entre consultas durante cargas concorrentes, deve usar
    uma transação REPEATABLE READ. Resultados SQL NULL permanecem como None.
    """
    if not isinstance(run_id, UUID):
        raise ValueError("run_id deve ser UUID.")
    parameters = {"run_id": run_id, "features": list(FEATURES)}
    return {
        name: [dict(row) for row in connection.execute(sa.text(sql), parameters).mappings()]
        for name, sql in QUERIES.items()
    }
