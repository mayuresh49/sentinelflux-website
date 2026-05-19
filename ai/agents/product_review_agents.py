"""Product review agents — PM, Dev Architect, QA Architect, UX Architect.

Each agent reads codebase context and calls the configured LLM to produce
structured insights about SentinelFlux from their expertise perspective.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ai.agents.base_agent import BaseAgent

_ROOT = Path(__file__).resolve().parents[2]

_INSIGHT_SCHEMA = """\
Return a JSON object only — no markdown fences, no prose:
{
  "insights": [
    {
      "title": "<short, specific title>",
      "description": "<2-3 sentences describing the issue or opportunity>",
      "recommendation": "<concrete, actionable next step>",
      "category": "<feature|risk|debt|opportunity|process>",
      "priority": "<high|medium|low>"
    }
  ]
}
Generate 5-8 insights. Be specific, critical, and actionable."""


def _read(path: Path, max_chars: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def _parse_insights(raw: str) -> list[dict]:
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
        items = data.get("insights", data) if isinstance(data, dict) else data
    except (json.JSONDecodeError, TypeError):
        return []
    validated = []
    for ins in (items if isinstance(items, list) else []):
        if not isinstance(ins, dict) or not ins.get("title"):
            continue
        ins.setdefault("description", "")
        ins.setdefault("recommendation", "")
        ins.setdefault("category", "opportunity")
        ins.setdefault("priority", "medium")
        if ins["category"] not in {"feature", "risk", "debt", "opportunity", "process"}:
            ins["category"] = "opportunity"
        if ins["priority"] not in {"high", "medium", "low"}:
            ins["priority"] = "medium"
        validated.append(ins)
    return validated


class ProductManagerAgent(BaseAgent):
    """Reviews SentinelFlux from a product management perspective."""
    name = "product_manager"

    def run(self, **kwargs) -> dict:
        if not self.client:
            return {"agent_type": self.name, "insights": [], "error": "No AI client configured"}
        resume = _read(_ROOT / "ai" / "context" / "RESUME.md", 6000)
        backlog = _read(_ROOT / "ai" / "context" / "progress" / "backlog.yaml", 3000)
        prompt = f"""\
You are a senior product manager reviewing SentinelFlux — a solo-built test automation framework
that serves as both a learning vehicle and a potential commercial product.

Project state:
{resume}

Current backlog:
{backlog}

Analyse from a product management perspective. Consider:
- Feature completeness and gaps vs market expectations for a test automation tool
- Backlog prioritisation — what's most valuable to build next
- User value delivery, onboarding experience, and time-to-value for new users
- Monetisation potential and target customer fit
- Competitive positioning vs tools like Playwright, Cypress, Robot Framework, Testsigma
- Missing product pillars (documentation, examples, integrations, ecosystem)

{_INSIGHT_SCHEMA}"""
        raw = self.client.generate(prompt, max_tokens=2500, temperature=0.4)
        insights = _parse_insights(raw)
        self._log.info("ProductManagerAgent: %d insights", len(insights))
        return {"agent_type": self.name, "insights": insights}


class DevArchitectAgent(BaseAgent):
    """Reviews SentinelFlux from a software architecture perspective."""
    name = "dev_architect"

    def run(self, **kwargs) -> dict:
        if not self.client:
            return {"agent_type": self.name, "insights": [], "error": "No AI client configured"}
        resume = _read(_ROOT / "ai" / "context" / "RESUME.md", 5000)
        db_schema = _read(_ROOT / "core" / "db.py", 3000)
        app_entry = _read(_ROOT / "dashboard" / "app.py", 2000)
        prompt = f"""\
You are a senior software architect reviewing SentinelFlux — a test automation framework
built with FastAPI, SQLite, Alpine.js, HTMX, and Playwright.

Project state:
{resume}

Database schema (core/db.py excerpt):
{db_schema}

Application entry point (dashboard/app.py excerpt):
{app_entry}

Analyse from a software architecture perspective. Consider:
- Architectural patterns, coupling, and separation of concerns
- Technical debt and refactoring opportunities
- Scalability and performance risks as the product grows
- Security posture (auth, session handling, injection risks, secrets management)
- Missing engineering infrastructure (database migrations, CI/CD, observability, error tracking)
- Testability of the framework itself (meta: how well is the framework tested?)
- Code quality signals and maintainability risks

