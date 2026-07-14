from src.business_catalog import BUSINESS_CONCEPT_KEYWORDS
from src.domain_registry import get_supported_analysis_ids, is_supported_domain


def normalize_column_name(column_name):
    return str(column_name).lower().replace("_", " ").replace("-", " ")


def column_matches_keywords(column_name, keywords):
    normalized_name = normalize_column_name(column_name)

    return any(keyword in normalized_name for keyword in keywords)


def find_matching_columns(columns, concept_type, concept):
    keywords = (
        BUSINESS_CONCEPT_KEYWORDS
        .get(concept_type, {})
        .get(concept, [])
    )

    return [
        column
        for column in columns
        if column_matches_keywords(column, keywords)
    ]


def get_metric_columns(profile):
    columns = list(profile.get("meaningful_numeric_columns", []))

    for column in profile.get("numeric_columns", []):
        if column not in columns:
            columns.append(column)

    return columns


def get_dimension_columns(profile):
    columns = (
        list(profile.get("meaningful_categorical_columns", []))
        + list(profile.get("identifier_columns", []))
    )

    if profile.get("date_column"):
        columns.append(profile["date_column"])

    return columns


def build_available_concepts(profile):
    metric_columns = get_metric_columns(profile)
    dimension_columns = get_dimension_columns(profile)
    available_concepts = {
        "metrics": {},
        "dimensions": {}
    }

    for concept in BUSINESS_CONCEPT_KEYWORDS.get("metrics", {}):
        matches = find_matching_columns(
            metric_columns,
            "metrics",
            concept
        )

        if matches:
            available_concepts["metrics"][concept] = matches

    for concept in BUSINESS_CONCEPT_KEYWORDS.get("dimensions", {}):
        matches = find_matching_columns(
            dimension_columns,
            "dimensions",
            concept
        )

        if matches:
            available_concepts["dimensions"][concept] = matches

    return available_concepts


def resolve_required_concepts(required_concepts, available_concepts):
    matched_concepts = {
        "metrics": {},
        "dimensions": {}
    }
    missing_concepts = []

    for concept_type in ["metrics", "dimensions"]:
        for concept in required_concepts.get(concept_type, []):
            matches = (
                available_concepts
                .get(concept_type, {})
                .get(concept, [])
            )

            if matches:
                matched_concepts[concept_type][concept] = matches
            else:
                missing_concepts.append(concept)

    return matched_concepts, missing_concepts


def build_unavailable_reason(missing_concepts):
    if not missing_concepts:
        return "All required concepts are available."

    if len(missing_concepts) == 1:
        return f"Missing {missing_concepts[0]} concept."

    return "Missing concepts: " + ", ".join(missing_concepts) + "."


def resolve_analysis_availability(analysis_catalog, available_concepts):
    resolved_analyses = []

    for analysis in analysis_catalog:
        matched_concepts, missing_concepts = resolve_required_concepts(
            analysis.get("required_concepts", {}),
            available_concepts
        )

        resolved_analyses.append({
            "id": analysis.get("id"),
            "title": analysis.get("title"),
            "business_value": analysis.get("business_value"),
            "complexity": analysis.get("complexity"),
            "available": len(missing_concepts) == 0,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
            "reason": build_unavailable_reason(missing_concepts)
        })

    return resolved_analyses


def build_available_analyses(business_diagnosis, analysis_catalog, available_concepts):
    dataset_type = business_diagnosis.get("dataset_type")

    if not is_supported_domain(dataset_type):
        return []

    supported_analysis_ids = get_supported_analysis_ids(dataset_type)
    domain_analysis_catalog = [
        analysis
        for analysis in analysis_catalog
        if analysis.get("id") in supported_analysis_ids
    ]

    return resolve_analysis_availability(
        domain_analysis_catalog,
        available_concepts
    )


def build_analysis_resolution(profile, analysis_catalog):
    available_concepts = build_available_concepts(profile)

    return build_available_analyses(
        profile.get("business_diagnosis", {}),
        analysis_catalog,
        available_concepts
    )
