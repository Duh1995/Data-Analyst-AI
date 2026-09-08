import os

from src.ai.providers.base_provider import AIProvider


DEFAULT_MODEL = "claude-opus-5"


class AnthropicProvider(AIProvider):
    def __init__(self, model=None):
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def generate_response(self, messages):
        if not self.api_key:
            return (
                "AI infrastructure is ready, but ANTHROPIC_API_KEY is not "
                "configured. Configure the key to enable Anthropic answers."
            )

        try:
            from anthropic import Anthropic
        except ImportError:
            return (
                "AI infrastructure is ready, but the Anthropic SDK is not "
                "installed. Install the anthropic package to enable answers."
            )

        try:
            client = Anthropic(api_key=self.api_key)
            system_prompt, api_messages = self.build_api_messages(messages)
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=api_messages
            )
            content = "\n".join(
                block.text
                for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip()

            return content or "The Anthropic provider returned an empty answer."
        except Exception:
            return (
                "The Anthropic provider could not complete this request. "
                "Check the API key, model and network configuration, then try again."
            )

    def build_api_messages(self, messages):
        system_parts = []
        api_messages = []

        for message in messages or []:
            role = message.get("role")
            content = str(message.get("content", "")).strip()

            if not content:
                continue

            if role == "system":
                system_parts.append(content)
                continue

            if role not in {"user", "assistant"}:
                continue

            if api_messages and api_messages[-1]["role"] == role:
                api_messages[-1]["content"] += "\n\n" + content
            else:
                api_messages.append({"role": role, "content": content})

        return "\n\n".join(system_parts), api_messages
