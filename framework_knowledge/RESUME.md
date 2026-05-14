# SentinelFlux — AI Resume Context

> **READ THIS FIRST.** Any AI tool working on this project should read this file before anything else.

Last updated: 2026-05-14  
Framework version: 0.1.0

---

## What This Project Is

Solo-built test automation framework covering API, UI, Mobile (scaffold), and Security (scaffold). Dual purpose: learning vehicle + potential product. Owner has 13+ yrs QE/SDE experience. Budget-constrained — be token-efficient.

---

## Current State

| Layer | Status | Notes |
|---|---|---|
| REST API | Working | Full CRUD, schema validation, data-driven, curl log on failure |
| GraphQL | Working | Query + variable support |
| Web UI | Working | POM + self-healing locators (3-tier) |
| Mobile | Scaffolded | Appium dep present, zero implementation |
| Security | Scaffolded | Marker only, nothing implemented |
| AI/KB Pipeline | Working | KB → doc → script (Mistral + Ollama/Qwen). `ai/pipeline/orchestrator.py` |
| AI Agents (post-suite) | Working | ResultAnalyzer, FlakyDetector, RegressionGuard, CoverageGap, LocatorHealer, QuarantineManager via `ai/agents/sentinel_orchestrator.py` |
| Dashboard | Working | FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind. 16 pages/routers. Start: `uvicorn dashboard.app:app --reload` |
| Runs | Working | Trigger/schedule pytest runs from dashboard, parse JSON reports, auto-analyze failures. `/runs` page |
| CLI | Working | `sentinelflux init/run/generate/doctor` via typer |
| Examples | Working | OrangeHRM (web+api), Restful Booker (13 API tests passing) |
| Docs site | Built | mkdocs-material, `mkdocs serve` to preview |
| Package | Built | `pyproject.toml` + hatchling, `pip install sentinelflux` |

---

## What Was Just Done (2026-05-14)

- **Dashboard**: Full monitoring UI at `/` — stat cards, pipeline execution flowchart showing live agent status
- **Agents page** (`/agents`): Registry of all 9 agents with last run status, config overrides, input/output docs
- **Activities page** (`/activities`): Filterable event log from `activity_log.json`
- **Approvals page** (`/approvals`): Human-in-the-loop queue for quarantine/regression/locator actions
- **Quality page** (`/quality`): Pass rates, quarantine stats, coverage metrics per product
- **KB page** (`/kb`): Browse/edit KB YAML files, trigger AI pipeline, view jobs
- **Runs page** (`/runs`): Trigger suite runs by product/domain, view history with pass-rate bars and failure category pills (Product Bug / Env Issue / Script/Data), schedule recurring runs, on-demand failure analysis via ResultAnalyzerAgent
- **Auth**: Login/session, user-product access control
- **Config page** (`/config`): Manage env configs, users, assignments, labels, priorities
- **AI Chat widget** (global): LLM-backed assistant, pluggable provider (Ollama/OpenAI/Anthropic/Gemini)

---

## Previous Sprints (1–4, 2026-05-08)

- Sprint 1: Apache 2.0 license, `pyproject.toml`, CLI (`init/run/generate`), OrangeHRM moved to `examples/`, GitHub Actions CI
- Sprint 2: mkdocs docs site, `sentinelflux doctor`, PyPI publish workflow, CONTRIBUTING.md, issue templates
- Sprint 3: Restful Booker second example (22 tests, 13/13 API passing), `sentinelflux init` smoke-tested
- Sprint 4: Product KB separation — per-product `ai/knowledge_base/<product>/` dirs, `--kb-dir` CLI flag

---

## Next Immediate Actions

1. **File locking** — `ActivityLog`, `ApprovalManager`, `RunManager`, `PipelineJobs` all write JSON/YAML without locks. Concurrent xdist runs + dashboard triggers will corrupt data. Add `filelock.FileLock` to each writer.
2. **`run_history.yaml` cap** — grows unbounded; FlakyDetector reads the whole file. Add a rolling 90-day window trim.
3. **Test `sentinelflux generate` end-to-end** — `./run_pipeline.sh restfulbooker booking api` against running Qwen
4. **Run web tests** — `make restfulbooker-web` and `make orangehrm-web`
5. **v0.1.0 tag + PyPI publish** when ready

Framework-level feature backlog: `framework_knowledge/progress/backlog.yaml`

---

## Key Architectural Decisions

- AI client: Mistral (cloud) or Ollama (local). Abstracted behind `AIClient` base. See `ADR-002`.
- KB structure: YAML files in `ai/knowledge_base/<product>/` (one dir per product). Increments in `ai/knowledge_base/increments/`.
- Per-product output: `examples/<product>/docs/test_cases/` and `examples/<product>/tests/`. Pass `--output-base examples/<product>` to orchestrator.
- Schema location: `schemas/rest_schemas/` is canonical. `api/schemas/` is dead code — do not use.
- All magic numbers: `utils/constants.py`
- RP API key: env var `RP_API_KEY` only, never committed.
- `BasePage.__init__(page, locale="en-US")` — NO base_url param; subclass stores URL as instance variable.
- `booking_client.py` lives at `examples/restfulbooker/` root (not `api/` subdir) — avoids namespace package collision under pytest.

