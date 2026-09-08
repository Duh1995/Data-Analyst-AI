import os

from src.ai.providers.anthropic_provider import AnthropicProvider
from src.ai.providers.gemini_provider import GeminiProvider
from src.ai.providers.mock_provider import MockProvider
from src.ai.providers.openai_provider import OpenAIProvider
from src.product_plan import FREE_PLAN, get_current_plan


PROVIDER_ENV_VAR = "INSIGHTFLOW_AI_PROVIDER"
DEFAULT_PROVIDER = "mock"

PROVIDER_MODELS = {
    "openai": ("OPENAI_MODEL", "gpt-4o-mini"),
    "anthropic": ("ANTHROPIC_MODEL", "claude-opus-5"),
    "gemini": ("GEMINI_MODEL", "gemini-3.7-flash")
}

PROVIDER_CLASSES = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider
}


def get_configured_provider_name(provider_name=None):
    configured_name = provider_name or os.getenv(
        PROVIDER_ENV_VAR,
        DEFAULT_PROVIDER
    )
    normalized_name = str(configured_name).strip().lower()

    if normalized_name in PROVIDER_CLASSES:
        return normalized_name

    return DEFAULT_PROVIDER


def get_configured_model(provider_name):
    model_config = PROVIDER_MODELS.get(provider_name)

    if not model_config:
        return None

    environment_name, default_model = model_config
    return os.getenv(environment_name, default_model)


def create_provider(provider_name=None):
    if provider_name is None and get_current_plan() == FREE_PLAN:
        return MockProvider()

    selected_name = get_configured_provider_name(provider_name)
    provider_class = PROVIDER_CLASSES[selected_name]

    if selected_name == "mock":
        return provider_class()

    return provider_class(model=get_configured_model(selected_name))
