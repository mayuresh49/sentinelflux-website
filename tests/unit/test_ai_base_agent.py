"""Unit tests for ai.agents.base_agent — AgentContext and BaseAgent."""
from __future__ import annotations

import pytest

from ai.agents.base_agent import AgentContext, BaseAgent


# ── AgentContext ──────────────────────────────────────────────────────────────

class TestAgentContext:
    def test_default_values(self):
        ctx = AgentContext(domain="api")
        assert ctx.domain == "api"
        assert ctx.product is None
        assert ctx.env == "qa"
        assert ctx.locale == "en-US"
        assert ctx.output_base is None
        assert ctx.extra == {}

    def test_custom_values(self):
        from pathlib import Path
        ctx = AgentContext(
            domain="web",
            product="orangehrm",
            env="staging",
            locale="fr-FR",
            output_base=Path("/tmp/output"),
        )
        assert ctx.domain == "web"
        assert ctx.product == "orangehrm"
        assert ctx.env == "staging"
        assert ctx.locale == "fr-FR"

    def test_get_returns_extra_value(self):
        ctx = AgentContext(domain="api", extra={"browser": "firefox"})
        assert ctx.get("browser") == "firefox"

    def test_get_returns_default_for_missing_key(self):
        ctx = AgentContext(domain="api")
        assert ctx.get("nonexistent", "default_val") == "default_val"

    def test_get_returns_none_default(self):
        ctx = AgentContext(domain="api")
        assert ctx.get("missing") is None

    def test_extend_creates_new_context(self):
        ctx = AgentContext(domain="web", product="acme")
        extended = ctx.extend(browser="chrome", auth_type="oauth2")
        assert extended is not ctx

    def test_extend_preserves_base_fields(self):
        ctx = AgentContext(domain="mobile", product="orangehrm", env="staging")
        extended = ctx.extend(device="pixel")
        assert extended.domain == "mobile"
        assert extended.product == "orangehrm"
        assert extended.env == "staging"

    def test_extend_adds_extra_dimensions(self):
        ctx = AgentContext(domain="api")
        extended = ctx.extend(api_version="v2", tenant="acme")
        assert extended.get("api_version") == "v2"
        assert extended.get("tenant") == "acme"

    def test_extend_merges_with_existing_extra(self):
        ctx = AgentContext(domain="api", extra={"existing": "yes"})
        extended = ctx.extend(new_key="new_val")
        assert extended.get("existing") == "yes"
        assert extended.get("new_key") == "new_val"

    def test_extend_does_not_mutate_original(self):
        ctx = AgentContext(domain="api", extra={"key": "original"})
        ctx.extend(key="overridden")
        assert ctx.get("key") == "original"

    def test_extend_overrides_extra_key(self):
        ctx = AgentContext(domain="api", extra={"key": "old"})
        extended = ctx.extend(key="new")
        assert extended.get("key") == "new"


# ── BaseAgent ─────────────────────────────────────────────────────────────────

class TestBaseAgent:
    def test_init_default_context(self):
        agent = BaseAgent()
        assert agent.ctx.domain == "api"

    def test_init_with_context(self):
        ctx = AgentContext(domain="web", product="orangehrm")
        agent = BaseAgent(context=ctx)
        assert agent.ctx.domain == "web"
        assert agent.ctx.product == "orangehrm"

    def test_init_ai_client_stored(self):
        class FakeClient:
            pass
        client = FakeClient()
        agent = BaseAgent(ai_client=client)
        assert agent.client is client

    def test_init_kb_loader_stored(self):
        class FakeKB:
            pass
        kb = FakeKB()
        agent = BaseAgent(kb_loader=kb)
        assert agent.kb is kb

    def test_run_raises_not_implemented(self):
        agent = BaseAgent()
        with pytest.raises(NotImplementedError):
            agent.run()

    def test_log_named_after_agent(self):
        import logging

        class MyAgent(BaseAgent):
            name = "my_test_agent"

        agent = MyAgent()
        assert agent._log.name == "sentinelflux.agents.my_test_agent"

    def test_artifact_names_for_api_domain(self):
        ctx = AgentContext(domain="api")
        agent = BaseAgent(context=ctx)
        artifacts = agent._artifact_names()
        assert "api_calls.log" in artifacts

    def test_artifact_names_for_web_domain(self):
        ctx = AgentContext(domain="web")
        agent = BaseAgent(context=ctx)
        artifacts = agent._artifact_names()
        assert "screenshot_full_page.png" in artifacts
        assert "console.log" in artifacts

    def test_artifact_names_empty_for_unknown_domain(self):
        ctx = AgentContext(domain="unknown_domain")
        agent = BaseAgent(context=ctx)
        assert agent._artifact_names() == []

    def test_failure_hint_for_api_domain(self):
        ctx = AgentContext(domain="api")
        agent = BaseAgent(context=ctx)
        hint = agent._failure_hint()
        assert "HTTP" in hint or "status" in hint.lower()

    def test_failure_hint_empty_for_unknown_domain(self):
        ctx = AgentContext(domain="unknown")
        agent = BaseAgent(context=ctx)
        assert agent._failure_hint() == ""

    def test_prompt_key_for_api(self):
        ctx = AgentContext(domain="api")
        agent = BaseAgent(context=ctx)
        assert agent._prompt_key() == "API_TEST_GENERATION_PROMPT"

    def test_prompt_key_for_web(self):
        ctx = AgentContext(domain="web")
        agent = BaseAgent(context=ctx)
        assert agent._prompt_key() == "TEST_SCRIPT_GEN_PROMPT"

    def test_prompt_key_unknown_domain_falls_back(self):
        ctx = AgentContext(domain="grpc")
        agent = BaseAgent(context=ctx)
        assert agent._prompt_key() == "GRPC"

    def test_domain_marker_for_api(self):
        ctx = AgentContext(domain="api")
        agent = BaseAgent(context=ctx)
        assert agent._domain_marker() == "api"

    def test_domain_marker_for_graphql(self):
        ctx = AgentContext(domain="graphql")
        agent = BaseAgent(context=ctx)
        assert agent._domain_marker() == "api"

    def test_domain_fixtures_for_api(self):
        ctx = AgentContext(domain="api")
        agent = BaseAgent(context=ctx)
        assert "rest_client" in agent._domain_fixtures()

    def test_domain_fixtures_for_web(self):
        ctx = AgentContext(domain="web")
        agent = BaseAgent(context=ctx)
        assert "page" in agent._domain_fixtures()

    def test_domain_fixtures_empty_for_unknown(self):
        ctx = AgentContext(domain="unknown")
        agent = BaseAgent(context=ctx)
        assert agent._domain_fixtures() == []

    def test_subclass_can_implement_run(self):
        class EchoAgent(BaseAgent):
            name = "echo"
            def run(self, **kwargs) -> dict:
                return {"echoed": kwargs}

        agent = EchoAgent()
        result = agent.run(test="value")
        assert result == {"echoed": {"test": "value"}}
