import pandas as pd


RETAIL_DATASET_TYPES = {
    "transactional_sales_dataset",
    "financial_or_sales_dataset",
    "customer_dataset",
    "product_dataset",
    "general_business_dataset"
}

PARETO_THRESHOLD = 80
ABC_A_THRESHOLD = 80
ABC_B_THRESHOLD = 95


def format_number(value):
    if value is None:
        return "n/a"

    if abs(value) >= 1000:
        return f"{value:,.0f}"

    return f"{value:,.2f}"


def format_percent(value):
    if value is None:
        return "n/a"

    return f"{value:.1f}%"


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


def build_analysis_result(analysis_id, title, grain, metric, findings, metrics):
    return {
        "analysis_id": analysis_id,
        "title": title,
        "grain": grain,
        "metric": metric,
        "findings": findings,
        "metrics": metrics
    }


def clean_grouped_data(df, dimension_column, metric_column):
    if (
        df is None
        or dimension_column not in df.columns
        or metric_column not in df.columns
    ):
        return pd.Series(dtype="float64")

    clean_df = df[[dimension_column, metric_column]].dropna()

    if clean_df.empty:
        return pd.Series(dtype="float64")

    grouped = (
        clean_df
        .groupby(dimension_column, dropna=True)[metric_column]
        .sum()
        .sort_values(ascending=False)
    )

    return grouped[grouped != 0]


def calculate_concentration(grouped):
    if grouped.empty:
        return None

    total = float(grouped.sum())

    if total == 0:
        return None

    top_name = grouped.index[0]
    top_value = float(grouped.iloc[0])
    top_share = (top_value / total) * 100
    top_three_value = float(grouped.head(3).sum())
    top_three_share = (top_three_value / total) * 100

    return {
        "top_name": str(top_name),
        "top_value": round(top_value, 2),
        "top_share": round(top_share, 2),
        "top_three_share": round(top_three_share, 2),
        "total": round(total, 2),
        "item_count": int(len(grouped))
    }


def build_concentration_analysis(
    analysis_id,
    title,
    grain,
    metric_label,
    grouped
):
    concentration = calculate_concentration(grouped)

    if not concentration:
        return None

    findings = [
        (
            f"{concentration['top_name']} contributes "
            f"{format_percent(concentration['top_share'])} of {metric_label}."
        ),
        (
            f"The top 3 {grain} values contribute "
            f"{format_percent(concentration['top_three_share'])} of {metric_label}."
        )
    ]
    metrics = {
        "top_name": concentration["top_name"],
        "top_value": format_number(concentration["top_value"]),
        "top_share": format_percent(concentration["top_share"]),
        "top_three_share": format_percent(concentration["top_three_share"]),
        "total": format_number(concentration["total"]),
        "item_count": concentration["item_count"]
    }

    return build_analysis_result(
        analysis_id,
        title,
        grain,
        metric_label,
        findings,
        metrics
    )


def build_pareto_analysis(grouped, grain, metric_label):
    if len(grouped) < 2:
        return None

    total = float(grouped.sum())

    if total == 0:
        return None

    cumulative_share = (grouped.cumsum() / total) * 100
    pareto_items = cumulative_share[cumulative_share <= PARETO_THRESHOLD]

    if pareto_items.empty:
        item_count = 1
    else:
        item_count = int(len(pareto_items))

        if item_count < len(grouped) and cumulative_share.iloc[item_count - 1] < PARETO_THRESHOLD:
            item_count += 1

    item_share = (item_count / len(grouped)) * 100
    actual_share = float(cumulative_share.iloc[item_count - 1])
    top_items = [str(item) for item in grouped.head(item_count).index]
    findings = [
        (
            f"{item_count} of {len(grouped)} {grain} values generate "
            f"{format_percent(actual_share)} of {metric_label}."
        ),
        (
            f"Those {grain} values represent {format_percent(item_share)} "
            "of the available base."
        )
    ]

    return build_analysis_result(
        f"pareto_{grain}_{metric_label}",
        f"Pareto Analysis - {grain.title()} {metric_label.title()}",
        grain,
        metric_label,
        findings,
        {
            "pareto_threshold": format_percent(PARETO_THRESHOLD),
            "pareto_item_count": item_count,
            "total_item_count": int(len(grouped)),
            "pareto_item_share": format_percent(item_share),
            "pareto_metric_share": format_percent(actual_share),
            "top_items": top_items
        }
    )


