from typing import Optional

from ai.clients.base_client import AIClient


def create_ai_client(ai_config: dict) -> Optional[AIClient]:
    if not ai_config.get("enabled", False):
        return None
    mode = ai_config.get("mode", "mistral")
    if mode == "mistral":
        from ai.clients.mistral_client import MistralClient
        local = ai_config.get("local", False)
        if local:
            return MistralClient(
                api_key=None,
                model=ai_config.get("model", "mistral"),
                local=True,
                local_url=ai_config.get("local_url", "http://localhost:11434"),
            )
        return MistralClient(
            api_key=ai_config.get("api_key"),
            model=ai_config.get("model", "mistral-medium"),
            local=False,
        )
    if mode == "openai":
        import os

        from ai.clients.openai_client import OpenAIClient
        return OpenAIClient(
            api_key=os.environ.get("OPENAI_API_KEY", ai_config.get("api_key", "")),
            model=ai_config.get("model", "gpt-4o-mini"),
        )
    if mode == "anthropic":
        import os

        from ai.clients.anthropic_client import AnthropicClient
        return AnthropicClient(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ai_config.get("api_key", "")),
            model=ai_config.get("model", "claude-haiku-4-5-20251001"),
        )
    return None
