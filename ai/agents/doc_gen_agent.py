"""DocGenAgent — generates a test case document from the knowledge base."""
from __future__ import annotations

from pathlib import Path

from ai.agents.base_agent import BaseAgent, AgentContext

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class DocGenAgent(BaseAgent):
    """
    Wraps ai.skills.test_case_doc_kb.TestCaseDocumentationSkill.

    Domain controls which generation method and prompt template are used:
      api    → generate_api_test_document()
      web    → generate_document()
      mobile → generate_document() with mobile hints via ctx.extra
      other  → generate_document() with domain label

    Extra params (passed via ctx.extend()):
      endpoint  — API endpoint path (api domain only, default /<feature_name>)
      method    — HTTP method (api domain only, default "ALL")
    """
    name = "doc_gen"

    def run(
        self,
        *,
        feature_name: str,
        output_path: Path | None = None,
    ) -> dict:
        from ai.skills.test_case_doc_kb import TestCaseDocumentationSkill

        skill = TestCaseDocumentationSkill(self.client, self.kb)
        domain = self.ctx.domain

        if domain == "api":
            content = skill.generate_api_test_document(
                endpoint=self.ctx.get("endpoint", f"/{feature_name}"),
                method=self.ctx.get("method", "ALL"),
                description=f"All {feature_name} API operations",
                api_type="rest",
                feature_name=feature_name,
            )
        else:
            content = skill.generate_document(
                page_url=f"/{feature_name}",
                form_description=f"{feature_name} {domain} feature",
                feature_name=feature_name,
            )

        out = output_path or self._default_output(feature_name)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        self._log.info("Doc written: %s", out)
        return {"doc_path": out, "domain": domain, "feature": feature_name, "content": content}

    def _default_output(self, feature_name: str) -> Path:
        base = self.ctx.output_base or _ROOT_DIR
        return base / "docs" / "test_cases" / self.ctx.domain / f"{feature_name}.md"
