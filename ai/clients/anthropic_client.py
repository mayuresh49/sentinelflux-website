from __future__ import annotations

import anthropic

from ai.clients.base_client import AIClient


class AnthropicClient(AIClient):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        super().__init__(api_key=api_key, model=model)
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list, **kwargs) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            messages=messages,
        )
        for block in resp.content:
            if hasattr(block, "text"):
                return block.text
        return ""
