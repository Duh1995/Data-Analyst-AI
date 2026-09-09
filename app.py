import html

import streamlit as st
import pandas as pd
from src.analysis import (
    get_data_types,
    get_statistics
)
from src.charts import (
    aggregate_metric_by_category,
    aggregate_metric_by_date,
    create_line_chart,
    create_bar_chart,
    create_scatter_chart,
    create_histogram
)
from src.analysis_catalog import get_analysis_catalog
from src.ai.conversation_manager import ConversationManager
from src.profiler import build_profile
from src.qa import answer_question, get_suggested_questions
from src.data_loader import DataLoadingError, load_data
from src.domain_registry import get_domain_display_name, is_supported_domain
from src.product_plan import (
    FREE_PLAN,
    PRO_PLAN,
    can_consume_usage,
    get_current_plan,
    get_plan_display_name
)


st.set_page_config(
    page_title="InsightFlow | Business Intelligence",
    page_icon=":bar_chart:"
)


def render_app_styles():
    st.markdown(
        """
        <style>
        :root {
            --if-bg: #0d1117;
            --if-panel: #151b24;
            --if-panel-muted: #111821;
            --if-border: rgba(148, 163, 184, 0.2);
            --if-text: #f4f7fb;
            --if-muted: #9aa8ba;
            --if-blue: #5b9cff;
            --if-purple: #9b7cff;
        }

        .stApp {
            background: var(--if-bg);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stFileUploader"] {
            background: var(--if-panel);
            border: 1px solid var(--if-border);
            border-radius: 8px;
            padding: 0.65rem;
        }

        [data-testid="stFileUploader"] section {
            border: 1px dashed rgba(91, 156, 255, 0.58);
            border-radius: 6px;
            background: var(--if-panel-muted);
        }

        div[data-testid="stMetric"] {
            background: var(--if-panel);
            border: 1px solid var(--if-border);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }

        .if-hero {
            border-bottom: 1px solid var(--if-border);
            padding: 1.1rem 0 1.65rem;
            margin-bottom: 1.35rem;
        }

        .if-eyebrow {
            color: var(--if-blue);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }

        .if-hero h1 {
            color: var(--if-text);
            font-size: clamp(2.15rem, 5vw, 3.6rem);
            line-height: 1.05;
            margin: 0;
        }

        .if-hero p {
            color: var(--if-muted);
            font-size: 1.08rem;
            margin: 0.8rem 0 0;
            max-width: 600px;
        }

        .if-upload-label {
            color: var(--if-text);
            font-size: 1rem;
            font-weight: 650;
            margin: 0 0 0.35rem;
        }

        .if-upload-note {
            color: var(--if-muted);
            font-size: 0.88rem;
            margin: 0.7rem 0 0;
        }

        .if-scope {
            border-left: 3px solid var(--if-purple);
            color: var(--if-muted);
            font-size: 0.9rem;
            margin-top: 1.15rem;
            padding: 0.1rem 0 0.1rem 0.8rem;
        }

        .if-scope strong {
            color: var(--if-text);
            font-weight: 650;
        }

        .if-dataset-header {
            align-items: baseline;
            border-bottom: 1px solid var(--if-border);
            display: flex;
            gap: 0.7rem;
            justify-content: space-between;
            margin: 0.25rem 0 1.4rem;
            padding-bottom: 0.9rem;
        }

        .if-dataset-name {
            color: var(--if-text);
            font-size: 1.15rem;
            font-weight: 700;
        }

        .if-dataset-meta {
            color: var(--if-muted);
            font-size: 0.84rem;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-top: 1.25rem;
            }

            .if-dataset-header {
                align-items: flex-start;
                flex-direction: column;
                gap: 0.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_landing_header(container=None):
    target = container or st
    target.markdown(
        """
        <section class="if-hero">
            <div class="if-eyebrow">Business intelligence for better decisions</div>
            <h1>From Data to Decisions</h1>
            <p>Turn your business data into a clear view of what is happening and what deserves attention.</p>
        </section>
        """,
        unsafe_allow_html=True
    )


def render_dataset_header(uploaded_file):
    header_column, action_column = st.columns([5, 1])

    with header_column:
        st.markdown(
            (
                '<div class="if-dataset-header">'
                f'<span class="if-dataset-name">{html.escape(uploaded_file.name)}</span>'
                f'<span class="if-dataset-meta">{get_plan_display_name()} plan - ready for analysis</span>'
                '</div>'
            ),
            unsafe_allow_html=True
        )

    with action_column:
        if st.button("Change dataset", key="change_dataset"):
            st.session_state.dataset_upload_version = (
                st.session_state.get("dataset_upload_version", 0) + 1
            )
            st.rerun()


BUSINESS_AREA_CONFIG = {
    "Sales": {
        "description": "Understand how your revenue and sales performance are evolving."
    },
    "Profitability": {
        "description": "Understand where your business is creating or losing margin."
    },
    "Customers": {
        "description": "Understand your customer base and concentration."
    },
    "Products": {
        "description": "Understand which products drive your business."
    }
}


def render_main_navigation():
    return st.radio(
        "Business area",
        ["Overview", *BUSINESS_AREA_CONFIG],
        horizontal=True,
        key="main_navigation",
        label_visibility="collapsed"
    )


def render_kpi_card(
    label,
    value=None,
    comparison=None,
    status=None,
    supporting_text=None
):
    display_value = "Not available" if value is None else value
    metric_help = supporting_text or status
    st.metric(label, display_value, delta=comparison, help=metric_help)


def render_analysis_grid(analysis_cards=None):
    analysis_cards = list(analysis_cards or [])[:4]

    if not analysis_cards:
        st.caption("Area-specific analyses will appear when they are available.")
        return

    columns = st.columns(2)
    for index, analysis in enumerate(analysis_cards):
        with columns[index % 2]:
            render_card(
                analysis.get("title", "Business analysis"),
                html.escape(analysis.get("description", "Analysis available.")),
                accent="#5b9cff"
            )


def render_analysis_coverage(area, has_analysis=False, missing_concepts=None):
    if has_analysis:
        return

    missing_text = ""
    if missing_concepts:
        missing_text = " Missing concepts: " + ", ".join(missing_concepts) + "."

    st.info(
        f"Based on the information available in your dataset, InsightFlow "
        f"could only provide a limited analysis of {area.lower()}."
        f"{missing_text}"
    )


def render_custom_analysis_entry(key):
    with st.expander("Create Custom Analysis", expanded=False):
        st.caption("Build a supported business view from the available dataset concepts.")
        st.selectbox("Metric", ["Available in a future analysis step"], key=f"{key}_metric", disabled=True)
        st.selectbox("Dimension", ["Available in a future analysis step"], key=f"{key}_dimension", disabled=True)
        st.button("Create analysis", key=f"{key}_submit", disabled=True)


def render_ask_insightflow_entry(key):
    with st.expander("Ask InsightFlow", expanded=False):
        st.caption("Ask a business question from the Overview AI Assistant.")
        st.text_input(
            "What would you like to know?",
            placeholder="Ask about your business...",
            key=f"{key}_question",
            disabled=True
        )


def render_key_business_insight(insight=None):
    st.markdown("**Key business insight**")

    if not insight:
        st.caption("No area-specific insight is available yet.")
        return

    insight_text = insight.get("finding") or insight.get("title", "Business insight")
    body = html.escape(str(insight_text))
    recommendation = insight.get("recommendation")
    if recommendation:
        body += f"<br><strong>Recommended action:</strong> {html.escape(str(recommendation))}"

    render_card(
        insight.get("title", "Business insight"),
        body,
        accent="#5b9cff"
    )


def render_business_area_page(area, profile, business_insights=None):
    config = BUSINESS_AREA_CONFIG[area]
    st.header(area)
    st.caption(config["description"])

    kpi_columns = st.columns(3)
    for index, label in enumerate(("Primary KPI", "Secondary KPI", "Supporting KPI")):
        with kpi_columns[index]:
            render_kpi_card(
                label,
                supporting_text="Area-specific KPI selection will be added in the next unit."
            )

    st.subheader("Analyses")
    render_analysis_grid()
    render_analysis_coverage(area)

    action_columns = st.columns(2)
    with action_columns[0]:
        render_custom_analysis_entry(f"{area.lower()}_custom")
    with action_columns[1]:
        render_ask_insightflow_entry(f"{area.lower()}_ask")

    render_key_business_insight()


SALES_ANALYSIS_PRIORITY = [
    "sales_over_time",
    "sales_by_product_category",
    "sales_by_geography",
    "sales_by_customer_segment"
]


def get_sales_kpis(profile):
    business_metrics = profile.get("business_metrics", {})
    kpis = []

    for area, label in (("sales", "Revenue"), ("profitability", "Profit")):
        metric_group = business_metrics.get(area, {})
        for column, values in metric_group.get("metrics_by_column", {}).items():
            if values.get("total") is not None:
                metric_label = (
                    "Margin"
                    if area == "profitability"
                    and "margin" in str(column).lower()
                    and "profit" not in str(column).lower()
                    else label
                )
                kpis.append({
                    "label": metric_label,
                    "value": format_overview_value(values["total"]),
                    "supporting_text": str(column)
                })
                break

    customer_metrics = business_metrics.get("customers", {})
    for column, value in customer_metrics.get("unique_counts", {}).items():
        kpis.append({
            "label": "Customers",
            "value": format_overview_value(value),
            "supporting_text": str(column)
        })
        break

    if len(kpis) < 3:
        sales_metrics = business_metrics.get("sales", {})
        for column, values in sales_metrics.get("metrics_by_column", {}).items():
            if values.get("count") is not None:
                kpis.append({
                    "label": "Sales records",
                    "value": format_overview_value(values["count"]),
                    "supporting_text": str(column)
                })
                break

    if len(kpis) < 3:
        kpis.append({
            "label": "Records",
            "value": format_overview_value(profile.get("rows", 0)),
            "supporting_text": "Dataset"
        })

    return kpis[:3]


def get_sales_analyses(available_analyses, analysis_catalog):
    catalog_by_id = get_analysis_by_id(analysis_catalog)
    available_by_id = get_available_analysis_by_id(available_analyses)
    selected = []

    for analysis_id in SALES_ANALYSIS_PRIORITY:
        resolved = available_by_id.get(analysis_id)
        if resolved and resolved.get("available"):
            selected.append({
                **catalog_by_id.get(analysis_id, {}),
                **resolved
            })

    return selected[:4]


def render_sales_analysis_card(df, analysis):
    matched_concepts = analysis.get("matched_concepts", {})
    metrics = matched_concepts.get("metrics", {})
    dimensions = matched_concepts.get("dimensions", {})
    metric_column = next(iter(metrics.values()), [None])[0]
    dimension_column = next(iter(dimensions.values()), [None])[0]

    if not metric_column:
        return False

    with st.container(border=True):
        st.markdown(f"**{html.escape(analysis.get('title', 'Sales analysis'))}**")
        st.caption(analysis.get("business_question", "Deterministic sales analysis."))

        if analysis.get("preferred_chart") == "line" and dimension_column:
            chart_df = aggregate_metric_by_date(df, dimension_column, metric_column)
            if chart_df.empty:
                st.caption("No valid time values are available for this analysis.")
                return False
            figure = create_line_chart(chart_df, dimension_column, metric_column)
        elif analysis.get("preferred_chart") == "bar" and dimension_column:
            chart_df = aggregate_metric_by_category(df, dimension_column, metric_column)
            if chart_df.empty:
                st.caption("No complete category values are available for this analysis.")
                return False
            figure = create_bar_chart(chart_df, dimension_column, metric_column)
        else:
            return False

        st.plotly_chart(figure, use_container_width=True)

    return True


def render_sales_custom_analysis(df, profile):
    metric_options = list(profile.get("meaningful_numeric_columns", []))
    dimension_options = []
    if profile.get("date_column"):
        dimension_options.append(profile["date_column"])
    dimension_options.extend(profile.get("meaningful_categorical_columns", []))

    with st.expander("Create Custom Analysis", expanded=False):
        if not metric_options:
            st.info("A custom sales analysis needs at least one valid numeric metric.")
            return

        metric = st.selectbox("Metric", metric_options, key="sales_custom_metric")
        dimension = st.selectbox(
            "Dimension",
            ["No dimension", *dimension_options],
            key="sales_custom_dimension"
        )
        aggregation = st.selectbox("Aggregation", ["Sum"], key="sales_custom_aggregation")
        chart_options = (
            ["Line"]
            if dimension == profile.get("date_column")
            else (["Bar"] if dimension != "No dimension" else ["Histogram"])
        )
        chart_type = st.selectbox(
            "Chart type",
            chart_options,
            key="sales_custom_chart_type"
        )

        if not st.button("Create analysis", key="sales_custom_submit", type="primary"):
            return

        if chart_type == "Line":
            result = aggregate_metric_by_date(df, dimension, metric)
            figure = create_line_chart(result, dimension, metric)
        elif chart_type == "Bar":
            result = aggregate_metric_by_category(df, dimension, metric)
            figure = create_bar_chart(result, dimension, metric)
        else:
            figure = create_histogram(df, metric)

        with st.container(border=True):
            st.markdown("**Custom sales analysis**")
            st.caption(f"{metric} - {aggregation} - {chart_type}")
            st.plotly_chart(figure, use_container_width=True)


def get_sales_insight(business_insights):
    sales_terms = ("sales", "revenue", "commercial", "customer")
    for insight in business_insights:
        text = " ".join(
            str(insight.get(key, ""))
            for key in ("title", "finding", "recommendation")
        ).lower()
        if any(term in text for term in sales_terms):
            return insight
    return None


def render_sales_ai_entry(profile, dataset_name):
    with st.expander("Ask InsightFlow", expanded=False):
        st.caption("Ask a sales question grounded in the available Business Knowledge.")
        question = st.text_input(
            "What would you like to know?",
            placeholder="Which products generate the most sales?",
            key="sales_ai_question"
        )
        submitted = st.button("Ask InsightFlow", key="sales_ai_submit", type="primary")

        dataset_key = f"{dataset_name}:sales"
        if st.session_state.get("sales_ai_dataset_key") != dataset_key:
            st.session_state.sales_ai_dataset_key = dataset_key
            st.session_state.sales_ai_conversation_manager = ConversationManager()

        if submitted and question.strip():
            questions_used = st.session_state.get("ai_questions_used", 0)
            if can_consume_usage("ai_questions_per_session", questions_used):
                answer_question(
                    question.strip(),
                    profile,
                    conversation_manager=st.session_state.sales_ai_conversation_manager
                )
                st.session_state.ai_questions_used = questions_used + 1
            else:
                st.info("The Free plan AI question limit has been reached.")

        render_ai_conversation(st.session_state.sales_ai_conversation_manager)


def render_sales_page(df, profile, dataset_name):
    st.header("Sales")
    st.caption("Understand how your revenue and sales performance are evolving.")

    kpis = get_sales_kpis(profile)
    kpi_columns = st.columns(3)
    for column, kpi in zip(kpi_columns, kpis):
        with column:
            render_kpi_card(
                kpi["label"],
                kpi["value"],
                supporting_text=kpi["supporting_text"]
            )

    analysis_catalog = get_analysis_catalog()
    sales_analyses = get_sales_analyses(
        profile.get("available_analyses", []),
        analysis_catalog
    )

    st.subheader("Sales analyses")
    rendered_count = 0
    for index in range(0, len(sales_analyses), 2):
        columns = st.columns(2)
        for column, analysis in zip(columns, sales_analyses[index:index + 2]):
            with column:
                if render_sales_analysis_card(df, analysis):
                    rendered_count += 1

    render_analysis_coverage("sales", has_analysis=rendered_count == 4)
    render_sales_custom_analysis(df, profile)
    render_sales_ai_entry(profile, dataset_name)
    render_key_business_insight(get_sales_insight(profile.get("business_insights", [])))


PROFITABILITY_ANALYSIS_PRIORITY = [
    "profitability_over_time",
    "profitability_by_product_category",
    "discount_vs_profitability",
    "profitability_by_geography",
    "profitability_by_customer_segment"
]


def get_profitability_kpis(profile):
    business_metrics = profile.get("business_metrics", {})
    kpis = []
    profitability_metrics = business_metrics.get("profitability", {})
    metric_items = list(profitability_metrics.get("metrics_by_column", {}).items())
    metric_items.sort(
        key=lambda item: "profit" not in str(item[0]).lower()
    )

    for column, values in metric_items:
        if values.get("total") is None:
            continue
        label = (
            "Margin"
            if "margin" in str(column).lower()
            and "profit" not in str(column).lower()
            else "Profit"
        )
        kpis.append({
            "label": label,
            "value": format_overview_value(values["total"]),
            "supporting_text": str(column)
        })
        if len(kpis) == 2:
            break

    sales_metrics = business_metrics.get("sales", {})
    for column, values in sales_metrics.get("metrics_by_column", {}).items():
        if values.get("total") is not None:
            kpis.append({
                "label": "Revenue",
                "value": format_overview_value(values["total"]),
                "supporting_text": str(column)
            })
            break

    if len(kpis) < 3:
        for column, values in sales_metrics.get("metrics_by_column", {}).items():
            if values.get("count") is not None:
                kpis.append({
                    "label": "Sales records",
                    "value": format_overview_value(values["count"]),
                    "supporting_text": str(column)
                })
                break

    if len(kpis) < 3:
        kpis.append({
            "label": "Records",
            "value": format_overview_value(profile.get("rows", 0)),
            "supporting_text": "Dataset"
        })

    while len(kpis) < 3:
        kpis.append({
            "label": "Profitability metric",
            "value": None,
            "supporting_text": "Not available in this dataset"
        })

    return kpis[:3]


def render_profitability_analysis_card(df, analysis):
    matched_concepts = analysis.get("matched_concepts", {})
    metrics = matched_concepts.get("metrics", {})
    dimensions = matched_concepts.get("dimensions", {})
    metric_column = next(iter(metrics.values()), [None])[0]
    dimension_column = next(iter(dimensions.values()), [None])[0]

    if not metric_column:
        return False

    with st.container(border=True):
        st.markdown(f"**{html.escape(analysis.get('title', 'Profitability analysis'))}**")
        st.caption(analysis.get("business_question", "Deterministic profitability analysis."))

        if analysis.get("preferred_chart") == "line" and dimension_column:
            chart_df = aggregate_metric_by_date(df, dimension_column, metric_column)
            if chart_df.empty:
                st.caption("No valid time values are available for this analysis.")
                return False
            figure = create_line_chart(chart_df, dimension_column, metric_column)
        elif analysis.get("preferred_chart") == "bar" and dimension_column:
            chart_df = aggregate_metric_by_category(df, dimension_column, metric_column)
            if chart_df.empty:
                st.caption("No complete category values are available for this analysis.")
                return False
            figure = create_bar_chart(chart_df, dimension_column, metric_column)
        elif analysis.get("preferred_chart") == "scatter":
            discount_column = metrics.get("discount", [None])[0]
            profitability_column = metrics.get("profitability", [None])[0]
            if not discount_column or not profitability_column:
                return False
            figure = create_scatter_chart(df, discount_column, profitability_column)
        else:
            return False

        st.plotly_chart(figure, use_container_width=True)

    return True


def get_profitability_analyses(available_analyses, analysis_catalog):
    catalog_by_id = get_analysis_by_id(analysis_catalog)
    available_by_id = get_available_analysis_by_id(available_analyses)
    selected = []

    for analysis_id in PROFITABILITY_ANALYSIS_PRIORITY:
        resolved = available_by_id.get(analysis_id)
        if resolved and resolved.get("available"):
            selected.append({
                **catalog_by_id.get(analysis_id, {}),
                **resolved
            })

    return selected[:4]


def render_profitability_custom_analysis(df, profile):
    metric_options = list(profile.get("meaningful_numeric_columns", []))
    dimension_options = []
    if profile.get("date_column"):
        dimension_options.append(profile["date_column"])
    dimension_options.extend(profile.get("meaningful_categorical_columns", []))

    with st.expander("Create Custom Analysis", expanded=False):
        if not metric_options:
            st.info("A custom profitability analysis needs at least one valid numeric metric.")
            return

        metric = st.selectbox("Metric", metric_options, key="profitability_custom_metric")
        dimension = st.selectbox(
            "Dimension",
            ["No dimension", *dimension_options],
            key="profitability_custom_dimension"
        )
        aggregation = st.selectbox(
            "Aggregation",
            ["Sum"],
            key="profitability_custom_aggregation"
        )
        chart_type = st.selectbox(
            "Chart type",
            ["Line"] if dimension == profile.get("date_column")
            else (["Bar"] if dimension != "No dimension" else ["Histogram"]),
            key="profitability_custom_chart_type"
        )

        if not st.button(
            "Create analysis",
            key="profitability_custom_submit",
            type="primary"
        ):
            return

        if chart_type == "Line":
            result = aggregate_metric_by_date(df, dimension, metric)
            figure = create_line_chart(result, dimension, metric)
        elif chart_type == "Bar":
            result = aggregate_metric_by_category(df, dimension, metric)
            figure = create_bar_chart(result, dimension, metric)
        else:
            figure = create_histogram(df, metric)

        with st.container(border=True):
            st.markdown("**Custom profitability analysis**")
            st.caption(f"{metric} - {aggregation} - {chart_type}")
            st.plotly_chart(figure, use_container_width=True)


def get_profitability_insight(business_insights):
    profitability_terms = (
        "profit",
        "margin",
        "discount",
        "cost",
        "efficiency"
    )
    for insight in business_insights:
        text = " ".join(
            str(insight.get(key, ""))
            for key in ("title", "finding", "recommendation")
        ).lower()
        if any(term in text for term in profitability_terms):
            return insight
    return None


def render_profitability_ai_entry(profile, dataset_name):
    with st.expander("Ask InsightFlow", expanded=False):
        st.caption("Ask a profitability question grounded in the available Business Knowledge.")
        question = st.text_input(
            "What would you like to know?",
            placeholder="Which products generate the most profit?",
            key="profitability_ai_question"
        )
        submitted = st.button(
            "Ask InsightFlow",
            key="profitability_ai_submit",
            type="primary"
        )

        dataset_key = f"{dataset_name}:profitability"
        if st.session_state.get("profitability_ai_dataset_key") != dataset_key:
            st.session_state.profitability_ai_dataset_key = dataset_key
            st.session_state.profitability_ai_conversation_manager = ConversationManager()

        if submitted and question.strip():
            questions_used = st.session_state.get("ai_questions_used", 0)
            if can_consume_usage("ai_questions_per_session", questions_used):
                answer_question(
                    question.strip(),
                    profile,
                    conversation_manager=st.session_state.profitability_ai_conversation_manager
                )
                st.session_state.ai_questions_used = questions_used + 1
            else:
                st.info("The Free plan AI question limit has been reached.")

        render_ai_conversation(
            st.session_state.profitability_ai_conversation_manager
        )


def render_profitability_page(df, profile, dataset_name):
    st.header("Profitability")
    st.caption("Understand where your business is creating or losing margin.")

    kpis = get_profitability_kpis(profile)
    kpi_columns = st.columns(3)
    for column, kpi in zip(kpi_columns, kpis):
        with column:
            render_kpi_card(
                kpi["label"],
                kpi["value"],
                supporting_text=kpi["supporting_text"]
            )

    analyses = get_profitability_analyses(
        profile.get("available_analyses", []),
        get_analysis_catalog()
    )

    st.subheader("Profitability analyses")
    rendered_count = 0
    for index in range(0, len(analyses), 2):
        columns = st.columns(2)
        for column, analysis in zip(columns, analyses[index:index + 2]):
            with column:
                if render_profitability_analysis_card(df, analysis):
                    rendered_count += 1

    render_analysis_coverage("profitability", has_analysis=rendered_count == 4)
    render_profitability_custom_analysis(df, profile)
    render_profitability_ai_entry(profile, dataset_name)
    render_key_business_insight(
        get_profitability_insight(profile.get("business_insights", []))
    )


render_app_styles()


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
            "<div style='border:1px solid rgba(148,163,184,0.24);"
            f"border-left:5px solid {accent};"
            "border-radius:8px;"
            "padding:0.75rem 0.85rem;"
            "margin-bottom:0.55rem;"
            "background:rgba(15,23,42,0.38);'>"
            f"<div style='font-weight:700;margin-bottom:0.35rem;'>{html.escape(str(title))}</div>"
            f"<div style='color:rgba(226,232,240,0.86);font-size:0.92rem;'>{body}</div>"
            "</div>"
        ),
        unsafe_allow_html=True
    )


def format_dataset_type(dataset_type):
    return get_domain_display_name(dataset_type)


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


def get_matched_column(resolved_analysis, concept_type, concept):
    matched_concepts = resolved_analysis.get("matched_concepts", {})
    matches = matched_concepts.get(concept_type, {}).get(concept, [])

    if matches:
        return matches[0]

    return None


def get_column_index(columns, preferred_column):
    if preferred_column in columns:
        return columns.index(preferred_column)

    return 0


def summarize_one_line(text):
    if not text:
        return "No summary available."

    return str(text).split(". ")[0].strip().rstrip(".") + "."


def build_executive_brief(profile):
    diagnosis = profile.get("business_diagnosis", {})
    business_health = profile.get("business_health", {})
    business_insights = profile.get("business_insights", [])
    advanced_retail_insights = profile.get("advanced_retail_insights", [])
    business_metrics = profile.get("business_metrics", {})
    priorities = profile.get("executive_priorities", [])
    action_plan = profile.get("executive_action_plan", [])
    lines = [
        "# InsightFlow Executive Brief",
        "",
        "## Dataset",
        f"- Business type: {format_dataset_type(diagnosis.get('dataset_type'))}",
        f"- Analysis readiness: {format_readiness(diagnosis.get('analysis_readiness'))}",
        f"- Rows: {profile.get('rows', 0)}",
        f"- Columns: {profile.get('columns', 0)}",
        f"- Missing values: {profile.get('null_count', 0)}",
        f"- Duplicate rows: {profile.get('duplicate_count', 0)}",
        f"- Business areas: {', '.join(diagnosis.get('business_areas', [])) or 'Not identified'}",
        "",
        "## Business Health"
    ]

    warnings = diagnosis.get("warnings", [])

    if warnings:
        lines.append("")
        lines.append("## Data Warnings")
        lines.extend(
            f"- {warning.get('message', 'Review this dataset.')}"
            for warning in warnings
        )

    for area, health in business_health.items():
        label = health.get("label", area)
        status = health.get("status", "unknown")
        reason = health.get("reason", "No assessment available.")
        lines.append(f"- {label}: {status}. {reason}")

    lines.append("")
    lines.append("## Business Insights")

    if business_insights:
        for insight in business_insights:
            title = insight.get("title", "Business Insight")
            finding = insight.get("finding", "No finding available.")
            recommendation = insight.get("recommendation")
            line = f"- {title}: {finding}"

            if recommendation:
                line += f" Recommendation: {recommendation}"

            lines.append(line)
    else:
        lines.append("- No deterministic business insights are available.")

    lines.append("")
    lines.append("## Advanced Retail Intelligence")

    if advanced_retail_insights:
        for analysis in advanced_retail_insights:
            findings = " ".join(analysis.get("findings", []))
            line = f"- {analysis.get('title', 'Retail Analysis')}: {findings}"
            metrics = analysis.get("metrics", {})

            if metrics:
                metric_text = "; ".join(
                    f"{label}: {value}"
                    for label, value in metrics.items()
                )
                line += f" Metrics: {metric_text}."

            lines.append(line)
    else:
        lines.append("- No advanced retail intelligence is available.")

    lines.append("")
    lines.append("## Key Metrics")

    metric_lines = []

    for area, metrics in business_metrics.items():
        for column, values in metrics.get("metrics_by_column", {}).items():
            metric_lines.append(
                f"- {area} - {column}: total {values.get('total')}, "
                f"average {values.get('average')}, count {values.get('count')}"
            )

        for column, unique_count in metrics.get("unique_counts", {}).items():
            metric_lines.append(
                f"- {area} - {column}: unique count {unique_count}"
            )

        if area == "data_quality" and not metrics.get("metrics_by_column"):
            metric_lines.append(
                "- data_quality: "
                f"null count {metrics.get('null_count', 0)}, "
                f"null percentage {metrics.get('null_percentage', 0)}, "
                f"duplicate count {metrics.get('duplicate_count', 0)}"
            )

    lines.extend(metric_lines or ["- No key metrics are available."])

    lines.append("")
    lines.append("## Executive Priorities")

    if priorities:
        for priority in priorities:
            lines.append(
                f"- #{priority.get('priority', '-')} {priority.get('title', 'Priority')}: "
                f"{priority.get('reason', 'No reason available.')}"
            )
    else:
        lines.append("- No executive priorities are available.")

    lines.append("")
    lines.append("## Executive Action Plan")

    if action_plan:
        for action in action_plan:
            lines.append(
                f"- #{action.get('implementation_priority', '-')} "
                f"{action.get('title', 'Action')}: "
                f"{action.get('recommended_action', 'No action available.')}"
            )
    else:
        lines.append("- No deterministic action plan is available.")

    lines.append("")
    lines.append("Generated by InsightFlow from deterministic Business Knowledge.")

    return "\n".join(lines)


def get_health_display(area, health):
    status = health.get("status", "unknown")
    title = health.get("label", str(area).replace("_", " ").title())
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
                        "<div style='display:grid;gap:0.3rem;'>"
                        "<div>"
                        "<span style='font-size:0.72rem;text-transform:uppercase;"
                        "letter-spacing:0;color:rgba(226,232,240,0.62);'>Status</span><br>"
                        f"<span style='font-size:1rem;font-weight:700;color:{accent};'>"
                        f"{html.escape(status)}</span>"
                        "</div>"
                        "<div style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                        f"{html.escape(summarize_one_line(reason))}</div>"
                        "</div>"
                    ),
                    accent=accent
                )


def format_overview_value(value):
    if value is None:
        return "Not available"

    if isinstance(value, float):
        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def get_overview_kpis(profile):
    business_metrics = profile.get("business_metrics", {})
    kpis = []

    metric_sources = [
        ("sales", "Sales", "total"),
        ("profitability", "Profit", "total")
    ]

    for area, label, value_key in metric_sources:
        metric_group = business_metrics.get(area, {})
        metrics_by_column = metric_group.get("metrics_by_column", {})

        for column, values in metrics_by_column.items():
            value = values.get(value_key)
            if value is not None:
                kpis.append({
                    "label": label,
                    "value": format_overview_value(value),
                    "context": str(column)
                })
                break

    customer_metrics = business_metrics.get("customers", {})
    for column, value in customer_metrics.get("unique_counts", {}).items():
        kpis.append({
            "label": "Customers",
            "value": format_overview_value(value),
            "context": str(column)
        })
        break

    if len(kpis) < 4:
        kpis.append({
            "label": "Records",
            "value": format_overview_value(profile.get("rows", 0)),
            "context": "Dataset"
        })

    return kpis[:4]


def render_overview(profile, business_health, business_insights, executive_priorities):
    st.subheader("Overview")
    st.caption("A concise view of what is happening and where to focus next.")

    kpis = get_overview_kpis(profile)
    kpi_columns = st.columns(4)

    for column, kpi in zip(kpi_columns, kpis):
        with column:
            st.metric(kpi["label"], kpi["value"], help=kpi["context"])

    overview_columns = st.columns(2)

    with overview_columns[0]:
        st.markdown("**What needs attention**")
        attention_items = [
            health
            for health in business_health.values()
            if health.get("status") == "attention"
        ]

        if attention_items:
            for health in attention_items[:2]:
                render_card(
                    health.get("label", "Business area"),
                    html.escape(summarize_one_line(health.get("reason"))),
                    accent="#dc2626"
                )
        elif executive_priorities:
            priority = executive_priorities[0]
            render_card(
                priority.get("title", "Priority"),
                html.escape(summarize_one_line(priority.get("reason"))),
                accent="#f59e0b"
            )
        else:
            st.caption("No immediate attention area was identified.")

    with overview_columns[1]:
        st.markdown("**Key business insight**")
        if business_insights:
            insight = business_insights[0]
            insight_text = insight.get("finding") or insight.get("title")
            render_card(
                insight.get("title", "Business insight"),
                html.escape(summarize_one_line(insight_text)),
                accent="#5b9cff"
            )
        elif executive_priorities:
            priority = executive_priorities[0]
            render_card(
                priority.get("title", "Recommended focus"),
                html.escape(summarize_one_line(priority.get("reason"))),
                accent="#5b9cff"
            )
        else:
            st.caption("More business context will appear as the dataset supports it.")


def render_executive_priority_card(priority, analyses_by_id):
    analysis = analyses_by_id.get(priority.get("analysis_id"), {})
    title = priority.get("title", "Recommended Analysis")
    reason = priority.get("reason", "Helps management decide where to focus first.")
    recommended_chart = format_chart_name(analysis.get("preferred_chart"))
    business_value = format_business_value(priority.get("business_value"))

    render_card(
        f"#{priority.get('priority')} {title}",
        (
            "<div style='display:grid;gap:0.35rem;'>"
            "<div style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
            f"{html.escape(summarize_one_line(reason))}</div>"
            "<div style='display:flex;gap:0.75rem;flex-wrap:wrap;"
            "color:rgba(226,232,240,0.68);font-size:0.86rem;'>"
            f"<span>Value: {html.escape(business_value)}</span>"
            f"<span>Chart: {html.escape(recommended_chart)}</span>"
            "</div>"
            "</div>"
        ),
        accent="#2563eb"
    )


def render_executive_priority_cards(executive_priorities, analysis_catalog):
    if not executive_priorities:
        st.write("No executive priorities available.")
        return

    analyses_by_id = get_analysis_by_id(analysis_catalog)
    top_priorities = executive_priorities[:3]
    remaining_priorities = executive_priorities[3:]

    for priority in top_priorities:
        render_executive_priority_card(priority, analyses_by_id)

    if remaining_priorities:
        with st.expander("See more analyses"):
            for priority in remaining_priorities:
                render_executive_priority_card(priority, analyses_by_id)


def render_executive_action_plan_cards(executive_action_plan):
    if not executive_action_plan:
        st.caption("No deterministic action plan is available for this dataset yet.")
        return

    for action in executive_action_plan:
        supporting_metrics = action.get("supporting_metrics", {})
        metrics_html = "".join(
            (
                "<span style='display:inline-block;margin:0 0.45rem 0.25rem 0;"
                "color:rgba(226,232,240,0.68);font-size:0.84rem;'>"
                f"<strong>{html.escape(str(label))}:</strong> "
                f"{html.escape(str(value))}</span>"
            )
            for label, value in supporting_metrics.items()
            if value is not None
        )
        impact = html.escape(str(action.get("expected_business_impact", "Unknown")))
        effort = html.escape(str(action.get("implementation_effort", "Unknown")))

        render_card(
            f"#{action.get('implementation_priority', '-')} {action.get('title', 'Executive Action')}",
            (
                "<div style='display:grid;gap:0.35rem;'>"
                f"<div>{html.escape(str(action.get('business_problem', '')))}</div>"
                "<div style='color:rgba(226,232,240,0.9);'>"
                f"<strong>Next step:</strong> {html.escape(str(action.get('recommended_action', '')))}"
                "</div>"
                "<div style='display:flex;gap:0.75rem;flex-wrap:wrap;"
                "color:rgba(226,232,240,0.68);font-size:0.86rem;'>"
                f"<span>Impact: {impact}</span><span>Effort: {effort}</span>"
                "</div>"
                f"<div style='display:flex;gap:0.75rem;flex-wrap:wrap;'>{metrics_html}</div>"
                "</div>"
            ),
            accent="#f59e0b"
        )


def get_available_analysis_options(available_analyses):
    return [
        analysis
        for analysis in available_analyses
        if analysis.get("available")
    ]


def format_analysis_option(analysis):
    return analysis.get("title", "Recommended Analysis")


def render_business_insight_cards(business_insights):
    if not business_insights:
        st.caption("No data-driven business insights are available for this dataset yet.")
        return

    for insight in business_insights:
        supporting_metrics = insight.get("supporting_metrics", {})
        metrics_html = "".join(
            (
                "<span style='display:inline-block;margin:0 0.45rem 0.25rem 0;"
                "color:rgba(226,232,240,0.68);font-size:0.84rem;'>"
                f"<strong>{html.escape(str(label))}:</strong> "
                f"{html.escape(str(value))}</span>"
            )
            for label, value in supporting_metrics.items()
        )
        impact_category = html.escape(str(
            insight.get("impact_category", "Business Impact")
        ))
        recommendation = html.escape(str(
            insight.get("recommendation", "")
        ))

        render_card(
            insight.get("title", "Business Insight"),
            (
                "<div style='display:grid;gap:0.35rem;'>"
                f"<div>{html.escape(str(insight.get('finding', '')))}</div>"
                "<div><span style='display:inline-block;padding:0.16rem 0.48rem;"
                "border-radius:999px;border:1px solid rgba(14,165,233,0.38);"
                "background:rgba(14,165,233,0.12);color:rgba(226,232,240,0.9);"
                "font-size:0.78rem;font-weight:700;'>"
                f"{impact_category}</span></div>"
                "<div style='color:rgba(226,232,240,0.78);'>"
                f"<strong>Recommendation:</strong> {recommendation}</div>"
                "<div style='display:flex;gap:0.75rem;flex-wrap:wrap;'>"
                f"{metrics_html}"
                "</div>"
                "</div>"
            ),
            accent="#0ea5e9"
        )


def render_advanced_retail_insight_cards(advanced_retail_insights):
    if not advanced_retail_insights:
        st.caption("No advanced retail intelligence is available for this dataset yet.")
        return

    for analysis in advanced_retail_insights:
        findings = analysis.get("findings", [])
        metrics = analysis.get("metrics", {})
        findings_html = "".join(
            f"<li>{html.escape(str(finding))}</li>"
            for finding in findings
        )
        metrics_html = "".join(
            (
                "<span style='display:inline-block;margin:0 0.45rem 0.25rem 0;"
                "color:rgba(226,232,240,0.68);font-size:0.84rem;'>"
                f"<strong>{html.escape(str(label))}:</strong> "
                f"{html.escape(str(value))}</span>"
            )
            for label, value in metrics.items()
            if value is not None
        )

        render_card(
            analysis.get("title", "Advanced Retail Analysis"),
            (
                "<div style='display:grid;gap:0.35rem;'>"
                f"<div style='color:rgba(226,232,240,0.68);font-size:0.84rem;'>"
                f"Grain: {html.escape(str(analysis.get('grain', 'business area')))} - "
                f"Metric: {html.escape(str(analysis.get('metric', 'metric')))}</div>"
                f"<ul style='margin:0;padding-left:1.2rem;'>{findings_html}</ul>"
                f"<div style='display:flex;gap:0.75rem;flex-wrap:wrap;'>{metrics_html}</div>"
                "</div>"
            ),
            accent="#14b8a6"
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


def render_ai_answer(answer):
    """Render the structured answer returned by an AI provider."""
    sections = str(answer or "").split("\n\n")

    for section in sections:
        title, separator, body = section.partition("\n")

        if separator and title in {
            "Answer",
            "Supporting Evidence",
            "Business Context",
            "Recommended Action"
        }:
            st.markdown(f"**{title}**\n\n{body}")
        else:
            st.markdown(section)


def render_ai_conversation(conversation_manager):
    for message in conversation_manager.get_history():
        role = message.get("role")
        content = message.get("content", "")

        if role not in {"user", "assistant"} or not content:
            continue

        with st.chat_message(role):
            if role == "assistant":
                render_ai_answer(content)
            else:
                st.markdown(content)


def render_see_pro(key, title, description):
    if get_current_plan() == PRO_PLAN:
        return

    st.caption(description)

    if st.button("See Pro", key=key):
        st.session_state.pro_details_visible = True

    if st.session_state.get("pro_details_visible"):
        render_card(
            title,
            "Example preview - demonstration only, not calculated from your dataset.",
            accent="#a855f7"
        )
        st.button("Coming Soon", key=f"{key}_coming_soon", disabled=True)


landing_placeholder = st.empty()
uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx"],
    key=f"dataset_upload_{st.session_state.get('dataset_upload_version', 0)}"
)

if uploaded_file is None:
    render_landing_header(landing_placeholder)
    landing_placeholder.markdown('<div class="if-upload-label">Start with your business data</div>', unsafe_allow_html=True)
    landing_placeholder.caption("CSV or XLSX files - no login required to try InsightFlow")
    landing_placeholder.markdown(
        '<div class="if-scope"><strong>Currently optimized for</strong><br>'
        'Sales - Retail - E-commerce - Products - Customers<br>'
        'Other business datasets can still be explored, but available analysis may be limited.</div>',
        unsafe_allow_html=True
    )

if uploaded_file is not None:
    dataset_key = f"{uploaded_file.name}:{uploaded_file.size}"
    datasets_used = st.session_state.get("datasets_used", [])

    if dataset_key not in datasets_used:
        if not can_consume_usage("datasets_per_session", len(datasets_used)):
            st.info("The Free plan dataset limit has been reached.")
            render_see_pro(
                "dataset_limit_pro",
                "Unlock more workspace capacity",
                "Pro is designed for larger recurring analysis workflows."
            )
            st.stop()

        st.session_state.datasets_used = [*datasets_used, dataset_key]

    try:
        df = load_data(uploaded_file)

    except DataLoadingError as error:
        st.error(str(error))
        st.stop()

    st.success("File loaded successfully.")
    render_dataset_header(uploaded_file)
    active_page = render_main_navigation()

    profile = build_profile(df)
    meaningful_numeric = profile["meaningful_numeric_columns"]
    meaningful_categorical = profile["meaningful_categorical_columns"]
    data_types = get_data_types(df)
    statistics = get_statistics(df)

    if active_page != "Overview":
        if active_page == "Sales":
            render_sales_page(
                df,
                profile,
                uploaded_file.name
            )
        elif active_page == "Profitability":
            render_profitability_page(
                df,
                profile,
                uploaded_file.name
            )
        else:
            render_business_area_page(
                active_page,
                profile,
                profile.get("business_insights", [])
            )
        st.stop()

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
    dataset_type = business_diagnosis.get("dataset_type")
    domain_is_supported = is_supported_domain(dataset_type)
    business_metrics = profile.get("business_metrics", {})
    business_health = profile.get("business_health", {})
    business_insights = profile.get("business_insights", [])
    available_analyses = profile.get("available_analyses", [])
    executive_priorities = profile.get("executive_priorities", [])
    analysis_catalog = get_analysis_catalog()
    available_analysis_count = sum(
        1
        for analysis in available_analyses
        if analysis.get("available")
    )
    recommended_catalog_analysis, recommended_resolved_analysis = get_recommended_analysis(
        executive_priorities,
        analysis_catalog,
        available_analyses
    )
    recommended_catalog_analysis = recommended_catalog_analysis or {}
    recommended_resolved_analysis = recommended_resolved_analysis or {}

    render_overview(
        profile,
        business_health,
        business_insights,
        executive_priorities
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
            "Recommended First Analysis",
            recommended_catalog_analysis.get("title", "None")
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

    if not domain_is_supported:
        st.info(
            "Business recommendations are not yet available for this domain. "
            "You can still review the dataset profile, summary, charts, and ask questions."
        )

    if domain_is_supported:
        st.subheader("Business Health")
        render_business_health_cards(business_health)

        st.subheader("Business Insights")
        render_business_insight_cards(business_insights)

        st.subheader("Advanced Retail Intelligence")
        render_advanced_retail_insight_cards(
            profile.get("advanced_retail_insights", [])
        )
        if profile.get("advanced_retail_insights"):
            render_see_pro(
                "advanced_retail_pro",
                "Unlock deeper retail intelligence",
                "Pro will add richer retail explanations and decision support here."
            )

        st.subheader("Executive Priorities")
        render_executive_priority_cards(executive_priorities, analysis_catalog)

        st.subheader("Executive Action Plan")
        render_executive_action_plan_cards(
            profile.get("executive_action_plan", [])
        )

    brief_name = uploaded_file.name.rsplit(".", 1)[0].strip() or "insightflow"
    st.download_button(
        "Download Executive Brief",
        data=build_executive_brief(profile),
        file_name=f"{brief_name}_executive_brief.md",
        mime="text/markdown"
    )

    st.subheader("Charts")
    available_analysis_options = get_available_analysis_options(available_analyses)
    selected_catalog_analysis = recommended_catalog_analysis
    selected_resolved_analysis = recommended_resolved_analysis

    if available_analysis_options:
        recommended_analysis_id = recommended_catalog_analysis.get("id")
        option_ids = [
            analysis.get("id")
            for analysis in available_analysis_options
        ]
        selected_resolved_analysis = st.selectbox(
            "Recommended First Analysis",
            available_analysis_options,
            index=get_column_index(option_ids, recommended_analysis_id),
            format_func=format_analysis_option
        )
        selected_catalog_analysis = get_analysis_by_id(analysis_catalog).get(
            selected_resolved_analysis.get("id"),
            selected_resolved_analysis
        )

    if selected_catalog_analysis:
        render_card(
            selected_catalog_analysis.get("title", "Recommended Analysis"),
            (
                "<div style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                f"{html.escape(selected_catalog_analysis.get('business_question', ''))}"
                "</div>"
            ),
            accent="#0ea5e9"
        )

    chart_names = {
        "line": "Line",
        "bar": "Bar",
        "scatter": "Scatter",
        "histogram": "Histogram"
    }
    preferred_chart = selected_catalog_analysis.get("preferred_chart")
    selected_chart_type = profile["recommended_chart"]
    scatter_x_column = get_matched_column(
        selected_resolved_analysis or {},
        "metrics",
        "discount"
    )
    scatter_y_column = get_matched_column(
        selected_resolved_analysis or {},
        "metrics",
        "profitability"
    )

    if preferred_chart == "line" and profile.get("date_column") and meaningful_numeric:
        selected_chart_type = "line"
    elif preferred_chart == "bar" and meaningful_categorical and meaningful_numeric:
        selected_chart_type = "bar"
    elif preferred_chart == "scatter" and scatter_x_column and scatter_y_column:
        selected_chart_type = "scatter"
    elif preferred_chart == "histogram" and meaningful_numeric:
        selected_chart_type = "histogram"

    chart_context = {
        "analysis": selected_catalog_analysis.get("title"),
        "business_question": selected_catalog_analysis.get("business_question"),
        "chart_type": format_chart_name(selected_chart_type)
    }

    if selected_chart_type is not None:

        st.write(
            f"Recommended chart: {chart_names[selected_chart_type]}"
        )

    if selected_chart_type == "line":

        if meaningful_numeric:
            preferred_metric = get_first_matched_column(
                selected_resolved_analysis or {},
                "metrics"
            )

            selected_column = st.selectbox(
                "Choose a business metric",
                meaningful_numeric,
                index=get_column_index(meaningful_numeric, preferred_metric)
            )

            line_df = aggregate_metric_by_date(
                df,
                profile["date_column"],
                selected_column
            )
            chart_context.update({
                "dimension": profile["date_column"],
                "metric": selected_column,
                "aggregation": "sum"
            })
            fig = create_line_chart(
                line_df,
                x_col=profile["date_column"],
                y_col=selected_column
            )

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    elif selected_chart_type == "bar":

        if meaningful_categorical and meaningful_numeric:
            preferred_dimension = get_first_matched_column(
                selected_resolved_analysis or {},
                "dimensions"
            )
            preferred_metric = get_first_matched_column(
                selected_resolved_analysis or {},
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
            bar_df = aggregate_metric_by_category(
                df,
                category_column,
                numeric_column
            )
            chart_context.update({
                "dimension": category_column,
                "metric": numeric_column,
                "aggregation": "sum"
            })
            fig = create_bar_chart(
                bar_df,
                x_col=category_column,
                y_col=numeric_column
            )

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    elif selected_chart_type == "scatter":

        if scatter_x_column and scatter_y_column:
            chart_context.update({
                "dimension": scatter_x_column,
                "metric": scatter_y_column
            })
            fig = create_scatter_chart(
                df,
                x_col=scatter_x_column,
                y_col=scatter_y_column
            )

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    elif selected_chart_type == "histogram":

        if meaningful_numeric:

            numeric_column = meaningful_numeric[0]
            chart_context.update({
                "metric": numeric_column
            })

            fig = create_histogram(
                df,
                column=numeric_column
            )

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.warning(
                "A chart cannot be recommended for this dataset yet."
            )

    else:

        st.warning(
            "A chart cannot be recommended for this dataset yet."
        )

    st.subheader("AI Assistant")
    st.caption(
        "Mock Mode - deterministic InsightFlow responses"
        if get_current_plan() == FREE_PLAN
        else "Configured AI provider - grounded in deterministic InsightFlow knowledge"
    )

    if st.session_state.get("ai_dataset_key") != dataset_key:
        st.session_state.ai_dataset_key = dataset_key
        st.session_state.ai_conversation_manager = ConversationManager()
        st.session_state.ai_question = ""
        st.session_state.ai_questions_used = 0
    elif "ai_conversation_manager" not in st.session_state:
        st.session_state.ai_conversation_manager = ConversationManager()

    suggested_questions = get_suggested_questions(
        profile.get("business_knowledge", {})
    )

    if suggested_questions:
        st.caption("Start with a business question")
        suggestion_columns = st.columns(min(len(suggested_questions), 2))

        for index, suggestion in enumerate(suggested_questions):
            with suggestion_columns[index % len(suggestion_columns)]:
                if st.button(
                    suggestion,
                    key=f"ai_suggestion_{index}",
                    use_container_width=True
                ):
                    st.session_state.ai_question = suggestion
                    st.rerun()
    else:
        st.caption("No business suggestions available for this domain.")

    with st.form("ai_question_form", clear_on_submit=True):
        question = st.text_input(
            "Ask a business question about your data",
            key="ai_question"
        )
        submitted = st.form_submit_button("Ask InsightFlow", type="primary")

    answer_generated = False

    if submitted and question.strip():
        ai_questions_used = st.session_state.get("ai_questions_used", 0)

        if can_consume_usage("ai_questions_per_session", ai_questions_used):
            answer_question(
                question.strip(),
                profile,
                conversation_manager=st.session_state.ai_conversation_manager,
                chart_context=chart_context
            )
            st.session_state.ai_questions_used = ai_questions_used + 1
            answer_generated = True
        else:
            st.info("The Free plan AI question limit has been reached.")
            render_see_pro(
                "ai_limit_pro",
                "Continue the conversation with Pro",
                "Pro is designed for deeper, recurring business conversations."
            )

    render_ai_conversation(st.session_state.ai_conversation_manager)

    if (
        answer_generated
        and get_current_plan() == FREE_PLAN
        and not profile.get("advanced_retail_insights")
    ):
        render_see_pro(
            "ai_pro_discovery",
            "Unlock more decision support",
            "Pro will extend the explanation layer around your business knowledge."
        )

    render_developer_debug(
        df,
        profile,
        meaningful_numeric,
        meaningful_categorical,
        business_metrics,
        data_types,
        statistics
    )
