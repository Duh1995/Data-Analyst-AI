import os
import unittest
from unittest.mock import patch

from src.ai.provider_registry import create_provider
from src.ai.providers.mock_provider import MockProvider
from src.ai.providers.openai_provider import OpenAIProvider
from src.product_plan import (
    FREE_PLAN,
    PRO_PLAN,
    can_consume_usage,
    get_current_plan,
    get_plan_limits,
    has_plan_feature
)


class ProductPlanTests(unittest.TestCase):
    def test_plan_defaults_to_free(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_current_plan(), FREE_PLAN)

    def test_plan_normalizes_supported_values_and_falls_back_safely(self):
        with patch.dict(os.environ, {"INSIGHTFLOW_PLAN": " PRO "}):
            self.assertEqual(get_current_plan(), PRO_PLAN)

        with patch.dict(os.environ, {"INSIGHTFLOW_PLAN": "enterprise"}):
            self.assertEqual(get_current_plan(), FREE_PLAN)

    def test_plan_features_preserve_deterministic_bi_in_free(self):
        self.assertTrue(has_plan_feature("deterministic_bi", FREE_PLAN))
        self.assertTrue(has_plan_feature("mock_ai", FREE_PLAN))
        self.assertFalse(has_plan_feature("real_ai_providers", FREE_PLAN))
        self.assertTrue(has_plan_feature("real_ai_providers", PRO_PLAN))

    def test_free_limits_are_optional_and_configurable(self):
        with patch.dict(
            os.environ,
            {
                "INSIGHTFLOW_FREE_DATASET_LIMIT": "2",
                "INSIGHTFLOW_FREE_AI_QUESTION_LIMIT": "3"
            }
        ):
            self.assertEqual(
                get_plan_limits(FREE_PLAN),
                {"datasets_per_session": 2, "ai_questions_per_session": 3}
            )
            self.assertTrue(can_consume_usage("datasets_per_session", 1, FREE_PLAN))
            self.assertFalse(can_consume_usage("datasets_per_session", 2, FREE_PLAN))

    def test_invalid_limits_keep_unlimited_default(self):
        with patch.dict(
            os.environ,
            {"INSIGHTFLOW_FREE_AI_QUESTION_LIMIT": "invalid"}
        ):
            self.assertIsNone(
                get_plan_limits(FREE_PLAN)["ai_questions_per_session"]
            )

    def test_free_plan_forces_mock_provider_for_app_selection(self):
        with patch.dict(
            os.environ,
            {
                "INSIGHTFLOW_PLAN": FREE_PLAN,
                "INSIGHTFLOW_AI_PROVIDER": "openai"
            }
        ):
            self.assertIsInstance(create_provider(), MockProvider)

    def test_pro_plan_can_select_configured_real_provider(self):
        with patch.dict(
            os.environ,
            {
                "INSIGHTFLOW_PLAN": PRO_PLAN,
                "INSIGHTFLOW_AI_PROVIDER": "openai"
            }
        ):
            self.assertIsInstance(create_provider(), OpenAIProvider)


if __name__ == "__main__":
    unittest.main()
