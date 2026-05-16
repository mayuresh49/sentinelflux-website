# SentinelFlux — Claude Working Guide

## About This Project
Test automation framework (QE + SDE). Solo project — learning vehicle and potential product.
Owner: 13+ yrs QE/SDE experience. Treat as production-grade.

---

## Token Efficiency Rules (Always Active)

- **Batch parallel tool calls** — never serial when independent
- **Subagents for exploration** — spawn `Explore` agent for any search >3 files; keeps main context lean
- **Edit over Write** — prefer `Edit` for existing files; `Write` only for new files
- **Read targeted ranges** — use `offset`+`limit` when you know the section; never read whole large files blind
- **Grep before read** — locate symbols with `grep` before opening files
- **No trailing summaries** — no "here's what I did" at end of responses
- **No docstrings/comment blocks** — one-line comments only, and only when WHY is non-obvious
- **Clarify before large writes** — if requirement is ambiguous, ask one focused question rather than write and rewrite

---

## Skills to Use (Claude Code)

| Skill | When to invoke |
|---|---|
| `/simplify` | After any feature is complete — catch reuse and quality issues |
| `/security-review` | Before any PR that touches auth, config loading, external calls, or data handling |
| `/review` | Before merging any non-trivial branch |
| `/fewer-permission-prompts` | When permission prompts become frequent |
| `/init` | When starting a new sub-project or major module |
| `claude-api` skill | Any file that imports `anthropic` — ensures caching, correct model IDs |

---

## Agent Patterns

```
Explore agent  → file/symbol search >3 queries
general-purpose agent → multi-step research or cross-file analysis
Plan agent → before non-trivial implementation (get alignment first)
```

Run independent agents **in parallel** (single message, multiple Agent blocks).

---

## Code Standards

- No premature abstractions; 3+ real duplications before extracting
- No error handling for impossible states
- No feature flags or backwards-compat shims
- Validate only at system boundaries (user input, external API responses)
- No hypothetical future requirements

---

## Dashboard UI Conventions

### Notifications & Confirmations (Alpine-only — no browser dialogs)
- **Never** use `alert()`, `confirm()`, or `prompt()` — always use the global helpers from `base.html`
- `sfToast(msg, type)` — inline toast (top-right, auto-dismiss 4.5 s)
  - `'warn'` — amber — validation failures, missing input
  - `'error'` — red (default) — API/server errors
  - `'info'` — slate — neutral messages
- `sfConfirm(msg)` → `Promise<boolean>` — use `await` inside `async` functions; resolves `true` on Confirm, `false` on Cancel
  - Always use for destructive actions (delete, overwrite, irreversible ops)

### Labels, Forms, Buttons
- No abbreviations in user-facing labels
- Title Case for buttons and headings
- Descriptive button labels (not just "Submit" or "OK")
- Expand tab names — no single-letter or cryptic abbreviations

---

## Access Control Rules (Dashboard)

Two user roles: **admin** (`admin: True`) and **regular** (product-scoped).

### Backend (FastAPI routes)

| What | Dependency to use |
|---|---|
| Any logged-in user | `require_user` (from `dashboard.routers.auth`) |
| Admin-only action | `_require_admin` (from `dashboard.routers.config._helpers`) |

- Every route that mutates global config (labels, priorities, products, fields, test distribution, generation categories) **must** use `_: dict = Depends(_require_admin)`.
- Every route that returns product-scoped data **must** filter with `user_products(current_user, all_products)` before returning.
- **Never** use `HTTPException(status_code=403, headers={"Location": "/"})` to redirect — the `headers` are silently ignored and the client gets raw JSON `{"detail":"Forbidden"}`. Use `return RedirectResponse("/", status_code=302)` for page routes, or `raise HTTPException(403, detail="Admin access required")` for API routes.
- **Never** use 307 for auth redirects on POST-capable pages — 307 tells the browser to re-POST to the redirect URL (e.g. `/login`), which then fails its own field validation. Always use **303** so the browser converts the redirect to a GET, showing the login page cleanly.

### Template (Jinja2)

