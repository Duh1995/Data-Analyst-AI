from src.business_catalog import BUSINESS_AREA_KEYWORDS, METRIC_KEYWORDS


def normalize_column_name(column_name):
    return str(column_name).lower().replace("_", " ").replace("-", " ")


def column_matches_keywords(column_name, keywords):
    normalized_name = normalize_column_name(column_name)

    return any(keyword in normalized_name for keyword in keywords)


def find_columns_by_keywords(columns, keywords):
    return [
        column
        for column in columns
        if column_matches_keywords(column, keywords)
    ]


def infer_dataset_type(profile):
    searchable_columns = (
        profile.get("meaningful_numeric_columns", [])
        + profile.get("meaningful_categorical_columns", [])
        + profile.get("identifier_columns", [])
    )
    searchable_text = " ".join(
        normalize_column_name(column)
        for column in searchable_columns
    )

    has_transaction_signal = any(
        keyword in searchable_text
        for keyword in ["order", "invoice", "transaction"]
    )
    has_sales_signal = any(
        keyword in searchable_text
        for keyword in ["sales", "revenue", "profit", "amount"]
    )
    has_customer_signal = "customer" in searchable_text or "client" in searchable_text
    has_product_signal = "product" in searchable_text or "item" in searchable_text

    if has_transaction_signal and has_sales_signal:
        return "transactional_sales_dataset"

    if has_customer_signal and not has_transaction_signal:
        return "customer_dataset"

    if has_product_signal and not has_transaction_signal:
        return "product_dataset"

    if has_sales_signal:
        return "financial_or_sales_dataset"

    if profile.get("meaningful_numeric_columns") and profile.get("meaningful_categorical_columns"):
        return "general_business_dataset"

    return "limited_business_dataset"


def identify_business_areas(profile):
    business_areas = []
    searchable_columns = (
        profile.get("meaningful_numeric_columns", [])
        + profile.get("meaningful_categorical_columns", [])
        + profile.get("identifier_columns", [])
    )

    for business_area, keywords in BUSINESS_AREA_KEYWORDS.items():
        if any(
            column_matches_keywords(column, keywords)
            for column in searchable_columns
        ):
            business_areas.append(business_area)

    return business_areas


def identify_business_metrics(profile):
    metrics = []

    for column in profile.get("meaningful_numeric_columns", []):
        if column_matches_keywords(column, METRIC_KEYWORDS):
            metrics.append(column)

    if metrics:
        return metrics

    return profile.get("meaningful_numeric_columns", [])


def identify_business_dimensions(profile):
    dimensions = list(profile.get("meaningful_categorical_columns", []))

    if profile.get("date_column"):
        dimensions.append(profile["date_column"])

    return dimensions


def assess_analysis_readiness(profile, business_metrics, business_dimensions):
    row_count = profile.get("rows", 0)
    column_count = profile.get("columns", 0)

    if row_count == 0 or column_count == 0:
        return "not_ready"

    if not business_metrics:
        return "not_ready"

    if not business_dimensions:
        return "partially_ready"

    if profile.get("null_count", 0) > 0 or profile.get("duplicate_count", 0) > 0:
        return "partially_ready"

    return "ready"


def build_warnings(profile, business_metrics, business_dimensions):
    warnings = []

    if not business_metrics:
        warnings.append({
            "type": "missing_business_metrics",
            "severity": "high",
            "message": "No meaningful business metrics were identified."
        })

    if not business_dimensions:
        warnings.append({
            "type": "missing_business_dimensions",
            "severity": "medium",
            "message": "No meaningful business dimensions were identified."
        })

    if profile.get("date_column") is None:
        warnings.append({
            "type": "missing_date_column",
            "severity": "low",
            "message": "No date column was identified."
        })

    if profile.get("null_count", 0) > 0:
        warnings.append({
            "type": "null_values",
            "severity": "medium",
            "message": "The dataset contains null values."
        })

    if profile.get("duplicate_count", 0) > 0:
        warnings.append({
            "type": "duplicate_rows",
            "severity": "medium",
            "message": "The dataset contains duplicate rows."
        })

    if (
        profile.get("identifier_columns")
        and not profile.get("meaningful_numeric_columns")
        and not profile.get("meaningful_categorical_columns")
    ):
        warnings.append({
            "type": "mostly_identifier_columns",
            "severity": "high",
            "message": "The dataset appears to contain mostly identifier columns."
        })

    return warnings


