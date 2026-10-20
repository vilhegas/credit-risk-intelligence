// Power Query M. Criar cada consulta separadamente no Editor Avançado.
// Substituir somente servidor e banco por valores locais sem credenciais.
// Nome: FonteBI
let
    Fonte = PostgreSQL.Database(
        "127.0.0.1:5432",
        "credit_risk",
        [CreateNavigationProperties = false]
    )
in
    Fonte

// Nome: Carteira
let
    Fonte = FonteBI{[Schema = "credit_bi", Item = "carteira"]}[Data],
    Tipos = Table.TransformColumnTypes(Fonte, {
        {"data_run_id", type text}, {"reference_date", type date},
        {"segment", type text}, {"nature", type text},
        {"observations", Int64.Type}, {"defaults", Int64.Type}
    })
in
    Tipos

// Nome: Desempenho
let
    Fonte = FonteBI{[Schema = "credit_bi", Item = "desempenho"]}[Data],
    Tipos = Table.TransformColumnTypes(Fonte, {
        {"data_run_id", type text}, {"prediction_run_id", type text},
        {"model_version", type text}, {"reference_date", type date},
        {"observations", Int64.Type}, {"defaults", Int64.Type},
        {"tn", Int64.Type}, {"fp", Int64.Type},
        {"fn", Int64.Type}, {"tp", Int64.Type},
        {"threshold", type number}, {"probability_sum", type number},
        {"brier_sum", type number}
    })
in
    Tipos

// Nome: Cenarios
let
    Fonte = FonteBI{[Schema = "credit_bi", Item = "cenarios"]}[Data],
    Tipos = Table.TransformColumnTypes(Fonte, {
        {"simulation_id", type text}, {"data_run_id", type text},
        {"reference_date", type date}, {"threshold", type number},
        {"observations", Int64.Type}, {"approved", Int64.Type},
        {"defaults", Int64.Type}, {"approved_defaults", Int64.Type},
        {"expected_loss", type number}, {"expected_revenue", type number}
    })
in
    Tipos

// Nome: Execucoes
let
    Fonte = Table.Distinct(Table.SelectColumns(Carteira, {"data_run_id"}))
in
    Fonte

// Nome: Datas
let
    Fonte = Table.Distinct(Table.SelectColumns(Carteira, {"reference_date"})),
    Ordenadas = Table.Sort(Fonte, {{"reference_date", Order.Ascending}})
in
    Ordenadas
