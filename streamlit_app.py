"""Ponto de entrada da demonstração Streamlit local."""

import json

import pandas as pd
import streamlit as st

from credit_risk.presentation.demo import (
    DATASET_VERSION,
    MODEL_VERSION,
    example_record,
    explore_policies,
    indicators,
    predict_record,
)


def main():
    st.set_page_config(page_title="Demonstração de risco de crédito", layout="wide")
    st.title("Demonstração de risco de crédito")
    st.warning(
        "Dados inteiramente sintéticos. Uso educacional; resultados não servem "
        "para concessão real, avaliação de pessoas ou estimativas bancárias."
    )
    st.caption(
        f"Fonte: gerador local determinístico | Dados: {DATASET_VERSION} | "
        f"Modelo: {MODEL_VERSION} | Período: artificial, sem datas observadas"
    )
    try:
        summary = indicators()
    except Exception:
        st.error("Não foi possível preparar a demonstração. Confira o ambiente documentado.")
        return
    st.caption(f"Amostra de exploração: {summary['observations']} registros sintéticos.")
    overview, prediction, policies = st.tabs(["Indicadores", "Prever registro", "Políticas"])
    with overview:
        columns = st.columns(3)
        columns[0].metric("Registros", summary["observations"])
        columns[1].metric("Inadimplentes sintéticos", summary["defaults"])
        columns[2].metric("Taxa de inadimplência", f"{summary['default_rate']:.1%}")
        st.bar_chart(pd.DataFrame({
            "Quantidade": [
                summary["observations"] - summary["defaults"], summary["defaults"]
            ]
        }, index=["Adimplentes", "Inadimplentes"]))
    with prediction:
        st.write(
            "Edite somente os 19 atributos financeiros do exemplo. "
            "Não informe nomes, documentos, contatos ou identificadores. "
            "Valores monetários são inteiros hipotéticos; PAY usa categorias textuais."
        )
        with st.form("prediction"):
            text = st.text_area(
                "Registro financeiro em JSON",
                value=json.dumps(example_record(), indent=2),
                height=360,
                max_chars=10000,
            )
            submitted = st.form_submit_button("Prever risco")
        if submitted:
            try:
                probability = predict_record(text)
            except ValueError as error:
                st.error(str(error))
            except Exception:
                st.error("Previsão indisponível. Confira o ambiente documentado.")
            else:
                st.metric("Probabilidade estimada pelo modelo sintético", f"{probability:.1%}")
    with policies:
        st.write(
            "Aprovação quando p < limiar; igualdade implica recusa. "
            "Compare três limiares distintos. A exploração usa validação sintética, "
            "sem consultar o teste reservado."
        )
        with st.form("policies"):
            thresholds = [
                st.number_input(
                    f"Limiar {i + 1}", min_value=0.0, max_value=1.0,
                    value=value, step=0.05,
                )
                for i, value in enumerate((0.2, 0.5, 0.8))
            ]
            exposure = st.number_input(
                "Exposição hipotética por registro", min_value=0.0,
                max_value=1_000_000_000.0, value=1000.0,
            )
            lgd = st.number_input(
                "Proporção perdida após recuperação (LGD)",
                min_value=0.0, max_value=1.0, value=0.5,
            )
            revenue = st.number_input(
                "Taxa de receita hipotética", min_value=0.0, max_value=1.0, value=0.1,
            )
            simulate = st.form_submit_button("Comparar políticas")
        if simulate:
            try:
                report = explore_policies(thresholds, exposure, lgd, revenue)
            except ValueError:
                st.error(
                    "Use três limiares distintos entre 0 e 1 e valores financeiros "
                    "finitos dentro dos limites indicados."
                )
            except Exception:
                st.error("Simulação indisponível. Confira o ambiente documentado.")
            else:
                rows = pd.DataFrame(report["rows"])
                st.dataframe(rows, hide_index=True)
                st.line_chart(rows.set_index("threshold")[["approval_rate"]])
                st.caption(
                    "Taxa entre aprovados ausente significa que não houve aprovados. "
                    "Montantes são hipóteses; margem exclui custos e não representa lucro."
                )
    st.info(
        "O modelo é ajustado somente no treino artificial. As métricas e políticas "
        "são descritivas; não demonstram causalidade, equidade, calibração em dados "
        "reais ou generalização temporal. Nenhum artefato externo é carregado."
    )


if __name__ == "__main__":
    main()
