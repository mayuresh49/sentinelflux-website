# SentinelFlux — AI Resume Context

> **READ THIS FIRST.** Any AI tool working on this project should read this file before anything else.

Last updated: 2026-05-16  
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
| DocReviewAgent | Working | Post-generation quality gate — audits batched headings, missing sections, thin steps; rewrites via LLM. Auto-runs after DocGenAgent in pipeline. `ai/agents/doc_review_agent.py` |
| Remote Runner | Working | Pull-based runner daemon (`sentinelflux runner`) polls `/api/runner/claim`, executes pytest, POSTs JSON report back. Bearer token auth. Decouples test execution from app server. |
| Multi-tenant Storage | Working | Per-product run/schedule sharding (`data/test_runs/<product>.json`), per-product run config YAML (`data/product_config/<product>.yaml`), O(1) run→product index at `data/run_product_index.json` |
| Dashboard | Working | FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind. 16 pages/routers. Start: `uvicorn dashboard.app:app --reload` |
| Runs | Working | Trigger/schedule pytest runs from dashboard, parse JSON reports, auto-analyze failures. `/runs` page |
| CLI | Working | `sentinelflux init/run/generate/doctor` via typer |
| Examples | Working | OrangeHRM (web+api), Restful Booker (13 API tests passing) |
| Docs site | Built | mkdocs-material, `mkdocs serve` to preview |
| Package | Built | `pyproject.toml` + hatchling, `pip install sentinelflux` |

---

## What Was Just Done (2026-05-16)

- **DocReviewAgent** (`ai/agents/doc_review_agent.py`): Post-generation quality gate. Detects batched TC headings (e.g. `OH-WEB-036 to OH-WEB-043`), missing mandatory sections (Pre-conditions, Steps, Expected Result), and thin TCs (<3 steps). Rewrites each failing TC via targeted LLM prompt + KB context. Integrated into `TestPipelineOrchestrator._review_doc()` (best-effort, never raises). Visible in `/agents` dashboard with full responsibility/inputs/outputs metadata.
- **DocGenAgent prompt hardening**: `TEST_CASE_DOC_PROMPT` and `API_TEST_CASE_DOC_PROMPT` upgraded with mandatory Fields-in-Scope rule, prohibition on range headings, min-3-steps rule, and per-TC format block. max_tokens raised: web/feature 3000→6000, API 3000→4000.
- **Multi-tenant run storage**: `core/run_manager.py` rewritten — per-product sharding to `data/test_runs/<product>.json` and `data/test_schedules/<product>.json`. O(1) run→product lookup via `data/run_product_index.json` (FileLock protected). Lazy migration from legacy flat files on first access. Global 200-run cap is now per-product.
- **Per-product run config YAML**: `dashboard/routers/config/_run_config.py` reads/writes `data/product_config/<product>.yaml`. Lazy migration fallback reads from `data/config.yaml` on first access.
- **Remote runner** (`dashboard/routers/runner.py`): Pull-based execution — `GET /api/runner/claim` returns next queued run, `POST /api/runner/{id}/progress` streams progress, `POST /api/runner/{id}/result` ingests JSON report and triggers AI analysis. Bearer token auth (bcrypt hashed) via `dashboard/routers/auth.py:require_runner_token`.
- **Runner token admin** (`dashboard/routers/config/_runners.py`): Admin CRUD for runner tokens. `POST` returns plain token once; only bcrypt hash stored.
- **`sentinelflux runner` CLI daemon** (`sentinelflux/commands/runner_cmd.py`): Polls claim endpoint, resolves test path from product/domain/module, builds env overrides from `run_config_snapshot`, runs pytest subprocess, streams progress every 5s, posts JSON report.

## Previous: Per-product Run Config + Env Injection (2026-05-15)

- **Per-product Run Config** (`/config` → Run Config tab): CRUD for environment profiles (name, base URL, API URL), browser profiles (chromium/firefox/webkit, headless), device profiles (platform, appium URL, capabilities JSON), credentials (username + password env var ref), and saved defaults per product. Data stored in `data/config.yaml` under each product's `run_config` key.
- **Run trigger with config**: Trigger panel and schedule form now load the product's run config profiles on product selection (Alpine.js fetch to `GET /api/config/run-config/{product}`); browser shown only for web/all, device only for mobile/all; defaults pre-selected.
- **Env injection into pytest**: `_execute_run` resolves the chosen profiles and injects `SF_ENV`, `SF_BASE_URL`, `SF_API_URL`, `SF_BROWSER`, `SF_HEADLESS`, `SF_APPIUM_URL`, `SF_DEVICE_PLATFORM`, `SF_DEVICE_CAPABILITIES` into the subprocess environment.
- **Run history snapshot**: Each run record stores `run_config_snapshot`; shown as monospace pills in run history cards. Reruns inherit the original config.
- **Debt D-01–D-06 resolved** (prior session): file locking (FileLock), 90-day run_history cap, `utils/paths.py` centralisation, config_router split into subpackage, unit tests for core utils, OpenAI/Anthropic wired to AI client.