def build_business_diagnosis(profile):
    business_metrics = identify_business_metrics(profile)
    business_dimensions = identify_business_dimensions(profile)

    return {
        "dataset_type": infer_dataset_type(profile),
        "business_areas": identify_business_areas(profile),
        "business_metrics": business_metrics,
        "business_dimensions": business_dimensions,
        "analysis_readiness": assess_analysis_readiness(
            profile,
            business_metrics,
            business_dimensions
        ),
        "warnings": build_warnings(
            profile,
            business_metrics,
            business_dimensions
        )
    }


def build_average_evidence(metric_group):
    evidence = []

    for column, metrics in metric_group.get("metrics_by_column", {}).items():
        if "average" in metrics:
            evidence.append({
                "metric": column,
                "average": metrics["average"]
            })

    return evidence


def assess_sales_health(profile):
    sales_metrics = profile.get("business_metrics", {}).get("sales", {})

    if not sales_metrics.get("available"):
        return {
            "status": "unknown",
            "reason": "Sales information not available."
        }

    evidence = build_average_evidence(sales_metrics)

    negative_average_metrics = [
        item["metric"]
        for item in evidence
        if item["average"] < 0
    ]

    if negative_average_metrics:
        return {
            "status": "attention",
            "reason": "At least one sales metric has a negative average.",
            "evidence": evidence
        }

    if evidence:
        return {
            "status": "healthy",
            "reason": "Available sales metrics do not show negative averages.",
            "evidence": evidence
        }

    return {
        "status": "unknown",
        "reason": "Sales information is available, but there is insufficient evidence to assess health."
    }


def assess_profitability_health(profile):
    profitability_metrics = profile.get("business_metrics", {}).get("profitability", {})

    if not profitability_metrics.get("available"):
        return {
            "status": "unknown",
            "reason": "Profitability information not available."
        }

    evidence = build_average_evidence(profitability_metrics)

    negative_average_metrics = [
        item["metric"]
        for item in evidence
        if item["average"] < 0
    ]

    if negative_average_metrics:
        return {
            "status": "attention",
            "reason": "At least one profitability metric has a negative average.",
            "evidence": evidence
        }

    if evidence:
        return {
            "status": "healthy",
            "reason": "Available profitability metrics do not show negative averages.",
            "evidence": evidence
        }

    return {
        "status": "unknown",
        "reason": "Profitability information is available, but there is insufficient evidence to assess health."
    }


def assess_customer_health(profile):
    customer_metrics = profile.get("business_metrics", {}).get("customers", {})

    if not customer_metrics.get("available"):
        return {
            "status": "unknown",
            "reason": "Customer information not available."
        }

    return {
        "status": "healthy",
        "reason": "Customer information is available.",
        "evidence": [
            {
                "dimension": column,
                "unique_count": customer_metrics.get("unique_counts", {}).get(column)
            }
            for column in customer_metrics.get("columns", [])
        ]
    }


def assess_data_quality_health(profile):
    data_quality_metrics = profile.get("business_metrics", {}).get("data_quality", {})
    evidence = [
        {
            "metric": "null_percentage",
            "value": data_quality_metrics.get("null_percentage", 0)
        },
        {
            "metric": "duplicate_count",
            "value": data_quality_metrics.get("duplicate_count", 0)
        }
    ]

    if data_quality_metrics.get("duplicate_count", 0) > 0:
        return {
            "status": "attention",
            "reason": "The dataset contains duplicate rows.",
            "evidence": evidence
        }

    if data_quality_metrics.get("null_percentage", 0) >= 5:
        return {
            "status": "attention",
            "reason": "The dataset contains many missing values.",
            "evidence": evidence
        }

    return {
        "status": "healthy",
        "reason": "No major data quality issues were detected.",
        "evidence": evidence
    }


