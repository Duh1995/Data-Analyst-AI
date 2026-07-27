import pandas as pd


RETAIL_DATASET_TYPES = {
    "transactional_sales_dataset"
}
MAX_INSIGHTS = 6


def get_available_analysis(available_analyses, analysis_id):
    for analysis in available_analyses:
        if analysis.get("id") == analysis_id and analysis.get("available"):
            return analysis

    return None


def get_matched_column(analysis, concept_type, concept):
    if not analysis:
        return None

    matches = (
        analysis
        .get("matched_concepts", {})
        .get(concept_type, {})
        .get(concept, [])
    )

    if matches:
        return matches[0]

    return None


def get_metric_total(business_metrics, metric_group, column):
    metrics = (
        business_metrics
        .get(metric_group, {})
        .get("metrics_by_column", {})
        .get(column, {})
    )

    return metrics.get("total")


def format_number(value):
    if value is None:
        return "n/a"

    if abs(value) >= 1000:
        return f"{value:,.0f}"

    return f"{value:,.2f}"


def format_percent(value):
    return f"{value:.1f}%"


def make_insight(
    title,
    finding,
    impact_category,
    recommendation,
    supporting_metrics
):
    return {
        "title": title,
        "finding": finding,
        "impact_category": impact_category,
        "recommendation": recommendation,
        "supporting_metrics": supporting_metrics
    }


def clean_grouped_data(df, dimension_column, metric_column):
    if (
        df is None
        or dimension_column not in df.columns
        or metric_column not in df.columns
    ):
        return pd.DataFrame()

    clean_df = df[[dimension_column, metric_column]].dropna()

    if clean_df.empty:
        return pd.DataFrame()

    return (
        clean_df
        .groupby(dimension_column, dropna=True)[metric_column]
        .sum()
        .sort_values(ascending=False)
    )


def build_market_insights(df, dimension_column, metric_column, business_metrics):
    grouped = clean_grouped_data(df, dimension_column, metric_column)

    if len(grouped) < 2:
        return []

    top_market = grouped.index[0]
    weak_market = grouped.index[-1]
    top_sales = float(grouped.iloc[0])
    weak_sales = float(grouped.iloc[-1])
    total_sales = get_metric_total(
        business_metrics,
        "sales",
        metric_column
    )

    if total_sales in (None, 0):
        total_sales = float(grouped.sum())

    if total_sales == 0:
        return []

    top_share = (top_sales / total_sales) * 100
    weak_share = (weak_sales / total_sales) * 100
    title = "Revenue Concentration" if top_share >= 50 else "Strongest Market"
    recommendation = (
        "Protect this market while strengthening secondary regions to reduce "
        "dependency."
        if top_share >= 50
        else "Use this market as the reference point for commercial execution "
        "in lower-performing regions."
    )

    return [
        make_insight(
            title,
            (
                f"{top_market} is the primary revenue driver, generating "
                f"{format_percent(top_share)} of total sales."
            ),
            "Revenue Driver",
            recommendation,
            {
                str(top_market): f"Sales: {format_number(top_sales)}",
                "Sales Share": format_percent(top_share)
            }
        ),
        make_insight(
            "Growth Opportunity",
            (
                f"{weak_market} is materially behind the other markets and "
                f"contributes only {format_percent(weak_share)} of sales."
            ),
            "Market Opportunity",
            (
                "Review local demand, sales coverage and product mix in this "
                "market before allocating growth resources."
            ),
            {
                str(weak_market): f"Sales: {format_number(weak_sales)}",
                "Sales Share": format_percent(weak_share)
            }
        )
    ]


def build_product_opportunity_insight(
    df,
    dimension_column,
    metric_column,
    business_metrics
):
    grouped = clean_grouped_data(df, dimension_column, metric_column)

    if len(grouped) < 2:
        return None

    top_product = grouped.index[0]
    top_sales = float(grouped.iloc[0])
    total_sales = get_metric_total(
        business_metrics,
        "sales",
        metric_column
    )

    if total_sales in (None, 0):
        total_sales = float(grouped.sum())

    if total_sales == 0:
        return None

    top_share = (top_sales / total_sales) * 100

    return make_insight(
        "Product Opportunity",
        (
            f"{top_product} is the strongest product category and accounts "
            f"for {format_percent(top_share)} of sales."
        ),
        "Growth Opportunity",
        (
            "Prioritize inventory, merchandising and campaign investment "
            "around this category."
        ),
        {
            str(top_product): f"Sales: {format_number(top_sales)}",
            "Sales Share": format_percent(top_share)
        }
    )


def build_profitability_risk_insight(df, dimension_column, metric_column):
    grouped = clean_grouped_data(df, dimension_column, metric_column)

    if len(grouped) < 2:
        return None

    weak_product = grouped.index[-1]
    weak_profit = float(grouped.iloc[-1])

    return make_insight(
        "Profitability Risk",
        (
            f"{weak_product} consistently underperforms compared to the "
            f"remaining product categories."
        ),
        "Profitability Risk",
        (
            "Review pricing strategy, discounts and operating costs for this "
            "category."
        ),
        {
            str(weak_product): f"Profit: {format_number(weak_profit)}"
        }
    )