- Wrap all admin-only tabs, buttons, and sections with `{% if current_user.admin %}`.
- Default Alpine tab state must reflect role: `x-data="{ tab: '{{ 'admin_tab' if current_user.admin else 'user_tab' }}' }"`.
- Never render destructive action buttons (delete, deactivate) unless the user has the right to perform them server-side.
- The `current_user` dict is available in every page template via `_ctx()` — use `current_user.admin` for guards.

---

## Project Structure

```
ai/               AI engine — agents, clients, skills, pipeline, KB loader
  context/        AI/Claude orientation docs (RESUME, architecture, ADRs, backlog)
  knowledge_base/ KB loader code + increments drop-zone
core/             Framework services (activity log, run manager, approvals, AI factory)
dashboard/        FastAPI web dashboard (routers, templates, static)
data/             Runtime state written by the app (gitignored sensitive files)
products/         Per-product test suites (orangehrm/, restfulbooker/)
  <product>/
    ai/knowledge_base/  Product-specific KB YAMLs
    tests/              Pytest suites
    pages/              Page object models
    docs/test_cases/    AI-generated test case docs
utils/            Test helpers (assertions, step, wait, locator manager, logger)
api/              Generic REST + GraphQL clients
pages/            Framework-level page base classes
tests/            Framework-level tests (unit/, api/, web/, mobile/)
config/           Environment profiles (env_qa.yaml, env_staging.yaml)
scripts/          Shell scripts and ops files (run_pipeline, start-local, Caddyfile)
sentinelflux/     pip-installable CLI (init, run, generate, doctor)
docs/             Public-facing user documentation (mkdocs)
```

---

## Prompt Caching (when using Claude API)

Always structure messages as:
1. System prompt (large, stable) → cache with `cache_control: {type: "ephemeral"}`
2. Knowledge base / context → cache
3. Dynamic user content → no cache

Use `claude-sonnet-4-6` as default; `claude-haiku-4-5-20251001` for high-volume, low-complexity tasks.

---

## Key Files

- `ai/context/RESUME.md` — **read this first** for any new session
- `ai/context/progress/backlog.yaml` — ordered work items
- `ai/knowledge_base/kb_loader.py` — KB ingestion (base + increments)
- `ai/knowledge_base/increments/` — drop feature YAMLs here for AI pipeline
- `ai/clients/mistral_client.py` — LLM client
- `utils/constants.py` — all magic numbers
- `core/ai_factory.py` — AI client creation (use this, never instantiate directly)
- `conftest.py` — pytest fixtures
- `pytest.ini` — test configuration (RP key via RP_API_KEY env var)
- `dashboard/agent_meta.py` — `AGENT_META` dict: responsibility, inputs, outputs per agent

## Agent Registration Checklist

When adding a new agent, touch **all four** of these:
1. `ai/agents/<agent>.py` — implement agent class extending `BaseAgent`
2. `ai/agents/__init__.py` — add import + `__all__` entry
3. `dashboard/routers/agents.py` → `_AGENT_REGISTRY` — add name, description, domain, requires_ai
4. `dashboard/agent_meta.py` → `AGENT_META` — add responsibility, inputs, outputs, config_params

Missing step 4 causes blank detail panels in the `/agents` dashboard.

## Multi-tenancy Architecture

- **Run/schedule storage**: `data/test_runs/<product>.json` + `data/test_schedules/<product>.json` (200-run per-product rolling window)
- **O(1) run lookup**: `data/run_product_index.json` maps `run_id → product` (FileLock on every write)
- **Per-product run config**: `data/product_config/<product>.yaml` (lazy migration from `data/config.yaml` on first read)
- **Remote runner**: Pull-based daemon (`sentinelflux runner`) — polls `GET /api/runner/claim`, POSTs progress/result; Bearer token auth (bcrypt hashes stored in `config.yaml runner_tokens`)
- **Runner token admin**: `dashboard/routers/config/_runners.py` — plain token shown once at creation, only hash persisted

---

## Before Implementing Anything Non-Trivial

1. State approach in 2-3 sentences + main tradeoff
2. Wait for approval
3. Then implement

This saves rework tokens.
