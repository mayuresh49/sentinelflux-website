import requests
from ai.clients.base_client import AIClient


class MistralClient(AIClient):
    def __init__(self, api_key: str, model: str = "mistral-medium"):
        super().__init__(api_key, model)
        self.base_url = "https://api.mistral.ai/v1"

    def generate(self, prompt: str, **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 100),
            "temperature": kwargs.get("temperature", 0.7)
        }
        response = requests.post(f"{self.base_url}/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]

    def chat(self, messages: list, **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 100),
            "temperature": kwargs.get("temperature", 0.7)
        }
        response = requests.post(f"{self.base_url}/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]