import streamlit as st
import pandas as pd
from src.analysis import (
    get_data_types,
    get_statistics
)
from src.charts import (
    create_line_chart,
    create_bar_chart,
    create_histogram
)
from src.profiler import build_profile
from src.qa import answer_question
from src.data_loader import load_data

st.title("Data Analyst AI")

uploaded_file = st.file_uploader(
    "Carrega um ficheiro CSV ou Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    df = load_data(uploaded_file)

    st.success("Ficheiro carregado com sucesso!")
    
    # Resumo

    st.subheader("Resumo dos Dados")

    profile = build_profile(df)
    meaningful_numeric = profile["meaningful_numeric_columns"]
    meaningful_categorical = profile["meaningful_categorical_columns"]
    st.subheader("Perfil do Dataset")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Linhas",
            profile["rows"]
        )

    with col2:
        st.metric(
            "Colunas",
            profile["columns"]
        )

    with col3:
        st.metric(
            "Nulos",
            profile["null_count"]
        )

    with col4:
        st.metric(
            "Duplicados",
            profile["duplicate_count"]
        )
    st.subheader("Insights Automáticos")
    
    for insight in profile["insights"]:

        st.write(f"• {insight}")



    st.write(f"Memória Utilizada: {profile['profile_memory']} MB")
    st.write(f"Coluna de Data: {profile['date_column']}")
    st.write(f"Colunas Numéricas: {len(meaningful_numeric)}")
    st.write(f"Colunas Categóricas: {len(meaningful_categorical)}")
    st.write("Cardinalidade das Colunas")

    st.dataframe(
        pd.DataFrame(
            profile["cardinality"].items(),
            columns=["Column", "Unique Values"]
    )
)
    st.subheader("Top Categorias")
    for column, categories in profile["top_categories"].items():

        st.write(f"### {column}")

        category_df = pd.DataFrame(
            categories.items(),
            columns=["Categoria", "Percentagem"]
        )

        st.dataframe(category_df)

    st.write("Colunas Numéricas:")
    st.write(", ".join(meaningful_numeric))
    st.write("Colunas Categóricas:")
    st.write(", ".join(meaningful_categorical))

    st.subheader("Debug Semântico")
    st.write("Colunas Identificadoras:")
    st.write(", ".join(profile["identifier_columns"]))
    st.write("Colunas Numéricas Relevantes:")
    st.write(", ".join(meaningful_numeric))
    st.write("Colunas Categóricas Relevantes:")
    st.write(", ".join(meaningful_categorical))


    # Primeiras linhas

    st.subheader("Primeiras linhas dos dados")

    st.dataframe(df.head())

    # Tipos de dados

    data_types = get_data_types(df)

    st.subheader("Tipos de Dados")

    st.dataframe(data_types)

    # Estatísticas

    statistics = get_statistics(df)

    st.subheader("Estatísticas")

    st.dataframe(statistics)

    report = "DATA ANALYST AI REPORT\n\n"

    report += f"Linhas: {profile['rows']}\n"
    report += f"Colunas: {profile['columns']}\n"
    report += f"Nulos: {profile['null_count']}\n"
    report += f"Duplicados: {profile['duplicate_count']}\n\n"

    report += "INSIGHTS\n\n"
   
    for insight in profile["insights"]:

        report += f"- {insight}\n"

    st.download_button(
        label="📥 Descarregar Relatório",
        data=report,
        file_name="data_analyst_ai_report.txt",
        mime="text/plain"
    )

    # Gráfico Automático

    st.subheader("Visualização Inteligente")
    chart_names = {
        "line": "Linha",
        "bar": "Barras",
        "histogram": "Histograma"
    }

    if profile["recommended_chart"] is not None:

        st.write(
            f"📈 Gráfico Recomendado: {chart_names[profile['recommended_chart']]}"
        )

    if profile["recommended_chart"] == "line":

        if meaningful_numeric:

            selected_column = st.selectbox(
                "Escolhe a métrica",
                meaningful_numeric
            )

            fig = create_line_chart(
                df,
                x_col=profile["date_column"],
                y_col=selected_column
            )

            st.plotly_chart(fig)

        else:

            st.warning(
                "Não foi possível recomendar um gráfico."
            )

    elif profile["recommended_chart"] == "bar":

        if meaningful_categorical and meaningful_numeric:

            category_column = st.selectbox(
                "Escolhe a categoria",
                meaningful_categorical
            )

            numeric_column = st.selectbox(
                "Escolhe a métrica",
                meaningful_numeric
            )
            bar_df = (
                df.groupby(category_column)[numeric_column]
                .mean()
                .reset_index()
            )
            fig = create_bar_chart(
                bar_df,
                x_col=category_column,
                y_col=numeric_column
            )

            st.plotly_chart(fig)

        else:

            st.warning(
                "Não foi possível recomendar um gráfico."
            )

    elif profile["recommended_chart"] == "histogram":

        if meaningful_numeric:

            numeric_column = meaningful_numeric[0]

            fig = create_histogram(
                df,
                column=numeric_column
            )

            st.plotly_chart(fig)

        else:

            st.warning(
                "Não foi possível recomendar um gráfico."
            )

    else:

        st.warning(
            "Não foi possível recomendar um gráfico."
        )

    st.subheader("🤖 Ask Your Data")
    question = st.text_input(
        "Ask a question about your dataset"
    )
    if question:

        answer = answer_question(question, profile, df)

        st.success(answer)
