from ai.clients.base_client import AIClient
from ai.prompts.prompt_templates import TEST_CASE_DOC_PROMPT


class TestCaseDocumentationSkill:
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    def generate_document(self, page_url: str, form_description: str) -> str:
        prompt = TEST_CASE_DOC_PROMPT.format(
            page_url=page_url,
            form_description=form_description,
        )
        return self.ai_client.generate(prompt, max_tokens=800, temperature=0.2).strip()