def build_abc_classification(grouped, grain, metric_label):
    if len(grouped) < 2:
        return None

    total = float(grouped.sum())

    if total == 0:
        return None

    cumulative_share = (grouped.cumsum() / total) * 100
    classes = {
        "A": [],
        "B": [],
        "C": []
    }

    for item_name, share in cumulative_share.items():
        if share <= ABC_A_THRESHOLD:
            classes["A"].append(str(item_name))
        elif share <= ABC_B_THRESHOLD:
            classes["B"].append(str(item_name))
        else:
            classes["C"].append(str(item_name))

    if not classes["A"] and len(grouped) > 0:
        first_item = str(grouped.index[0])
        classes["A"].append(first_item)

        for class_name in ["B", "C"]:
            if first_item in classes[class_name]:
                classes[class_name].remove(first_item)

    findings = [
        f"Class A contains {len(classes['A'])} {grain} value(s).",
        f"Class B contains {len(classes['B'])} {grain} value(s).",
        f"Class C contains {len(classes['C'])} {grain} value(s)."
    ]

    return build_analysis_result(
        f"abc_{grain}_{metric_label}",
        f"ABC Classification - {grain.title()} {metric_label.title()}",
        grain,
        metric_label,
        findings,
        {
            "class_a_count": len(classes["A"]),
            "class_b_count": len(classes["B"]),
            "class_c_count": len(classes["C"]),
            "class_a_items": classes["A"],
            "class_b_items": classes["B"],
            "class_c_items": classes["C"]
        }
    )


def build_dependency_analysis(
    analysis_id,
    title,
    grain,
    metric_label,
    grouped
):
    concentration = calculate_concentration(grouped)

    if not concentration:
        return None

    dependency_level = "high" if concentration["top_share"] >= 50 else "moderate"
    findings = [
        (
            f"{concentration['top_name']} is the largest {grain} dependency "
            f"at {format_percent(concentration['top_share'])} of {metric_label}."
        ),
        f"Dependency level is {dependency_level}."
    ]

    return build_analysis_result(
        analysis_id,
        title,
        grain,
        metric_label,
        findings,
        {
            "dependency_name": concentration["top_name"],
            "dependency_share": format_percent(concentration["top_share"]),
            "dependency_level": dependency_level
        }
    )


def build_discount_effectiveness(df, discount_column, profit_column):
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
    effectiveness = (
        "positive"
        if difference > 0
        else "negative"
        if difference < 0
        else "neutral"
    )
    findings = [
        (
            "High-discount records have "
            f"{format_number(float(high_discount_profit))} average profit."
        ),
        (
            "Low-discount records have "
            f"{format_number(float(low_discount_profit))} average profit."
        ),
        f"Discount effectiveness is {effectiveness} based on average profit."
    ]

    return build_analysis_result(
        "discount_effectiveness",
        "Discount Effectiveness",
        "discount",
        "profit",
        findings,
        {
            "median_discount": format_number(float(median_discount)),
            "low_discount_average_profit": format_number(float(low_discount_profit)),
            "high_discount_average_profit": format_number(float(high_discount_profit)),
            "profit_difference": format_number(difference),
            "effectiveness": effectiveness
        }
    )


def append_if_present(results, analysis):
    if analysis:
        results.append(analysis)


def build_advanced_retail_insights(profile, df):
    dataset_type = (
        profile
        .get("business_diagnosis", {})
        .get("dataset_type")
    )

    if dataset_type not in RETAIL_DATASET_TYPES:
        return []

    available_analyses = profile.get("available_analyses", [])
    results = []
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
    product_sales = clean_grouped_data(
        df,
        product_column,
        product_sales_column
    )

    append_if_present(
        results,
        build_dependency_analysis(
            "product_dependency",
            "Product Dependency",
            "product category",
            "revenue",
            product_sales
        )
    )
    append_if_present(
        results,
        build_pareto_analysis(product_sales, "product category", "revenue")
    )
    append_if_present(
        results,
        build_abc_classification(product_sales, "product category", "revenue")
    )
    append_if_present(
        results,
        build_concentration_analysis(
            "revenue_concentration_product_category",
            "Revenue Concentration",
            "product category",
            "revenue",
            product_sales
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
    product_profit = clean_grouped_data(
        df,
        profit_product_column,
        profit_column
    )
    positive_product_profit = product_profit[product_profit > 0]
    append_if_present(
        results,
        build_concentration_analysis(
            "profit_concentration_product_category",
            "Profit Concentration",
            "product category",
            "profit",
            positive_product_profit
        )
    )

    sales_by_segment = get_available_analysis(
        available_analyses,
        "sales_by_customer_segment"
    )
    customer_column = get_matched_column(
        sales_by_segment,
        "dimensions",
        "customer_segment"
    )
    customer_sales_column = get_matched_column(
        sales_by_segment,
        "metrics",
        "sales"
    )
    customer_sales = clean_grouped_data(
        df,
        customer_column,
        customer_sales_column
    )
    append_if_present(
        results,
        build_concentration_analysis(
            "customer_concentration",
            "Customer Concentration",
            "customer segment",
            "revenue",
            customer_sales
        )
    )
    append_if_present(
        results,
        build_dependency_analysis(
            "customer_dependency",
            "Customer Dependency",
            "customer segment",
            "revenue",
            customer_sales
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
        results,
        build_discount_effectiveness(
            df,
            discount_column,
            discount_profit_column
        )
    )

    return results
