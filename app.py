import html

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
from src.analysis_catalog import get_analysis_catalog
from src.profiler import build_profile
from src.qa import answer_question
from src.data_loader import DataLoadingError, load_data


def render_badges(values, empty_text="None identified."):
    if not values:
        st.caption(empty_text)
        return

    badge_html = " ".join(
        (
            "<span style='display:inline-block;"
            "padding:0.2rem 0.55rem;"
            "margin:0 0.25rem 0.35rem 0;"
            "border-radius:999px;"
            "background:#eef2ff;"
            "color:#1e3a8a;"
            "font-size:0.82rem;"
            "font-weight:600;'>"
            f"{html.escape(str(value))}</span>"
        )
        for value in values
    )

    st.markdown(badge_html, unsafe_allow_html=True)


def render_card(title, body, accent="#2563eb"):
    st.markdown(
        (
            "<div style='border:1px solid #e5e7eb;"
            f"border-left:5px solid {accent};"
            "border-radius:8px;"
            "padding:1rem;"
            "margin-bottom:0.75rem;"
            "background:#ffffff;'>"
            f"<div style='font-weight:700;margin-bottom:0.35rem;'>{html.escape(str(title))}</div>"
            f"<div style='color:#374151;font-size:0.95rem;'>{body}</div>"
            "</div>"
        ),
        unsafe_allow_html=True
    )


def format_dataset_type(dataset_type):
    dataset_types = {
        "transactional_sales_dataset": "Retail / Sales Business",
        "financial_or_sales_dataset": "Sales or Financial Business",
        "customer_dataset": "Customer-Focused Business",
        "product_dataset": "Product-Focused Business",
        "general_business_dataset": "General Business Dataset",
        "limited_business_dataset": "Limited Business Dataset"
    }

    return dataset_types.get(dataset_type, "Business Dataset")


def format_readiness(readiness):
    readiness_labels = {
        "ready": "Ready",
        "partially_ready": "Partially Ready",
        "not_ready": "Not Ready"
    }

    return readiness_labels.get(readiness, "Unknown")


def format_business_value(value):
    if not value:
        return "Unknown"

    return str(value).title()


def format_chart_name(chart_name):
    chart_names = {
        "line": "Line Chart",
        "bar": "Bar Chart",
        "histogram": "Histogram",
        "scatter": "Scatter Plot"
    }

    return chart_names.get(chart_name, "Chart")


def get_analysis_by_id(analysis_catalog):
    return {
        analysis.get("id"): analysis
        for analysis in analysis_catalog
    }


def get_available_analysis_by_id(available_analyses):
    return {
        analysis.get("id"): analysis
        for analysis in available_analyses
    }


def get_recommended_analysis(executive_priorities, analysis_catalog, available_analyses):
    if not executive_priorities:
        return None, None

    priority = executive_priorities[0]
    analysis_id = priority.get("analysis_id")

    return (
        get_analysis_by_id(analysis_catalog).get(analysis_id, {}),
        get_available_analysis_by_id(available_analyses).get(analysis_id, {})
    )


def get_first_matched_column(resolved_analysis, concept_type):
    matched_concepts = resolved_analysis.get("matched_concepts", {})
    concept_matches = matched_concepts.get(concept_type, {})

    for matches in concept_matches.values():
        if matches:
            return matches[0]

    return None


def get_column_index(columns, preferred_column):
    if preferred_column in columns:
        return columns.index(preferred_column)

    return 0


def get_health_display(area, health):
    status = health.get("status", "unknown")
    title = str(area).replace("_", " ").title()
    reason = health.get("reason", "No assessment available.")

    if status == "healthy":
        return title, "Healthy", reason, "#16a34a"

    if status == "attention":
        return title, "Needs Attention", reason, "#dc2626"

    return title, "Unknown", reason, "#64748b"


def render_business_health_cards(business_health):
    if not business_health:
        st.write("No business health assessment available.")
        return

    health_items = list(business_health.items())

    for index in range(0, len(health_items), 2):
        columns = st.columns(2)
        row_items = health_items[index:index + 2]

        for column, (area, health) in zip(columns, row_items):
            title, status, reason, accent = get_health_display(area, health)

            with column:
                render_card(
                    title,
                    (
                        f"<div style='font-size:1.05rem;font-weight:700;"
                        f"color:{accent};margin-bottom:0.35rem;'>"
                        f"{html.escape(status)}</div>"
                        f"{html.escape(reason)}"
                    ),
                    accent=accent
                )


