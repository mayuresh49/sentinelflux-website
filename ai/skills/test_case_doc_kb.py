"""Test Case Documentation Skill — KB-aware, domain-specific context injection."""

import yaml
from pathlib import Path
from ai.clients.base_client import AIClient
from ai.prompts.prompt_templates import (
    TEST_CASE_DOC_PROMPT,
    API_TEST_CASE_DOC_PROMPT,
    FEATURE_DOC_PROMPT,
)
from ai.knowledge_base.kb_loader import KnowledgeBaseLoader


class TestCaseDocumentationSkill:
    def __init__(self, ai_client: AIClient, kb_loader: KnowledgeBaseLoader = None):
        self.ai_client = ai_client
        self.kb_loader = kb_loader or KnowledgeBaseLoader()

    # --- web ---

    def generate_document(self, page_url: str, form_description: str, feature_name: str = None) -> str:
        """Generate UI test case doc. If feature_name given, injects full page + business rule context."""
        if feature_name:
            kb_context = self._build_web_context(feature_name)
        else:
            kb_context = self.kb_loader.get_ui_context()

        prompt = TEST_CASE_DOC_PROMPT.format(
            page_url=page_url,
            form_description=form_description,
            kb_context=kb_context,
        )
        return self.ai_client.generate(prompt, max_tokens=3000, temperature=0.2).strip()

    def _build_web_context(self, feature_name: str) -> str:
        """Build rich context: matching page fields + business rules + personas + validation rules."""
        parts = []

        # Find matching page(s) from ui_pages KB
        try:
            ui = self.kb_loader.load_ui_pages()
            pages = ui.get("pages", [])
            tokens = [t for t in feature_name.lower().replace("_", " ").split() if len(t) > 2]
            matching = [
                p for p in pages
                if any(t in p["name"].lower() for t in tokens)
            ]
            if matching:
                parts.append("=== PAGE DETAILS ===")
                for page in matching:
                    parts.append(f"\nPage: {page['name']} ({page['url']})")
                    parts.append(f"Description: {page.get('description', '')}")
                    if page.get("fields"):
                        parts.append("Fields (these are the ONLY fields on this form — do not add others):")
                        for f in page["fields"]:
                            req = "required" if f.get("required") else "optional"
                            line = f"  - {f['label']} ({req})"
                            if f.get("max_length"):
                                line += f", max_length={f['max_length']}"
                            if f.get("validation"):
                                line += f", validation={f['validation']}"
                            parts.append(line)
                    if page.get("test_scenarios"):
                        parts.append("Defined test scenarios:")
                        for cat, scenarios in page["test_scenarios"].items():
                            for s in scenarios:
                                parts.append(f"  [{cat}] {s}")
        except Exception:
            parts.append(self.kb_loader.get_ui_context())

        # Business rules
        parts.append(self.kb_loader.get_business_rules_context())

        # Validation rules
        try:
            product = self.kb_loader.load_product_knowledge()
            vr = product.get("validation_rules", {})
            if vr:
                parts.append("\n=== FIELD VALIDATION RULES ===")
                for field, rules in vr.items():
                    parts.append(f"  {field}: {rules}")
        except Exception:
            pass

        # Known issues (test hints)
        try:
            product = self.kb_loader.load_product_knowledge()
            issues = product.get("known_issues", [])
            if issues:
                parts.append("\n=== KNOWN ISSUES (test hints) ===")
                for issue in issues:
                    parts.append(f"  [{issue.get('severity','?')}] {issue['description']}")
                    if issue.get("test_hint"):
                        parts.append(f"    Hint: {issue['test_hint']}")
        except Exception:
            pass

        # Credentials (inject actual values so model doesn't invent generic ones)
        try:
            app = self.kb_loader.load_application_metadata()
            creds = app.get("default_credentials", {})
            if creds:
                parts.append("\n=== ACTUAL TEST CREDENTIALS (use these exactly) ===")
                for role, c in creds.items():
                    parts.append(f"  {role}: username={c.get('username')}, password={c.get('password')}")
        except Exception:
            pass

        # Personas
        parts.append(self.kb_loader.get_personas_context())

        return "\n".join(parts)

    # --- api ---

    def generate_api_test_document(
        self,
        endpoint: str,
        method: str,
        description: str,
        api_type: str = "rest",
        feature_name: str = None,
    ) -> str:
        if api_type == "rest":
            api_context = self._build_api_context(feature_name)
        else:
            api_context = self.kb_loader.get_graphql_api_context()

        prompt = API_TEST_CASE_DOC_PROMPT.format(
            endpoint=endpoint,
            method=method,
            description=description,
            api_context=api_context,
            kb_context=self.kb_loader.get_feature_context(feature_name),
        )
        return self.ai_client.generate(prompt, max_tokens=3000, temperature=0.2).strip()

    def _build_api_context(self, feature_name: str = None) -> str:
        """Build rich API context including matching endpoints + business rules."""
        parts = [self.kb_loader.get_rest_api_context()]

        if feature_name:
            try:
                specs = self.kb_loader.load_api_specs()
                endpoints = specs.get("rest_api", {}).get("endpoints", [])
                matching = [
                    e for e in endpoints
                    if feature_name.lower().replace("_", " ") in e["name"].lower().replace("_", " ")
                    or feature_name.lower().split("_")[0] in e["path"].lower()
                ]
                if matching:
                    parts.append("\n=== MATCHING ENDPOINT DETAILS ===")
                    for e in matching:
                        parts.append(f"\n{e['method']} {e['path']}: {e['description']}")
                        if e.get("request_body"):
                            parts.append(f"  Request: {e['request_body']}")
                        if e.get("response_codes"):
                            parts.append(f"  Response codes: {e['response_codes']}")
                        if e.get("negative_cases"):
                            parts.append("  Negative cases:")
                            for nc in e["negative_cases"]:
                                parts.append(f"    - {nc}")
            except Exception:
                pass

        parts.append(self.kb_loader.get_business_rules_context())
        return "\n".join(parts)

    # --- feature (generic) ---

    def generate_feature_test_documentation(self, feature_name: str) -> str:
        feature_context = self.kb_loader.get_feature_context(feature_name)
        increments_context = self.kb_loader.get_increments_context()
        kb_context = self.kb_loader.get_all_context()

        prompt = FEATURE_DOC_PROMPT.format(
            feature_context=feature_context + "\n" + increments_context,
            kb_context=kb_context,
        )
        return self.ai_client.generate(prompt, max_tokens=3000, temperature=0.2).strip()
