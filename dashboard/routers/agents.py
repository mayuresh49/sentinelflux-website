from __future__ import annotations

from fastapi import APIRouter

from core.activity_log import ActivityLog

router = APIRouter(prefix="/agents", tags=["agents"])

_AGENT_REGISTRY = [
    {"name": "app_explorer", "description": "Crawls the running app with Playwright to discover real UI elements, selectors, and flows — grounds doc/script generation in verified DOM structure", "domain": "web,mobile", "requires_ai": False},
    {"name": "doc_gen", "description": "Generates test case docs from KB", "domain": "all", "requires_ai": True},
    {"name": "doc_review", "description": "Reviews generated docs, rewrites thin or malformed test cases", "domain": "all", "requires_ai": True},
    {"name": "script_gen", "description": "Generates pytest scripts from test case docs", "domain": "all", "requires_ai": True},
    {"name": "script_review", "description": "Reviews generated scripts for assertion quality, conventions, and anti-patterns", "domain": "all", "requires_ai": True},
    {"name": "result_analyzer", "description": "Classifies test failures using AI", "domain": "all", "requires_ai": True},
    {"name": "flaky_detector", "description": "Rule-based flaky test detection from run history", "domain": "all", "requires_ai": False},
    {"name": "regression_guard", "description": "Compares current run against baseline", "domain": "all", "requires_ai": False},
    {"name": "coverage_gap", "description": "Diffs KB scenarios vs existing tests", "domain": "all", "requires_ai": True},
    {"name": "locator_healer", "description": "Proposes healed UI selectors for failing elements", "domain": "web,mobile", "requires_ai": True},
    {"name": "quarantine_manager", "description": "Manages test quarantine lifecycle", "domain": "all", "requires_ai": False},
    {"name": "sentinel_orchestrator", "description": "Coordinates all monitoring agents post-suite", "domain": "all", "requires_ai": False},
    {"name": "product_manager", "description": "Reviews SentinelFlux from a product management perspective", "domain": "product", "requires_ai": True},
    {"name": "dev_architect", "description": "Reviews SentinelFlux architecture, tech debt, and security", "domain": "product", "requires_ai": True},
    {"name": "qa_architect", "description": "Reviews testing strategy, coverage, and quality infrastructure", "domain": "product", "requires_ai": True},
    {"name": "ux_architect", "description": "Reviews dashboard UX and information architecture", "domain": "product", "requires_ai": True},
    {"name": "cto", "description": "Synthesises all expert insights into a strategic top-5 roadmap", "domain": "product", "requires_ai": True},
]


_PUBLIC_REGISTRY = [a for a in _AGENT_REGISTRY if a["domain"] != "product"]


@router.get("/")
def list_agents():
    return {"agents": _PUBLIC_REGISTRY, "total": len(_PUBLIC_REGISTRY)}


@router.get("/status")
def agent_status():
    """Last activity entry per agent, most recent first."""
    alog = ActivityLog()
    entries = alog.all()
    seen: dict[str, dict] = {}
    for e in reversed(entries):
        name = e.get("agent", "")
        if name and name not in seen:
            seen[name] = {
                "agent": name,
                "last_run": e["timestamp"],
                "status": e["status"],
                "summary": e["summary"],
                "requires_human": e.get("requires_human", False),
            }
    return {"status": list(seen.values())}


@router.get("/{agent_name}")
def get_agent(agent_name: str):
    meta = next((a for a in _PUBLIC_REGISTRY if a["name"] == agent_name), None)
    if not meta:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    alog = ActivityLog()
    history = [e for e in alog.all() if e.get("agent") == agent_name]
    return {**meta, "run_count": len(history), "recent_runs": list(reversed(history))[-10:]}
