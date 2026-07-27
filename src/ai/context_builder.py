def format_section(title, lines):
    clean_lines = [
        str(line).strip()
        for line in lines
        if str(line).strip()
    ]

    if not clean_lines:
        return f"{title}: Unavailable."

    return title + ":\n" + "\n".join(f"- {line}" for line in clean_lines)


def build_summary_lines(summary):
    lines = []

    if summary.get("dataset_type"):
        lines.append(f"Dataset type: {summary.get('dataset_type')}")

    if summary.get("analysis_readiness"):
        lines.append(f"Analysis readiness: {summary.get('analysis_readiness')}")

    if summary.get("business_areas"):
        lines.append("Business areas: " + ", ".join(summary.get("business_areas", [])))

    for warning in summary.get("warnings", []):
        message = warning.get("message")

        if message:
            lines.append(f"Warning: {message}")

    return lines


def build_health_lines(health):
    return [
        (
            f"{item.get('label', area)}: {item.get('status', 'unknown')} - "
            f"{item.get('reason', 'No reason provided.')}"
        )
        for area, item in health.items()
    ]


def build_insight_lines(insights):
    lines = []

    for index, insight in enumerate(insights, start=1):
        title = insight.get("title", f"Insight {index}")
        finding = insight.get("finding", "No finding provided.")
        impact = insight.get("impact_category", "Business Impact")
        supporting_metrics = insight.get("supporting_metrics", {})
        metric_text = "; ".join(
            f"{label}: {value}"
            for label, value in supporting_metrics.items()
        )
        line = f"{index}. {title} ({impact}): {finding}"

        if metric_text:
            line += f" Supporting metrics: {metric_text}."

        lines.append(line)

    return lines


def build_recommendation_lines(recommendations):
    return [
        (
            f"{index}. {recommendation.get('title', 'Recommendation')}: "
            f"{recommendation.get('recommendation')}"
        )
        for index, recommendation in enumerate(recommendations, start=1)
        if recommendation.get("recommendation")
    ]


def build_priority_lines(priorities):
    return [
        (
            f"{priority.get('priority', index)}. {priority.get('title')}: "
            f"{priority.get('reason')}"
        )
        for index, priority in enumerate(priorities, start=1)
        if priority.get("title")
    ]


def build_metric_lines(key_metrics):
    lines = []

    for area, metrics in key_metrics.items():
        if metrics.get("metrics_by_column"):
            for column, values in metrics.get("metrics_by_column", {}).items():
                parts = []

                for key in ["total", "average", "count"]:
                    if key in values:
                        parts.append(f"{key}: {values.get(key)}")

                if parts:
                    lines.append(f"{area} - {column}: " + ", ".join(parts))

        elif metrics.get("unique_counts"):
            for column, unique_count in metrics.get("unique_counts", {}).items():
                lines.append(f"{area} - {column}: unique count {unique_count}")

        elif area == "data_quality":
            lines.append(
                "data_quality: "
                f"null count {metrics.get('null_count', 0)}, "
                f"null percentage {metrics.get('null_percentage', 0)}, "
                f"duplicate count {metrics.get('duplicate_count', 0)}"
            )

    return lines


def build_ai_context(business_knowledge):
    business_knowledge = business_knowledge or {}

    sections = [
        format_section(
            "Executive Summary",
            build_summary_lines(business_knowledge.get("summary", {}))
        ),
        format_section(
            "Business Health",
            build_health_lines(business_knowledge.get("health", {}))
        ),
        format_section(
            "Business Insights",
            build_insight_lines(business_knowledge.get("insights", []))
        ),
        format_section(
            "Recommendations",
            build_recommendation_lines(business_knowledge.get("recommendations", []))
        ),
        format_section(
            "Executive Priorities",
            build_priority_lines(business_knowledge.get("priorities", []))
        ),
        format_section(
            "Key Metrics",
            build_metric_lines(business_knowledge.get("key_metrics", {}))
        )
    ]

    return "\n\n".join(sections)
