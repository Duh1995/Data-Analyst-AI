SUPPORTED_DATASET_TYPES = {
    "transactional_sales_dataset",
    "financial_or_sales_dataset",
    "customer_dataset",
    "product_dataset",
    "general_business_dataset"
}

MAX_ACTIONS = 5

IMPACT_SCORE = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}

EFFORT_SCORE = {
    "Easy": 3,
    "Medium": 2,
    "Hard": 1
}


def is_supported_business_knowledge(business_knowledge):
    dataset_type = (
        business_knowledge
        .get("summary", {})
        .get("dataset_type")
    )

    return dataset_type in SUPPORTED_DATASET_TYPES


def normalize_text(value):
    return str(value or "").lower()


def find_first(items, keywords):
    for item in items:
        searchable_text = normalize_text(item)

        if isinstance(item, dict):
            searchable_text = normalize_text(
                " ".join(
                    str(value)
                    for value in item.values()
                )
            )

        if all(keyword in searchable_text for keyword in keywords):
            return item

    return None


def find_priority(priorities, keywords):
    priority = find_first(priorities, keywords)

    if not priority:
        return None

    return {
        "priority": priority.get("priority"),
        "title": priority.get("title"),
        "analysis_id": priority.get("analysis_id"),
        "reason": priority.get("reason")
    }


def get_advanced_analysis(advanced_retail_insights, analysis_id):
    for analysis in advanced_retail_insights:
        if analysis.get("analysis_id") == analysis_id:
            return analysis

    return None


def get_insight(insights, title_keywords):
    for insight in insights:
        title = normalize_text(insight.get("title"))

        if all(keyword in title for keyword in title_keywords):
            return insight

    return None


def get_metric_value(metrics, key):
    value = metrics.get(key)

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return value


def make_action(
    title,
    business_problem,
    recommended_action,
    expected_business_impact,
    implementation_effort,
    reasoning,
    related_business_insight=None,
    related_priority=None,
    supporting_metrics=None
):
    return {
        "title": title,
        "business_problem": business_problem,
        "recommended_action": recommended_action,
        "expected_business_impact": expected_business_impact,
        "implementation_effort": implementation_effort,
        "implementation_priority": None,
        "reasoning": reasoning,
        "related_business_insight": related_business_insight,
        "related_priority": related_priority,
        "supporting_metrics": supporting_metrics or {}
    }


def action_sort_key(action):
    related_priority = action.get("related_priority") or {}
    priority_value = related_priority.get("priority") or 99

    return (
        -IMPACT_SCORE.get(action.get("expected_business_impact"), 0),
        priority_value,
        -EFFORT_SCORE.get(action.get("implementation_effort"), 0),
        action.get("title", "")
    )


def rank_actions(actions):
    ranked_actions = sorted(actions, key=action_sort_key)[:MAX_ACTIONS]

    for index, action in enumerate(ranked_actions, start=1):
        action["implementation_priority"] = index

    return ranked_actions


def build_discount_action(business_knowledge):
    advanced = business_knowledge.get("advanced_retail_insights", [])
    insights = business_knowledge.get("insights", [])
    priorities = business_knowledge.get("priorities", [])
    discount_analysis = get_advanced_analysis(advanced, "discount_effectiveness")
    discount_insight = get_insight(insights, ["business", "risk"])

    if not discount_analysis:
        return None

    metrics = discount_analysis.get("metrics", {})

    if metrics.get("effectiveness") != "negative":
        return None

    return make_action(
        "Reduce excessive discounting",
        "High-discount records show weaker average profit than low-discount records.",
        "Review discount policies and approval rules before expanding discount activity.",
        "High",
        "Medium",
        "Discount effectiveness is negative in Advanced Retail Intelligence.",
        related_business_insight=discount_insight,
        related_priority=find_priority(priorities, ["discount", "profitability"]),
        supporting_metrics={
            "median_discount": metrics.get("median_discount"),
            "low_discount_average_profit": metrics.get("low_discount_average_profit"),
            "high_discount_average_profit": metrics.get("high_discount_average_profit"),
            "profit_difference": metrics.get("profit_difference"),
            "effectiveness": metrics.get("effectiveness")
        }
    )


def build_product_inventory_action(business_knowledge):
    insights = business_knowledge.get("insights", [])
    priorities = business_knowledge.get("priorities", [])
    product_insight = get_insight(insights, ["product", "opportunity"])

    if not product_insight:
        return None

    supporting_metrics = product_insight.get("supporting_metrics", {})
    product_name = next(iter(supporting_metrics), "the strongest product category")

    return make_action(
        f"Prioritize {product_name} inventory",
        "One product category is identified as the strongest sales contributor.",
        "Prioritize inventory, merchandising and campaign focus around the strongest category.",
        "High",
        "Medium",
        "The action is supported by a Product Opportunity business insight.",
        related_business_insight=product_insight,
        related_priority=find_priority(priorities, ["product", "category"]),
        supporting_metrics=supporting_metrics
    )