def render_executive_priority_cards(executive_priorities, analysis_catalog):
    if not executive_priorities:
        st.write("No executive priorities available.")
        return

    analyses_by_id = get_analysis_by_id(analysis_catalog)

    for priority in executive_priorities:
        analysis = analyses_by_id.get(priority.get("analysis_id"), {})
        title = priority.get("title", "Recommended Analysis")
        business_question = analysis.get(
            "business_question",
            "This analysis can help clarify business performance."
        )
        why_it_matters = analysis.get(
            "decision_supported",
            priority.get("reason", "Helps management decide where to focus first.")
        )
        recommended_chart = format_chart_name(analysis.get("preferred_chart"))
        business_value = format_business_value(priority.get("business_value"))

        render_card(
            f"Priority #{priority.get('priority')} - {title}",
            (
                "<div style='display:grid;gap:0.55rem;'>"
                "<div><strong>Business Question</strong><br>"
                f"{html.escape(business_question)}</div>"
                "<div><strong>Why it matters</strong><br>"
                f"{html.escape(why_it_matters)}</div>"
                "<div><strong>Recommended visualization</strong><br>"
                f"{html.escape(recommended_chart)}</div>"
                "<div><strong>Business Value</strong><br>"
                f"{html.escape(business_value)}</div>"
                "</div>"
            ),
            accent="#2563eb"
        )


def render_business_metrics_summary(business_metrics):
    summary_rows = []

    for area, metrics in business_metrics.items():
        if "metrics_by_column" in metrics:
            for column, values in metrics["metrics_by_column"].items():
                summary_rows.append({
                    "Area": area,
                    "Column": column,
                    "Total": values.get("total"),
                    "Average": values.get("average"),
                    "Count": values.get("count")
                })

        elif "unique_counts" in metrics:
            for column, unique_count in metrics["unique_counts"].items():
                summary_rows.append({
                    "Area": area,
                    "Column": column,
                    "Unique Count": unique_count
                })

        else:
            summary_rows.append({
                "Area": area,
                "Null Count": metrics.get("null_count"),
                "Null Percentage": metrics.get("null_percentage"),
                "Duplicate Count": metrics.get("duplicate_count")
            })

    if not summary_rows:
        st.write("No business metrics available.")
        return

    st.dataframe(
        pd.DataFrame(summary_rows),
        use_container_width=True,
        hide_index=True
    )


def render_business_health_summary(business_health):
    health_rows = []

    for area, health in business_health.items():
        health_rows.append({
            "Area": area,
            "Status": health.get("status"),
            "Reason": health.get("reason")
        })

    if not health_rows:
        st.write("No business health assessment available.")
        return

    st.dataframe(
        pd.DataFrame(health_rows),
        use_container_width=True,
        hide_index=True
    )


def render_executive_priorities(executive_priorities):
    if not executive_priorities:
        st.write("No executive priorities available.")
        return

    st.dataframe(
        pd.DataFrame(executive_priorities),
        use_container_width=True,
        hide_index=True
    )


def render_developer_debug(
    df,
    profile,
    meaningful_numeric,
    meaningful_categorical,
    business_metrics,
    data_types,
    statistics
):
    with st.expander("Developer Debug"):
        st.write("Raw Data Preview")
        st.dataframe(df.head(), use_container_width=True)

        st.write("Data Types")
        st.dataframe(data_types, use_container_width=True)

        st.write("Descriptive Statistics")
        st.dataframe(statistics, use_container_width=True)

        st.write("Business Metrics Detail")
        render_business_metrics_summary(business_metrics)

        st.write("Semantic Classification")
        debug_col1, debug_col2, debug_col3 = st.columns(3)

        with debug_col1:
            st.caption("Identifier Columns")
            render_badges(profile["identifier_columns"])

        with debug_col2:
            st.caption("Meaningful Numeric Columns")
            render_badges(meaningful_numeric)

        with debug_col3:
            st.caption("Meaningful Categorical Columns")
            render_badges(meaningful_categorical)

        st.write("Column Cardinality")
        st.dataframe(
            pd.DataFrame(
                profile["cardinality"].items(),
                columns=["Column", "Unique Values"]
            ),
            use_container_width=True,
            hide_index=True
        )

        st.write("Top Categories")
        for column, categories in profile["top_categories"].items():
            st.caption(column)
            st.dataframe(
                pd.DataFrame(
                    categories.items(),
                    columns=["Category", "Percentage"]
                ),
                use_container_width=True,
                hide_index=True
            )


