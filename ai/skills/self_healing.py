from ai.clients.mistral_client import MistralClient
from ai.prompts.prompt_templates import LOCATOR_HEALING_PROMPT


class SelfHealingSkill:
    def __init__(self, ai_client: MistralClient):
        self.ai_client = ai_client

    def heal_locator(self, html: str, broken_locator: str, url: str) -> str | None:
        """
        Returns a replacement CSS selector, or None if the element was not found in the HTML.
        Callers must not write the result to disk without first validating it against a live page.
        """
        prompt = LOCATOR_HEALING_PROMPT.format(html=html, broken_locator=broken_locator, url=url)
        result = self.ai_client.generate(prompt).strip()
        if not result or result.upper() == "NOT_FOUND":
            return None
        # Strip any accidental prose the model added despite the rules
        first_line = result.splitlines()[0].strip()
        return first_line if first_line else None