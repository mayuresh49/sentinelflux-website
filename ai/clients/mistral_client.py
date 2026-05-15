import requests

from ai.clients.base_client import AIClient
from utils.constants import MISTRAL_CLOUD_TIMEOUT_S, MISTRAL_LOCAL_TIMEOUT_S


class MistralClient(AIClient):
    def __init__(self, api_key: str = None, model: str = "mistral", local: bool = True, local_url: str = "http://localhost:11434"):
        """
        Initialize Mistral AI client.
        
        Args:
            api_key: API key for cloud Mistral API (required for cloud, optional for local)
            model: Model name (e.g., "mistral-medium" for cloud, "mistral" for local Ollama)
            local: Whether to use local Mistral via Ollama (default: False)
            local_url: URL for local Mistral instance (default: http://localhost:11434)
        """
        super().__init__(api_key or "local", model)
        self.local = local
        
        if local:
            self.base_url = f"{local_url}/api"
            self.api_key = "unused"  # Local Ollama doesn't need API key
        else:
            self.base_url = "https://api.mistral.ai/v1"
            if not api_key:
                raise ValueError("api_key is required for cloud Mistral API")
            self.api_key = api_key

    def generate(self, prompt: str, **kwargs) -> str:
        if self.local:
            return self._generate_local(prompt, **kwargs)
        else:
            return self._generate_cloud(prompt, **kwargs)

    def _generate_cloud(self, prompt: str, **kwargs) -> str:
        """Generate text using cloud Mistral API."""
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
        response = requests.post(f"{self.base_url}/completions", json=data, headers=headers, timeout=MISTRAL_CLOUD_TIMEOUT_S)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]

    def _generate_local(self, prompt: str, **kwargs) -> str:
        """Generate text using local Mistral via Ollama."""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
        }
        response = requests.post(f"{self.base_url}/generate", json=data, timeout=MISTRAL_LOCAL_TIMEOUT_S)
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def chat(self, messages: list, **kwargs) -> str:
        if self.local:
            return self._chat_local(messages, **kwargs)
        else:
            return self._chat_cloud(messages, **kwargs)

    def _chat_cloud(self, messages: list, **kwargs) -> str:
        """Chat using cloud Mistral API."""
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
        response = requests.post(f"{self.base_url}/chat/completions", json=data, headers=headers, timeout=MISTRAL_CLOUD_TIMEOUT_S)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _chat_local(self, messages: list, **kwargs) -> str:
        """Chat using local Mistral via Ollama."""
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7),
        }
        response = requests.post(f"{self.base_url}/chat", json=data, timeout=MISTRAL_LOCAL_TIMEOUT_S)
        response.raise_for_status()
        result = response.json()
        return result.get("message", {}).get("content", "").strip()