def build_profitability_action(business_knowledge):
    insights = business_knowledge.get("insights", [])
    priorities = business_knowledge.get("priorities", [])
    profitability_insight = get_insight(insights, ["profitability", "risk"])

    if not profitability_insight:
        return None

    supporting_metrics = profitability_insight.get("supporting_metrics", {})
    product_name = next(iter(supporting_metrics), "the underperforming category")

    return make_action(
        f"Improve {product_name} profitability",
        "A product category is identified as underperforming on profitability.",
        "Review pricing strategy, discounting and operating costs for the underperforming category.",
        "High",
        "Hard",
        "The action is supported by a Profitability Risk business insight.",
        related_business_insight=profitability_insight,
        related_priority=find_priority(priorities, ["profitability", "product"]),
        supporting_metrics=supporting_metrics
    )


def build_region_action(business_knowledge):
    insights = business_knowledge.get("insights", [])
    priorities = business_knowledge.get("priorities", [])
    revenue_insight = (
        get_insight(insights, ["revenue", "concentration"])
        or get_insight(insights, ["strongest", "market"])
    )

    if not revenue_insight:
        return None

    supporting_metrics = revenue_insight.get("supporting_metrics", {})
    region_name = next(iter(supporting_metrics), "the leading region")

    return make_action(
        f"Increase investment in {region_name}",
        "One market is identified as the primary revenue driver.",
        "Protect the leading market while using it as a reference for commercial execution.",
        "Medium",
        "Medium",
        "The action is supported by revenue concentration evidence in Business Insights.",
        related_business_insight=revenue_insight,
        related_priority=find_priority(priorities, ["geography"]),
        supporting_metrics=supporting_metrics
    )


def build_customer_segment_action(business_knowledge):
    insights = business_knowledge.get("insights", [])
    priorities = business_knowledge.get("priorities", [])
    customer_insight = get_insight(insights, ["customer", "opportunity"])

    if not customer_insight:
        return None

    return make_action(
        "Review underperforming customer segments",
        "Customer segments show materially different sales contribution.",
        "Review the offer and acquisition strategy for weaker customer segments.",
        "Medium",
        "Medium",
        "The action is supported by a Customer Opportunity business insight.",
        related_business_insight=customer_insight,
        related_priority=find_priority(priorities, ["customer", "segment"]),
        supporting_metrics=customer_insight.get("supporting_metrics", {})
    )


def build_product_dependency_action(business_knowledge):
    advanced = business_knowledge.get("advanced_retail_insights", [])
    priorities = business_knowledge.get("priorities", [])
    product_dependency = get_advanced_analysis(advanced, "product_dependency")

    if not product_dependency:
        return None

    metrics = product_dependency.get("metrics", {})

    if metrics.get("dependency_level") != "high":
        return None

    dependency_name = metrics.get("dependency_name", "one product category")

    return make_action(
        "Reduce dependency on a single product",
        f"{dependency_name} is the largest product dependency.",
        "Reduce reliance on the dominant product category by strengthening secondary categories.",
        "Medium",
        "Hard",
        "Advanced Retail Intelligence identifies high product dependency.",
        related_business_insight=product_dependency,
        related_priority=find_priority(priorities, ["product", "category"]),
        supporting_metrics={
            "dependency_name": metrics.get("dependency_name"),
            "dependency_share": metrics.get("dependency_share"),
            "dependency_level": metrics.get("dependency_level")
        }
    )


def build_customer_dependency_action(business_knowledge):
    advanced = business_knowledge.get("advanced_retail_insights", [])
    priorities = business_knowledge.get("priorities", [])
    customer_dependency = get_advanced_analysis(advanced, "customer_dependency")

    if not customer_dependency:
        return None

    metrics = customer_dependency.get("metrics", {})

    if metrics.get("dependency_level") != "high":
        return None

    dependency_name = metrics.get("dependency_name", "one customer segment")

    return make_action(
        "Diversify customer concentration",
        f"{dependency_name} is the largest customer segment dependency.",
        "Reduce reliance on the dominant customer segment by strengthening secondary segments.",
        "Medium",
        "Hard",
        "Advanced Retail Intelligence identifies high customer dependency.",
        related_business_insight=customer_dependency,
        related_priority=find_priority(priorities, ["customer", "segment"]),
        supporting_metrics={
            "dependency_name": metrics.get("dependency_name"),
            "dependency_share": metrics.get("dependency_share"),
            "dependency_level": metrics.get("dependency_level")
        }
    )


def build_executive_action_plan(business_knowledge):
    if not is_supported_business_knowledge(business_knowledge):
        return []

    candidate_builders = [
        build_discount_action,
        build_profitability_action,
        build_product_dependency_action,
        build_product_inventory_action,
        build_region_action,
        build_customer_dependency_action,
        build_customer_segment_action
    ]
    actions = []

    for builder in candidate_builders:
        action = builder(business_knowledge)

        if action:
            actions.append(action)

    return rank_actions(actions)
