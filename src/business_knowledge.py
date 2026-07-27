from src.domain_registry import is_supported_domain


def is_business_knowledge_supported(profile):
    dataset_type = (
        profile
        .get("business_diagnosis", {})
        .get("dataset_type")
    )

    return is_supported_domain(dataset_type)


def build_summary(profile):
    business_diagnosis = profile.get("business_diagnosis", {})

    return {
        "dataset_type": business_diagnosis.get("dataset_type"),
        "analysis_readiness": business_diagnosis.get("analysis_readiness"),
        "business_areas": business_diagnosis.get("business_areas", []),
        "warnings": business_diagnosis.get("warnings", [])
    }


def build_recommendations(profile):
    if not is_business_knowledge_supported(profile):
        return []

    if "business_recommendations" in profile:
        return profile.get("business_recommendations", [])

    recommendations = []

    for insight in profile.get("business_insights", []):
        recommendation = insight.get("recommendation")

        if not recommendation:
            continue

        recommendations.append({
            "title": insight.get("title"),
            "impact_category": insight.get("impact_category"),
            "recommendation": recommendation
        })

    return recommendations


def build_business_knowledge(profile):
    if not is_business_knowledge_supported(profile):
        return {
            "summary": build_summary(profile),
            "health": {},
            "insights": [],
            "advanced_retail_insights": [],
            "executive_action_plan": [],
            "recommendations": [],
            "priorities": [],
            "key_metrics": {}
        }

    return {
        "summary": build_summary(profile),
        "health": profile.get("business_health", {}),
        "insights": profile.get("business_insights", []),
        "advanced_retail_insights": profile.get("advanced_retail_insights", []),
        "executive_action_plan": profile.get("executive_action_plan", []),
        "recommendations": build_recommendations(profile),
        "priorities": profile.get("executive_priorities", []),
        "key_metrics": profile.get("business_metrics", {})
    }
