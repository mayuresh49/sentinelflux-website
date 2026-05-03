"""Test Case Documentation Skill using Knowledge Base Context"""

from pathlib import Path
from ai.clients.mistral_client import MistralClient
from ai.prompts.prompt_templates import (
    TEST_CASE_DOC_PROMPT,
    API_TEST_CASE_DOC_PROMPT,
)
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader


class TestCaseDocumentationSkill:
    """Generate test case documentation using AI with knowledge base context."""
    
    def __init__(self, ai_client: MistralClient, kb_loader: KnowledgeBaseLoader = None):
        self.ai_client = ai_client
        self.kb_loader = kb_loader or KnowledgeBaseLoader()
    
    def generate_document(self, page_url: str, form_description: str) -> str:
        """Generate UI test case documentation with knowledge base context."""
        
        # Get knowledge base context
        ui_context = self.kb_loader.get_ui_context()
        
        # Format prompt with KB context
        prompt = TEST_CASE_DOC_PROMPT.format(
            page_url=page_url,
            form_description=form_description,
            kb_context=ui_context,
        )
        
        return self.ai_client.generate(
            prompt,
            max_tokens=2000,
            temperature=0.2
        ).strip()
    
    def generate_api_test_document(
        self,
        endpoint: str,
        method: str,
        description: str,
        api_type: str = "rest"
    ) -> str:
        """Generate API test case documentation with knowledge base context."""
        
        # Get knowledge base context
        if api_type == "rest":
            api_context = self.kb_loader.get_rest_api_context()
        else:
            api_context = self.kb_loader.get_graphql_api_context()
        
        # Format prompt with KB context
        prompt = API_TEST_CASE_DOC_PROMPT.format(
            endpoint=endpoint,
            method=method,
            description=description,
            api_context=api_context,
            kb_context=self.kb_loader.get_feature_context(),
        )
        
        return self.ai_client.generate(
            prompt,
            max_tokens=2500,
            temperature=0.2
        ).strip()
    
    def generate_feature_test_documentation(self, feature_name: str) -> str:
        """Generate documentation for a specific feature."""
        
        feature_context = self.kb_loader.get_feature_context(feature_name)
        
        prompt = f"""
Based on the following feature information, generate a comprehensive test case document:

{feature_context}

Include:
- Positive test cases
- Negative test cases
- Edge cases
- Integration scenarios
- Expected error handling

Generate detailed pytest test code and documentation.
"""
        
        return self.ai_client.generate(
            prompt,
            max_tokens=3000,
            temperature=0.2
        ).strip()