## Previous: Dashboard Build (2026-05-14)

- **Dashboard**: Full monitoring UI at `/` — stat cards, pipeline execution flowchart showing live agent status
- **Agents page** (`/agents`): Registry of all 9 agents with last run status, config overrides, input/output docs
- **Activities page** (`/activities`): Filterable event log from `activity_log.json`
- **Approvals page** (`/approvals`): Human-in-the-loop queue for quarantine/regression/locator actions
- **Quality page** (`/quality`): Pass rates, quarantine stats, coverage metrics per product
- **KB page** (`/kb`): Browse/edit KB YAML files, trigger AI pipeline, view jobs
- **Runs page** (`/runs`): Trigger suite runs by product/domain/env/browser/device, view history with pass-rate bars, failure category pills, and config snapshot badges (env/browser/device used); schedule recurring runs with config; on-demand failure analysis via ResultAnalyzerAgent
- **Auth**: Login/session, user-product access control
- **Config page** (`/config`): Manage env configs, users, assignments, labels, priorities, and per-product Run Config (environments, browsers, devices, credentials, defaults)
- **AI Chat widget** (global): LLM-backed assistant, pluggable provider (Ollama/OpenAI/Anthropic/Gemini)

---

## Previous Sprints (1–4, 2026-05-08)

- Sprint 1: Apache 2.0 license, `pyproject.toml`, CLI (`init/run/generate`), OrangeHRM moved to `products/`, GitHub Actions CI
- Sprint 2: mkdocs docs site, `sentinelflux doctor`, PyPI publish workflow, CONTRIBUTING.md, issue templates
- Sprint 3: Restful Booker second example (22 tests, 13/13 API passing), `sentinelflux init` smoke-tested
- Sprint 4: Product KB separation — per-product `ai/knowledge_base/<product>/` dirs, `--kb-dir` CLI flag

---

## Next Immediate Actions

1. **Wire SF_* env vars into conftest/config loader** — tests need to read `SF_BASE_URL`, `SF_BROWSER`, etc. instead of hardcoded values for the run config injection to take effect end-to-end.
2. **Test `sentinelflux generate` end-to-end** — `./run_pipeline.sh restfulbooker booking api` against running Qwen
3. **Run web tests** — `make restfulbooker-web` and `make orangehrm-web`
4. **v0.1.0 tag + PyPI publish** when ready

Framework-level feature backlog: `ai/context/progress/backlog.yaml`

---

## Key Architectural Decisions

- AI client: Mistral (cloud) or Ollama (local). Abstracted behind `AIClient` base. See `ADR-002`.
- KB structure: YAML files in `ai/knowledge_base/<product>/` (one dir per product). Increments in `ai/knowledge_base/increments/`.
- Per-product output: `products/<product>/docs/test_cases/` and `products/<product>/tests/`. Pass `--output-base products/<product>` to orchestrator.
- Schema location: `schemas/rest_schemas/` is canonical. `api/schemas/` is dead code — do not use.
- All magic numbers: `utils/constants.py`
- RP API key: env var `RP_API_KEY` only, never committed.
- `BasePage.__init__(page, locale="en-US")` — NO base_url param; subclass stores URL as instance variable.
- `booking_client.py` lives at `products/restfulbooker/` root (not `api/` subdir) — avoids namespace package collision under pytest.

---

## Where Things Live