st.title("Data Analyst AI")
st.caption("Your Business Decision Assistant")

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    try:
        df = load_data(uploaded_file)

    except DataLoadingError as error:
        st.error(str(error))
        st.stop()

    st.success("File loaded successfully.")

    profile = build_profile(df)
    meaningful_numeric = profile["meaningful_numeric_columns"]
    meaningful_categorical = profile["meaningful_categorical_columns"]
    data_types = get_data_types(df)
    statistics = get_statistics(df)

    st.subheader("Dataset Profile")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Rows",
            profile["rows"]
        )

    with col2:
        st.metric(
            "Columns",
            profile["columns"]
        )

    with col3:
        st.metric(
            "Missing Values",
            profile["null_count"]
        )

    with col4:
        st.metric(
            "Duplicate Rows",
            profile["duplicate_count"]
        )

    business_diagnosis = profile.get("business_diagnosis", {})
    business_metrics = profile.get("business_metrics", {})
    business_health = profile.get("business_health", {})
    available_analyses = profile.get("available_analyses", [])
    executive_priorities = profile.get("executive_priorities", [])
    analysis_catalog = get_analysis_catalog()
    available_analysis_count = sum(
        1
        for analysis in available_analyses
        if analysis.get("available")
    )

    st.subheader("Executive Summary")
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric(
            "Business Type",
            format_dataset_type(business_diagnosis.get("dataset_type"))
        )

    with summary_col2:
        st.metric(
            "Analysis Readiness",
            format_readiness(business_diagnosis.get("analysis_readiness"))
        )

    with summary_col3:
        st.metric(
            "Available Analyses",
            available_analysis_count
        )

    with summary_col4:
        st.metric(
            "Priority Analyses",
            len(executive_priorities)
        )

    st.write("This dataset contains information about:")
    render_badges(business_diagnosis.get("business_areas", []))

    if not business_diagnosis.get("business_areas"):
        st.caption("Business areas could not be identified from this dataset yet.")

    warnings = business_diagnosis.get("warnings", [])

    if warnings:
        with st.expander("Warnings"):
            for warning in warnings:
                st.warning(warning.get("message", "Review this dataset before analysis."))

    st.subheader("Business Health")
    render_business_health_cards(business_health)

    st.subheader("Executive Priorities")
    render_executive_priority_cards(executive_priorities, analysis_catalog)

    st.subheader("Charts")
    recommended_catalog_analysis, recommended_resolved_analysis = get_recommended_analysis(
        executive_priorities,
        analysis_catalog,
        available_analyses
    )

    if recommended_catalog_analysis:
        st.info("Recommended first analysis")
        render_card(
            recommended_catalog_analysis.get("title", "Recommended Analysis"),
            (
                "<strong>Business Question</strong><br>"
                f"{html.escape(recommended_catalog_analysis.get('business_question', ''))}"
            ),
            accent="#0ea5e9"
        )

    chart_names = {
        "line": "Line",
        "bar": "Bar",
        "histogram": "Histogram"
    }
    preferred_chart = recommended_catalog_analysis.get("preferred_chart")
    selected_chart_type = profile["recommended_chart"]

    if preferred_chart == "line" and profile.get("date_column") and meaningful_numeric:
        selected_chart_type = "line"
    elif preferred_chart == "bar" and meaningful_categorical and meaningful_numeric:
        selected_chart_type = "bar"
    elif preferred_chart == "histogram" and meaningful_numeric:
        selected_chart_type = "histogram"

    if selected_chart_type is not None:

        st.write(
            f"Recommended chart: {chart_names[selected_chart_type]}"
        )

    if selected_chart_type == "line":

        if meaningful_numeric:
            preferred_metric = get_first_matched_column(
                recommended_resolved_analysis or {},
                "metrics"
            )

            selected_column = st.selectbox(
                "Choose a business metric",
                meaningful_numeric,
                index=get_column_index(meaningful_numeric, preferred_metric)
            )

            fig = create_line_chart(
                df,
                x_col=profile["date_column"],
                y_col=selected_column
            )

            st.plotly_chart(fig)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    elif selected_chart_type == "bar":

        if meaningful_categorical and meaningful_numeric:
            preferred_dimension = get_first_matched_column(
                recommended_resolved_analysis or {},
                "dimensions"
            )
            preferred_metric = get_first_matched_column(
                recommended_resolved_analysis or {},
                "metrics"
            )

            category_column = st.selectbox(
                "Choose a category",
                meaningful_categorical,
                index=get_column_index(meaningful_categorical, preferred_dimension)
            )

            numeric_column = st.selectbox(
                "Choose a business metric",
                meaningful_numeric,
                index=get_column_index(meaningful_numeric, preferred_metric)
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
                "A chart cannot be recommended for this dataset yet."
            )

    elif selected_chart_type == "histogram":

        if meaningful_numeric:

            numeric_column = meaningful_numeric[0]

            fig = create_histogram(
                df,
                column=numeric_column
            )

            st.plotly_chart(fig)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    else:

        st.warning(
            "A chart cannot be recommended for this dataset yet."
        )

    st.subheader("AI Assistant")
    st.caption("Suggested questions")
    render_badges([
        "Which region performs best?",
        "Which products generate the most profit?",
        "Where might the business be losing money?",
        "Which customer segment should management focus on?"
    ])

    question = st.text_input(
        "Ask a business question about your data"
    )
    if question:

        answer = answer_question(question, profile, df)

        st.success(answer)

    render_developer_debug(
        df,
        profile,
        meaningful_numeric,
        meaningful_categorical,
        business_metrics,
        data_types,
        statistics
    )