{_INSIGHT_SCHEMA}"""
        raw = self.client.generate(prompt, max_tokens=2500, temperature=0.4)
        insights = _parse_insights(raw)
        self._log.info("DevArchitectAgent: %d insights", len(insights))
        return {"agent_type": self.name, "insights": insights}


class QAArchitectAgent(BaseAgent):
    """Reviews SentinelFlux's testing strategy and quality infrastructure."""
    name = "qa_architect"

    def run(self, **kwargs) -> dict:
        if not self.client:
            return {"agent_type": self.name, "insights": [], "error": "No AI client configured"}
        resume = _read(_ROOT / "ai" / "context" / "RESUME.md", 5000)
        conftest = _read(_ROOT / "conftest.py", 2000)
        pytest_ini = _read(_ROOT / "pytest.ini", 500)
        products_dir = _ROOT / "products"
        domain_counts: dict[str, int] = {}
        for f in products_dir.rglob("test_*.py"):
            parts = f.relative_to(products_dir).parts
            if len(parts) >= 3 and parts[1] == "tests":
                domain_counts[parts[2]] = domain_counts.get(parts[2], 0) + 1
        coverage_summary = "\n".join(
            f"- {d}: {n} test files" for d, n in sorted(domain_counts.items())
        ) or "(no test files detected)"
        prompt = f"""\
You are a senior QA architect reviewing SentinelFlux — a test automation framework
that also needs to be well-tested itself.

Project state:
{resume}

Root conftest.py:
{conftest}

pytest.ini:
{pytest_ini}

Test coverage by domain:
{coverage_summary}

Analyse from a QA architecture perspective. Consider:
- Test pyramid balance for the framework itself (unit/integration/e2e of the framework code)
- Test data management, environment isolation, and reproducibility
- AI-generated test quality — how well does the pipeline produce maintainable tests?
- Flakiness risks in the generated test suites
- Reporting and observability gaps (what's hard to debug when tests fail?)
- CI/CD integration and gate quality
- Missing test types or domains in the generated test coverage
- Framework reliability — does the framework's own infrastructure have adequate test coverage?

{_INSIGHT_SCHEMA}"""
        raw = self.client.generate(prompt, max_tokens=2500, temperature=0.4)
        insights = _parse_insights(raw)
        self._log.info("QAArchitectAgent: %d insights", len(insights))
        return {"agent_type": self.name, "insights": insights}


class UXArchitectAgent(BaseAgent):
    """Reviews SentinelFlux's dashboard UX and information architecture."""
    name = "ux_architect"

    def run(self, **kwargs) -> dict:
        if not self.client:
            return {"agent_type": self.name, "insights": [], "error": "No AI client configured"}
        resume = _read(_ROOT / "ai" / "context" / "RESUME.md", 4000)
        templates_dir = _ROOT / "dashboard" / "templates"
        template_names = sorted(
            f.name for f in templates_dir.glob("*.html") if not f.name.startswith("_")
        )
        nav_html = _read(_ROOT / "dashboard" / "templates" / "base.html", 3000)
        prompt = f"""\
You are a senior UX architect reviewing the web dashboard of SentinelFlux — a test automation
framework with a FastAPI + Alpine.js + HTMX dashboard.

Project state:
{resume}

Dashboard pages ({len(template_names)} pages total):
{chr(10).join("- " + n for n in template_names)}

Navigation and layout HTML (base.html excerpt):
{nav_html}

Analyse from a UX and information architecture perspective. Consider:
- Navigation structure and page organisation — is the information hierarchy logical?
- Feature discoverability — can a new user find and use the key features?
- Cognitive load — are there pages that try to do too much?
- Onboarding experience — what does a new user see first, and is it helpful?
- Consistency of UI patterns (modals, toasts, tables, forms) across pages
- Missing user workflows, dead ends, or confusing transitions
- Accessibility and keyboard navigation
- Mobile/responsive design considerations
- Dashboard as a product — would a paying customer find this dashboard intuitive?

{_INSIGHT_SCHEMA}"""
        raw = self.client.generate(prompt, max_tokens=2500, temperature=0.4)
        insights = _parse_insights(raw)
        self._log.info("UXArchitectAgent: %d insights", len(insights))
        return {"agent_type": self.name, "insights": insights}
