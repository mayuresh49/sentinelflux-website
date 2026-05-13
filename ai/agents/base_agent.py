"""
BaseAgent + AgentContext — shared foundation for all SentinelFlux agents.

Extensibility model
-------------------
Built-in dimensions on AgentContext: domain, product, env, locale, output_base.
These cover the most common axes of variation today.

For any NEW dimension (browser, auth_type, tenant, api_version, …):
  1. Pass it in ctx.extra at call time — no schema change needed.
  2. Retrieve it inside agents with ctx.get("dimension_name", default).
  3. Add domain-specific routing for it in ai/agents/registry.py if needed.

To add a new DOMAIN (graphql, grpc, desktop, …):
  1. Add entries to the four dicts in registry.py.
  2. No changes to BaseAgent or any existing agent.

To add a new AGENT:
  1. Subclass BaseAgent, set name, implement run(**kwargs) -> dict.
  2. Register it in __init__.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentContext:
    """
    Carries all dimension parameters for an agent invocation.

    Extra params example:
        ctx = AgentContext(domain="web", product="orangehrm")
        ctx2 = ctx.extend(browser="firefox", auth_type="oauth2")
        agent.run(context=ctx2, ...)
    """
    domain: str                                   # api | web | mobile | security
    product: str | None = None                    # e.g. "orangehrm", "restfulbooker"
    env: str = "qa"                               # qa | staging | prod
    locale: str = "en-US"
    output_base: Path | None = None               # root dir for generated file outputs
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an extra dimension value."""
        return self.extra.get(key, default)

    def extend(self, **kwargs: Any) -> "AgentContext":
        """Return a new context with additional dimensions merged into extra."""
        return AgentContext(
            domain=self.domain,
            product=self.product,
            env=self.env,
            locale=self.locale,
            output_base=self.output_base,
            extra={**self.extra, **kwargs},
        )


class BaseAgent:
    """
    All agents inherit from this. Subclasses must:
      - Set class attribute ``name`` (used for logging)
      - Implement ``run(**kwargs) -> dict``

    Convention: run() always returns a dict so callers can chain agents without
    knowing the exact output shape of each one.
    """
    name: str = "base"

    def __init__(
        self,
        ai_client=None,
        kb_loader=None,
        context: AgentContext | None = None,
    ):
        self.client = ai_client
        self.kb = kb_loader
        self.ctx = context or AgentContext(domain="api")
        self._log = logging.getLogger(f"sentinelflux.agents.{self.name}")

    def run(self, **kwargs) -> dict:
        raise NotImplementedError

    # ── domain-aware helpers (delegates to registry) ───────────────────────

    def _artifact_names(self) -> list[str]:
        from ai.agents.registry import ARTIFACT_PATHS
        return ARTIFACT_PATHS.get(self.ctx.domain, [])

    def _failure_hint(self) -> str:
        from ai.agents.registry import FAILURE_HINTS
        return FAILURE_HINTS.get(self.ctx.domain, "")

    def _prompt_key(self) -> str:
        from ai.agents.registry import PROMPT_KEYS
        return PROMPT_KEYS.get(self.ctx.domain, self.ctx.domain.upper())

    def _domain_marker(self) -> str:
        from ai.agents.registry import DOMAIN_MARKERS
        return DOMAIN_MARKERS.get(self.ctx.domain, self.ctx.domain)

    def _domain_fixtures(self) -> list[str]:
        from ai.agents.registry import DOMAIN_FIXTURES
        return DOMAIN_FIXTURES.get(self.ctx.domain, [])
