import os

from src.ai.providers.base_provider import AIProvider


DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(AIProvider):
    def __init__(self, model=None, api_key=None):
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate_response(self, messages):
        if not self.api_key:
            return (
                "AI infrastructure is ready, but OPENAI_API_KEY is not configured. "
                "Configure the key to enable AI-generated answers."
            )

        try:
            from openai import OpenAI
        except ImportError:
            return (
                "AI infrastructure is ready, but the OpenAI SDK is not installed. "
                "Install the openai package to enable AI-generated answers."
            )

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2
            )

            content = response.choices[0].message.content

            if content:
                return content

            return (
                "The OpenAI provider returned an empty answer. "
                "Please try the question again."
            )
        except Exception:
            return (
                "The OpenAI provider could not complete this request. "
                "Check the API key, model and network configuration, then try again."
            )