def build_business_health(profile):
    return {
        "sales": assess_sales_health(profile),
        "profitability": assess_profitability_health(profile),
        "customers": assess_customer_health(profile),
        "data_quality": assess_data_quality_health(profile)
    }


BUSINESS_VALUE_PRIORITY = {
    "high": 3,
    "medium": 2,
    "low": 1
}

COMPLEXITY_PRIORITY = {
    "basic": 3,
    "intermediate": 2,
    "advanced": 1
}


def get_analysis_concepts(analysis):
    matched_concepts = analysis.get("matched_concepts", {})

    return (
        list(matched_concepts.get("metrics", {}).keys())
        + list(matched_concepts.get("dimensions", {}).keys())
    )


def get_diagnosis_context_score(analysis, business_diagnosis):
    concepts = get_analysis_concepts(analysis)
    dataset_type = business_diagnosis.get("dataset_type", "")
    business_areas = business_diagnosis.get("business_areas", [])
    score = 0

    if "sales" in concepts and (
        "sales" in dataset_type
        or "Sales" in business_areas
    ):
        score += 1

    if "profitability" in concepts and "Finance" in business_areas:
        score += 1

    if "geography" in concepts and "Geography" in business_areas:
        score += 1

    if (
        ("product" in concepts or "product_category" in concepts)
        and "Products" in business_areas
    ):
        score += 1

    if (
        ("customer" in concepts or "customer_segment" in concepts)
        and "Customers" in business_areas
    ):
        score += 1

    return score


def get_health_context_score(analysis, business_health):
    concepts = get_analysis_concepts(analysis)
    score = 0

    if (
        "sales" in concepts
        and business_health.get("sales", {}).get("status") == "attention"
    ):
        score += 1

    if (
        "profitability" in concepts
        and business_health.get("profitability", {}).get("status") == "attention"
    ):
        score += 1

    if (
        ("customer" in concepts or "customer_segment" in concepts)
        and business_health.get("customers", {}).get("status") == "attention"
    ):
        score += 1

    return score


def get_priority_score(analysis, business_health, business_diagnosis):
    business_value_score = BUSINESS_VALUE_PRIORITY.get(
        analysis.get("business_value"),
        0
    )
    complexity_score = COMPLEXITY_PRIORITY.get(
        analysis.get("complexity"),
        0
    )

    return (
        business_value_score * 100
        + complexity_score * 10
        + get_diagnosis_context_score(analysis, business_diagnosis)
        + get_health_context_score(analysis, business_health)
    )


def build_priority_reason(analysis, business_health, business_diagnosis):
    reason_parts = [
        f"{analysis.get('business_value', 'unknown')} business value",
        f"{analysis.get('complexity', 'unknown')} complexity"
    ]

    if get_diagnosis_context_score(analysis, business_diagnosis) > 0:
        reason_parts.append("matches the dataset business context")

    if get_health_context_score(analysis, business_health) > 0:
        reason_parts.append("matches an area flagged in business health")

    return "; ".join(reason_parts) + "."


def build_executive_priorities(
    available_analyses,
    business_health,
    business_diagnosis
):
    ranked_analyses = []

    for original_position, analysis in enumerate(available_analyses):
        if not analysis.get("available"):
            continue

        ranked_analyses.append({
            "analysis": analysis,
            "score": get_priority_score(
                analysis,
                business_health,
                business_diagnosis
            ),
            "original_position": original_position
        })

    ranked_analyses.sort(
        key=lambda item: (
            -item["score"],
            item["original_position"]
        )
    )

    return [
        {
            "priority": index + 1,
            "analysis_id": item["analysis"].get("id"),
            "title": item["analysis"].get("title"),
            "business_value": item["analysis"].get("business_value"),
            "reason": build_priority_reason(
                item["analysis"],
                business_health,
                business_diagnosis
            )
        }
        for index, item in enumerate(ranked_analyses)
    ]
