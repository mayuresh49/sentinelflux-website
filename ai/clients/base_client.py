from abc import ABC, abstractmethod


class AIClient(ABC):
    def __init__(self, api_key: str, model: str = "mistral"):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        pass