"""ScriptGenAgent — generates a pytest script from a test case document."""
from __future__ import annotations

import ast
from pathlib import Path

from ai.agents.base_agent import BaseAgent
from utils.paths import ROOT as _ROOT_DIR


class ScriptGenAgent(BaseAgent):
    """
    Wraps ai.skills.test_script_gen.TestScriptGenSkill.

    Domain controls which markers, fixtures, and conventions are injected:
      api      → @pytest.mark.api, rest_client fixture
      web      → @pytest.mark.web, page fixture, BasePage imports
      mobile   → @pytest.mark.mobile, mobile_driver fixture
      security → @pytest.mark.security, rest_client fixture

    Extra params (passed via ctx.extend()):
      custom_fixtures — list[str] to override default fixtures for the domain
      tc_prefix       — TC ID prefix passed to script gen for function naming hints
    """
    name = "script_gen"

    def run(
        self,
        *,
        test_case_doc: str,
        feature_name: str,
        output_path: Path | None = None,
    ) -> dict:
        if not self.client:
            raise RuntimeError("ScriptGenAgent requires an AI client — configure one via the chat config")
        if not self.kb:
            raise RuntimeError("ScriptGenAgent requires a KB loader — pass kb= when constructing the agent")
        from ai.skills.test_script_gen import TestScriptGenSkill
        from dashboard.routers.config_router import (
            get_generation_categories_instruction,
            get_generation_type_instruction,
        )

        skill = TestScriptGenSkill(self.client, self.kb)
        tc_prefix = self.ctx.get("tc_prefix", "")
        product = self.ctx.product or None
        type_instruction = get_generation_type_instruction(product=product)
        categories_instruction = get_generation_categories_instruction(product=product)
        exploration_context = self.ctx.get("exploration_context", "")
        code = skill.generate_script(
            test_case_doc, self.ctx.domain, feature_name,
            tc_prefix=tc_prefix,
            test_type_instruction=type_instruction,
            categories_instruction=categories_instruction,
            output_base=self.ctx.output_base,
            exploration_context=exploration_context,
        )

        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise ValueError(
                f"ScriptGenAgent: generated code for '{feature_name}' has syntax error at line {exc.lineno}: {exc.msg}"
            ) from exc

        out = output_path or self._default_output(feature_name)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(code, encoding="utf-8")
        self._log.info("Script written: %s", out)
        return {"script_path": out, "domain": self.ctx.domain, "feature": feature_name}

    def _default_output(self, feature_name: str) -> Path:
        base = self.ctx.output_base or _ROOT_DIR
        return base / "tests" / self.ctx.domain / f"test_{feature_name}.py"
