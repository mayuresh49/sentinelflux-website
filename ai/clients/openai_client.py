from __future__ import annotations

from ai.clients.base_client import AIClient


class OpenAIClient(AIClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key=api_key, model=model)
        import openai
        self._client = openai.OpenAI(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def chat(self, messages: list, **kwargs) -> str:
        resp = self._client.chat.completions.create(model=self.model, messages=messages)
        return resp.choices[0].message.content or ""
