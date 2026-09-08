import os

from src.ai.providers.base_provider import AIProvider


DEFAULT_MODEL = "gemini-3.7-flash"


class GeminiProvider(AIProvider):
    def __init__(self, model=None):
        self.model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.api_key = os.getenv("GEMINI_API_KEY")

    def generate_response(self, messages):
        if not self.api_key:
            return (
                "AI infrastructure is ready, but GEMINI_API_KEY is not "
                "configured. Configure the key to enable Gemini answers."
            )

        try:
            from google import genai
        except ImportError:
            return (
                "AI infrastructure is ready, but the Google GenAI SDK is not "
                "installed. Install google-genai to enable answers."
            )

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=self.build_prompt(messages)
            )
            content = str(getattr(response, "text", "") or "").strip()

            return content or "The Gemini provider returned an empty answer."
        except Exception:
            return (
                "The Gemini provider could not complete this request. "
                "Check the API key, model and network configuration, then try again."
            )

    def build_prompt(self, messages):
        prompt_parts = []

        for message in messages or []:
            role = message.get("role", "user").upper()
            content = str(message.get("content", "")).strip()

            if content:
                prompt_parts.append(f"[{role}]\n{content}")

        return "\n\n".join(prompt_parts)