```
ai/knowledge_base/<product>/    Per-product KB (application, api_specs, ui_pages, product_knowledge)
ai/knowledge_base/increments/   Feature drop YAMLs
ai/knowledge_base/kb_loader.py  Loads base + increments, formats context for prompts
ai/clients/mistral_client.py    LLM client (cloud + local Ollama)
ai/agents/                      10 agents: ResultAnalyzer, FlakyDetector, RegressionGuard,
                                  CoverageGap, LocatorHealer, QuarantineManager, DocGen,
                                  DocReview, ScriptGen, SentinelOrchestrator
ai/agents/doc_review_agent.py   Post-generation quality gate (regex audit + LLM rewrite)
ai/agents/sentinel_orchestrator.py  Post-suite monitoring pipeline (chains all agents)
ai/pipeline/orchestrator.py     End-to-end KB → doc → script (supports --output-base)
api/rest_client.py              REST API test client (supports data_dir param)
api/graphql_client.py           GraphQL test client
pages/base_page.py              Base POM with self-healing locators
sentinelflux/                   CLI commands (init, run, generate, doctor)
utils/constants.py              All magic numbers
utils/ai_factory.py             AI client instantiation (do not duplicate in conftest)
utils/activity_log.py           Append-only event store → data/activity_log.json
utils/approval_manager.py       Human-in-the-loop approvals → data/pending_approvals.yaml
utils/run_manager.py            Test run records + schedules → data/test_runs.json
conftest.py                     Generic fixtures — NO product references
products/orangehrm/             OrangeHRM example (web + API + KB)
products/restfulbooker/         Restful Booker example (API + KB)
data/            Runtime data (activity log, approvals, runs, quarantine, KB log)
dashboard/app.py                FastAPI app entry point — registers all routers
dashboard/routers/pages.py      All UI page routes (/, /runs, /agents, /activities, /kb, etc.)
dashboard/routers/runs.py       Test run API + trigger + schedule endpoints; env injection
dashboard/routers/pipeline.py   AI pipeline job trigger + job history
dashboard/routers/config/       Config subpackage: _helpers, _meta, _users, _products, _assignments, _run_config, _runners
dashboard/routers/config/_run_config.py  Per-product run config CRUD — reads/writes data/product_config/<product>.yaml
dashboard/routers/config/_runners.py     Admin CRUD for runner tokens (bcrypt-hashed in config.yaml runner_tokens)
dashboard/routers/runner.py     Remote runner API: /api/runner/claim, /progress, /result (Bearer token auth)
sentinelflux/commands/runner_cmd.py  `sentinelflux runner` daemon — polls claim, runs pytest, posts report
data/test_runs/<product>.json   Per-product sharded run records (200-run rolling window each)
data/test_schedules/<product>.json  Per-product sharded schedules
data/run_product_index.json     O(1) run_id → product mapping (FileLock protected)
data/product_config/<product>.yaml  Per-product run config (envs, browsers, devices, credentials, defaults)
dashboard/routers/config_router.py  Thin re-export shim for backward compat
dashboard/templates/            Jinja2 templates (one per page + partials/ subdir)
dashboard/templates/partials/config_run_config.html  Run config UI partial (4 sections + defaults)
```

---

## Dashboard — How to Add a Page

1. Add route handler to `dashboard/routers/pages.py` (see existing pattern — use `_ctx()` + `_require_auth`)
2. Create `dashboard/templates/<page>.html` extending `base.html`
3. Add nav entry in `base.html` nav_items list (href, label, svg path)
4. Register any new JSON API router in `dashboard/app.py` under `/api` prefix

---

## Conventions (quick ref)

- Test files: `products/<product>/tests/{domain}/test_{feature_name}.py`
- KB per product: `ai/knowledge_base/<product>/`
- Generated docs: `products/<product>/docs/test_cases/{domain}/{feature_name}.md`
- Generated scripts: `products/<product>/tests/{domain}/test_{feature_name}.py`
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
- Do not write to `data/` files without checking for concurrent access — use FileLock (already in place for run_manager, run_product_index, product_config)
- Do not add new agents to `_AGENT_REGISTRY` in `agents.py` without also adding metadata to `dashboard/agent_meta.py`

---

## AI Doc Generation — Anti-Hallucination Rules

1. **Only test KB-listed fields.** If a field is not in the KB context, it does not exist on that form.
2. **Do not use training-data knowledge of the AUT.** KB context is the only truth.
3. **Add Employee ≠ Employee Profile.** OrangeHRM's Add Employee form has 4 fields only: First Name, Last Name, Middle Name, Employee ID.
4. **Use real credentials.** OrangeHRM demo: `Admin / admin123`. Restful Booker: `admin / password123` (API), `admin / password` (web).
5. **Prompt templates enforce this** via STRICT RULES blocks — if modifying prompts, preserve those blocks.
