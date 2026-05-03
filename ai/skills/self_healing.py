from ai.clients.mistral_client import MistralClient
from ai.prompts.prompt_templates import LOCATOR_HEALING_PROMPT


class SelfHealingSkill:
    def __init__(self, ai_client: MistralClient):
        self.ai_client = ai_client

    def heal_locator(self, html: str, broken_locator: str, url: str) -> str:
        prompt = LOCATOR_HEALING_PROMPT.format(html=html, broken_locator=broken_locator, url=url)
        return self.ai_client.generate(prompt).strip()