def build_customer_opportunity_insight(df, dimension_column, metric_column):
    grouped = clean_grouped_data(df, dimension_column, metric_column)

    if len(grouped) < 2:
        return None

    best_name = grouped.index[0]
    worst_name = grouped.index[-1]
    best_value = float(grouped.iloc[0])
    worst_value = float(grouped.iloc[-1])
    difference = best_value - worst_value

    if difference == 0:
        return None

    return make_insight(
        "Customer Opportunity",
        (
            f"{best_name} materially outperforms {worst_name}, creating a "
            f"{format_number(difference)} sales gap between segments."
        ),
        "Customer Opportunity",
        (
            "Focus campaigns on the strongest segment while reviewing the "
            "offer and acquisition strategy for weaker segments."
        ),
        {
            str(best_name): f"Sales: {format_number(best_value)}",
            str(worst_name): f"Sales: {format_number(worst_value)}"
        }
    )


def build_discount_impact_insight(df, discount_column, profit_column):
    if (
        df is None
        or discount_column not in df.columns
        or profit_column not in df.columns
    ):
        return None

    clean_df = df[[discount_column, profit_column]].dropna()

    if len(clean_df) < 4 or clean_df[discount_column].nunique() < 2:
        return None

    median_discount = clean_df[discount_column].median()
    low_discount_profit = clean_df[
        clean_df[discount_column] <= median_discount
    ][profit_column].mean()
    high_discount_profit = clean_df[
        clean_df[discount_column] > median_discount
    ][profit_column].mean()

    if pd.isna(low_discount_profit) or pd.isna(high_discount_profit):
        return None

    difference = float(high_discount_profit - low_discount_profit)

    if difference == 0:
        return None

    if difference < 0:
        return make_insight(
            "Business Risk",
            (
                "High-discount records produce lower average profitability "
                "than low-discount records."
            ),
            "Cost Risk",
            "Review discount policies and approval rules to improve margins.",
            {
                "Low-discount profit": format_number(float(low_discount_profit)),
                "High-discount profit": format_number(float(high_discount_profit))
            }
        )

    return make_insight(
        "Efficiency Opportunity",
        (
            "High-discount records produce higher average profitability than "
            "low-discount records."
        ),
        "Efficiency Opportunity",
        (
            "Identify where discounts are supporting profitable conversion "
            "and apply that discipline selectively."
        ),
        {
            "Low-discount profit": format_number(float(low_discount_profit)),
            "High-discount profit": format_number(float(high_discount_profit))
        }
    )


def append_if_present(insights, insight):
    if insight:
        insights.append(insight)


def build_retail_sales_insights(profile, df):
    business_metrics = profile.get("business_metrics", {})
    available_analyses = profile.get("available_analyses", [])
    insights = []

    sales_by_geography = get_available_analysis(
        available_analyses,
        "sales_by_geography"
    )
    sales_geo_column = get_matched_column(
        sales_by_geography,
        "dimensions",
        "geography"
    )
    sales_column = get_matched_column(
        sales_by_geography,
        "metrics",
        "sales"
    )

    if sales_geo_column and sales_column:
        insights.extend(
            build_market_insights(
                df,
                sales_geo_column,
                sales_column,
                business_metrics
            )
        )

    sales_by_product = get_available_analysis(
        available_analyses,
        "sales_by_product_category"
    )
    product_column = get_matched_column(
        sales_by_product,
        "dimensions",
        "product_category"
    )
    product_sales_column = get_matched_column(
        sales_by_product,
        "metrics",
        "sales"
    )

    if product_column and product_sales_column:
        append_if_present(
            insights,
            build_product_opportunity_insight(
                df,
                product_column,
                product_sales_column,
                business_metrics
            )
        )

    profitability_by_product = get_available_analysis(
        available_analyses,
        "profitability_by_product_category"
    )
    profit_product_column = get_matched_column(
        profitability_by_product,
        "dimensions",
        "product_category"
    )
    profit_column = get_matched_column(
        profitability_by_product,
        "metrics",
        "profitability"
    )

    if profit_product_column and profit_column:
        append_if_present(
            insights,
            build_profitability_risk_insight(
                df,
                profit_product_column,
                profit_column
            )
        )

    sales_by_segment = get_available_analysis(
        available_analyses,
        "sales_by_customer_segment"
    )
    segment_column = get_matched_column(
        sales_by_segment,
        "dimensions",
        "customer_segment"
    )
    segment_sales_column = get_matched_column(
        sales_by_segment,
        "metrics",
        "sales"
    )

    append_if_present(
        insights,
        build_customer_opportunity_insight(
            df,
            segment_column,
            segment_sales_column
        )
    )

    discount_analysis = get_available_analysis(
        available_analyses,
        "discount_vs_profitability"
    )
    discount_column = get_matched_column(
        discount_analysis,
        "metrics",
        "discount"
    )
    discount_profit_column = get_matched_column(
        discount_analysis,
        "metrics",
        "profitability"
    )

    append_if_present(
        insights,
        build_discount_impact_insight(
            df,
            discount_column,
            discount_profit_column
        )
    )

    return insights[:MAX_INSIGHTS]


def build_business_insights(profile, df):
    dataset_type = (
        profile
        .get("business_diagnosis", {})
        .get("dataset_type")
    )

    if dataset_type not in RETAIL_DATASET_TYPES:
        return []

    return build_retail_sales_insights(profile, df)
