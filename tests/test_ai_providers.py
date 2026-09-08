import os
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.ai.provider_registry import create_provider
from src.ai.providers.anthropic_provider import AnthropicProvider
from src.ai.providers.base_provider import AIProvider
from src.ai.providers.gemini_provider import GeminiProvider
from src.ai.providers.mock_provider import MockProvider
from src.ai.providers.openai_provider import OpenAIProvider
from src.qa import answer_question


class TestProviderArchitecture(unittest.TestCase):
    def test_all_providers_implement_base_provider(self):
        for provider_class in [
            MockProvider,
            OpenAIProvider,
            AnthropicProvider,
            GeminiProvider
        ]:
            self.assertTrue(issubclass(provider_class, AIProvider))

    def test_mock_provider_remains_deterministic(self):
        messages = [
            {"role": "user", "content": "Business Knowledge Context:\nExecutive Summary:\n- Dataset type: transactional_sales_dataset"},
            {"role": "user", "content": "What is the business summary?"}
        ]

        first_answer = MockProvider().generate_response(messages)
        second_answer = MockProvider().generate_response(messages)

        self.assertEqual(first_answer, second_answer)
        self.assertTrue(first_answer.startswith("Answer"))

    def test_providers_are_safe_without_api_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIn("OPENAI_API_KEY", OpenAIProvider().generate_response([]))
            self.assertIn("ANTHROPIC_API_KEY", AnthropicProvider().generate_response([]))
            self.assertIn("GEMINI_API_KEY", GeminiProvider().generate_response([]))

    def test_anthropic_valid_response_and_error_are_handled(self):
        response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Anthropic answer")]
        )
        working_sdk = types.SimpleNamespace(
            Anthropic=lambda api_key: SimpleNamespace(
                messages=SimpleNamespace(
                    create=lambda **kwargs: response
                )
            )
        )

        with patch.dict(sys.modules, {"anthropic": working_sdk}):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
                answer = AnthropicProvider().generate_response([])

        self.assertEqual(answer, "Anthropic answer")

        failing_sdk = types.SimpleNamespace(
            Anthropic=lambda api_key: SimpleNamespace(
                messages=SimpleNamespace(
                    create=lambda **kwargs: 1 / 0
                )
            )
        )

        with patch.dict(sys.modules, {"anthropic": failing_sdk}):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
                answer = AnthropicProvider().generate_response([])

        self.assertIn("could not complete", answer)

    def test_gemini_valid_response_and_error_are_handled(self):
        response = SimpleNamespace(text="Gemini answer")
        working_genai = SimpleNamespace(
            Client=lambda api_key: SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=lambda **kwargs: response
                )
            )
        )
        google_module = types.ModuleType("google")
        google_module.genai = working_genai

        with patch.dict(sys.modules, {"google": google_module}):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}):
                answer = GeminiProvider().generate_response([])

        self.assertEqual(answer, "Gemini answer")

        failing_genai = SimpleNamespace(
            Client=lambda api_key: SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=lambda **kwargs: 1 / 0
                )
            )
        )
        failing_google_module = types.ModuleType("google")
        failing_google_module.genai = failing_genai

        with patch.dict(sys.modules, {"google": failing_google_module}):
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}):
                answer = GeminiProvider().generate_response([])

        self.assertIn("could not complete", answer)

    def test_openai_valid_response_and_error_are_handled(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="OpenAI answer"))]
        )
        working_sdk = types.SimpleNamespace(
            OpenAI=lambda api_key: SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(
                        create=lambda **kwargs: response
                    )
                )
            )
        )

        with patch.dict(sys.modules, {"openai": working_sdk}):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
                answer = OpenAIProvider().generate_response([])

        self.assertEqual(answer, "OpenAI answer")

        failing_sdk = types.SimpleNamespace(
            OpenAI=lambda api_key: SimpleNamespace(
                chat=SimpleNamespace(
                    completions=SimpleNamespace(
                        create=lambda **kwargs: 1 / 0
                    )
                )
            )
        )

        with patch.dict(sys.modules, {"openai": failing_sdk}):
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
                answer = OpenAIProvider().generate_response([])

        self.assertIn("could not complete", answer)

    def test_provider_selector_chooses_each_provider(self):
        expected = {
            "mock": MockProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider
        }

        for provider_name, provider_class in expected.items():
            self.assertIsInstance(create_provider(provider_name), provider_class)

        self.assertIsInstance(create_provider("unknown"), MockProvider)

    def test_qa_continues_to_work_with_explicit_mock_provider(self):
        profile = {
            "business_knowledge": {
                "summary": {
                    "dataset_type": "transactional_sales_dataset"
                },
                "health": {},
                "insights": [],
                "advanced_retail_insights": [],
                "recommendations": [],
                "priorities": [],
                "executive_action_plan": [],
                "key_metrics": {}
            }
        }

        answer = answer_question(
            "What is the business summary?",
            profile,
            provider=MockProvider()
        )

        self.assertTrue(answer.startswith("Answer"))

    def test_no_api_secrets_are_hardcoded(self):
        project_root = Path(__file__).resolve().parents[1]
        source_files = list(project_root.glob("*.py")) + list(
            (project_root / "src").rglob("*.py")
        )
        source_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in source_files
        )

        self.assertNotIn("sk-", source_text)
        self.assertNotIn("AIza", source_text)


if __name__ == "__main__":
    unittest.main()