---

## Where Things Live

```
ai/knowledge_base/<product>/    Per-product KB (application, api_specs, ui_pages, product_knowledge)
ai/knowledge_base/increments/   Feature drop YAMLs
ai/knowledge_base/kb_loader.py  Loads base + increments, formats context for prompts
ai/clients/mistral_client.py    LLM client (cloud + local Ollama)
ai/agents/                      9 agents: ResultAnalyzer, FlakyDetector, RegressionGuard,
                                  CoverageGap, LocatorHealer, QuarantineManager, DocGen,
                                  ScriptGen, SentinelOrchestrator
ai/agents/sentinel_orchestrator.py  Post-suite monitoring pipeline (chains all agents)
ai/pipeline/orchestrator.py     End-to-end KB → doc → script (supports --output-base)
api/rest_client.py              REST API test client (supports data_dir param)
api/graphql_client.py           GraphQL test client
pages/base_page.py              Base POM with self-healing locators
sentinelflux/                   CLI commands (init, run, generate, doctor)
utils/constants.py              All magic numbers
utils/ai_factory.py             AI client instantiation (do not duplicate in conftest)
utils/activity_log.py           Append-only event store → framework_knowledge/activity_log.json
utils/approval_manager.py       Human-in-the-loop approvals → framework_knowledge/pending_approvals.yaml
utils/run_manager.py            Test run records + schedules → framework_knowledge/test_runs.json
conftest.py                     Generic fixtures — NO product references
examples/orangehrm/             OrangeHRM example (web + API + KB)
examples/restfulbooker/         Restful Booker example (API + KB)
framework_knowledge/            Tracking system (activity log, approvals, runs, quarantine, KB log)
dashboard/app.py                FastAPI app entry point — registers all 16 routers
dashboard/routers/pages.py      All UI page routes (/, /runs, /agents, /activities, /kb, etc.)
dashboard/routers/runs.py       Test run API + trigger + schedule endpoints
dashboard/routers/pipeline.py   AI pipeline job trigger + job history
dashboard/routers/config_router.py  Environment/user/assignment config (908 lines — large)
dashboard/templates/            Jinja2 templates (one per page + partials/ subdir)
```

---

## Dashboard — How to Add a Page

1. Add route handler to `dashboard/routers/pages.py` (see existing pattern — use `_ctx()` + `_require_auth`)
2. Create `dashboard/templates/<page>.html` extending `base.html`
3. Add nav entry in `base.html` nav_items list (href, label, svg path)
4. Register any new JSON API router in `dashboard/app.py` under `/api` prefix

---

## Conventions (quick ref)

- Test files: `examples/<product>/tests/{domain}/test_{feature_name}.py`
- KB per product: `ai/knowledge_base/<product>/`
- Generated docs: `examples/<product>/docs/test_cases/{domain}/{feature_name}.md`
- Generated scripts: `examples/<product>/tests/{domain}/test_{feature_name}.py`
- Locator files: `locators/{platform}/{page_name}.json` with `primary` + `alternatives`
- Config per env: `config/env_{qa|staging|prod}.yaml`
- All timeouts/magic numbers: define in `utils/constants.py`, import everywhere
- Failure categories in ResultAnalyzerAgent: `assertion`=Product Bug, `env`+`infra`=Env Issue, `locator`+`flaky`=Script/Data

---

## Do Not

- Do not hardcode API keys or tokens anywhere — use env vars
- Do not add `@lru_cache` to instance methods — use `self._cache` dict
- Do not create files under `api/schemas/` — dead code
- Do not duplicate AI factory logic — use `utils/ai_factory.py`
- Do not add magic numbers inline — add to `utils/constants.py`
- Do not put product-specific imports in root `conftest.py`
- Do not put `booking_client.py` inside `api/` subdir in examples — namespace collision under pytest
- Do not write to `framework_knowledge/` files without checking for concurrent access — no file locking exists yet

---

## AI Doc Generation — Anti-Hallucination Rules

1. **Only test KB-listed fields.** If a field is not in the KB context, it does not exist on that form.
2. **Do not use training-data knowledge of the AUT.** KB context is the only truth.
3. **Add Employee ≠ Employee Profile.** OrangeHRM's Add Employee form has 4 fields only: First Name, Last Name, Middle Name, Employee ID.
4. **Use real credentials.** OrangeHRM demo: `Admin / admin123`. Restful Booker: `admin / password123` (API), `admin / password` (web).
5. **Prompt templates enforce this** via STRICT RULES blocks — if modifying prompts, preserve those blocks.
