import os


FREE_PLAN = "free"
PRO_PLAN = "pro"
PLAN_ENV_VAR = "INSIGHTFLOW_PLAN"
DEFAULT_PLAN = FREE_PLAN

PLAN_FEATURES = {
    FREE_PLAN: {
        "deterministic_bi": True,
        "mock_ai": True,
        "real_ai_providers": False,
        "advanced_retail_intelligence_full": False
    },
    PRO_PLAN: {
        "deterministic_bi": True,
        "mock_ai": True,
        "real_ai_providers": True,
        "advanced_retail_intelligence_full": True
    }
}

DEFAULT_PLAN_LIMITS = {
    FREE_PLAN: {
        "datasets_per_session": None,
        "ai_questions_per_session": None
    },
    PRO_PLAN: {
        "datasets_per_session": None,
        "ai_questions_per_session": None
    }
}

LIMIT_ENV_VARS = {
    "datasets_per_session": "INSIGHTFLOW_FREE_DATASET_LIMIT",
    "ai_questions_per_session": "INSIGHTFLOW_FREE_AI_QUESTION_LIMIT"
}


def get_current_plan(plan_name=None):
    configured_plan = plan_name or os.getenv(PLAN_ENV_VAR, DEFAULT_PLAN)
    normalized_plan = str(configured_plan).strip().lower()

    if normalized_plan in PLAN_FEATURES:
        return normalized_plan

    return DEFAULT_PLAN


def get_plan_display_name(plan_name=None):
    return get_current_plan(plan_name).title()


def has_plan_feature(feature_name, plan_name=None):
    plan = get_current_plan(plan_name)
    return bool(PLAN_FEATURES[plan].get(feature_name, False))


def _read_optional_limit(environment_name, default_value):
    configured_value = os.getenv(environment_name)

    if configured_value is None or not configured_value.strip():
        return default_value

    try:
        parsed_value = int(configured_value)
    except ValueError:
        return default_value

    return parsed_value if parsed_value >= 0 else default_value


def get_plan_limits(plan_name=None):
    plan = get_current_plan(plan_name)
    limits = dict(DEFAULT_PLAN_LIMITS[plan])

    if plan == FREE_PLAN:
        for limit_name, environment_name in LIMIT_ENV_VARS.items():
            limits[limit_name] = _read_optional_limit(
                environment_name,
                limits[limit_name]
            )

    return limits


def can_consume_usage(usage_name, current_count, plan_name=None):
    limit = get_plan_limits(plan_name).get(usage_name)

    if limit is None:
        return True

    return current_count < limit
