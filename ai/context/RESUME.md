# SentinelFlux — AI Resume Context

> **READ THIS FIRST.** Any AI tool working on this project should read this file before anything else.

Last updated: 2026-05-19 (51)  
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
| VAPT | Working | Full engagement lifecycle: scope → scan → findings → PDF report/certificate, per scan type (web/infra/infra_int/mobile). External infra (black-box) + internal infra (grey-box SSH). SSH auth: key_path (server path) / key_paste (PEM textarea) / password. `core/vapt_manager.py`, `/vapt` dashboard page. |
| Performance Testing | Working | Load/stress/spike/soak profiles, httpx+asyncio engine, VUs/duration/ramp-up/endpoints, p50/p75/p95/p99/throughput/error-rate metrics, threshold checks, PDF report. `core/perf_manager.py`, `/perf` page. |
| Accessibility Testing | Working | Playwright + axe-core CDN injection, WCAG 2.1 A/AA/AAA, per-page violations by impact, multi-scan history, PDF report. `core/a11y_manager.py`, `/a11y` page. |
| API Contract Validation | Working | Loads OpenAPI spec (URL or file), validates status codes + jsonschema per endpoint, skips path-param routes, PDF report. `core/contract_manager.py`, `/contract` page. |
| Visual Regression | Working | Playwright screenshot capture, Pillow pixel diff, configurable threshold %, baseline management, PDF report. `core/visual_manager.py`, `/visual` page. |
| Bug Tracker | Working | Full defect lifecycle: state machine (new→open→in_progress→resolved→closed/wont_fix/deferred), artifact storage (screenshot/video/log/HAR/doc), comments, history, PDF incident report. `core/bug_manager.py`, `/bugs` page. Per-product `bugs_enabled` flag. |
| Storage | Working | SQLite WAL mode (`data/sentinelflux.db` via `core/db.py`). Runs, schedules, approvals, pipeline jobs, activity log, quarantine all in DB. Per-product run config YAML still at `data/product_config/<product>.yaml`. |
| Dashboard | Working | FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind. 20 pages/routers. Start: `uvicorn dashboard.app:app --reload` |
| Runs | Working | Trigger/schedule pytest runs from dashboard, parse JSON reports, auto-analyze failures. `/runs` page |
| CLI | Working | `sentinelflux init/run/generate/doctor` via typer |
| Examples | Working | OrangeHRM (web+api), Restful Booker (13 API tests passing) |
| Docs site | Built | mkdocs-material, `mkdocs serve` to preview |
| Package | Built | `pyproject.toml` + hatchling, `pip install sentinelflux` |

---

## What Was Just Done (2026-05-19)

- **Bugs: auto-attach run artifacts on bug creation; fix transition config fallback** (`dashboard/routers/bugs.py`, `core/bug_manager.py`): `create_bug_from_run` now calls `_attach_run_artifacts` after creating the bug — copies screenshot, console log, API log, trace.zip, and the JSON run report from `reports/artifacts/<safe_nodeid>/` into bug artifact storage. `_get_transitions` fix: `if raw is not None` (was `if raw`) so an explicitly empty `bug_transitions: {}` is honoured rather than falling back to defaults; correctly reflects Config > Bug Workflow settings in the Move To dropdown.

## Previous: UI padding + bug sequential numbers (2026-05-19)

- **UI: Standardise padding/spacing across all dashboard pages** (all non-PDF templates + partials): All right/detail panel containers now use `border-slate-100` + `shadow-sm`. Section card headers uniformly `px-5 py-3`. Tab content areas `p-6`. Config page: removed `max-w-5xl` width constraint and redundant `<h1>` title block; tab spacing tightened. Covers: bugs, vapt, test_plans, a11y, contract, perf, visual, kb, runs, docs, scripts, admin_users, index, quality, insights, config, config_labels, config_priorities partials.
- **Bugs: sequential bug numbers with per-product code** (`core/bug_manager.py`, `core/db.py`, `dashboard/routers/config/_products.py`, `dashboard/templates/partials/config_products.html`, `dashboard/templates/test_plan_report_pdf.html`): Bugs now get a sequential number on creation (`BUG-XX-001` format). Per-product `bug_code` field (up to 6 chars) configurable inline from Config > Products. DB gains `bug_seq` + `bug_number` columns. PDF report shows `bug_number` instead of raw UUID.

## Previous: Bugs: Bug ID display + test plan link (2026-05-19)

- **Bugs: Bug ID display + test plan link in Details panel** (`dashboard/templates/bugs.html`, `dashboard/templates/config.html`, `dashboard/templates/partials/config_labels.html`, `dashboard/templates/partials/config_priorities.html`): Details tab now shows a Bug ID row at the top (mono font, slate styling). Linked info row adds a test plan link (`/test-plans?highlight=`) and updates the empty-state label to mention plan. Config and label/priority panels get tighter `py-3` padding.

## Previous: Activities OOB pagination fix (2026-05-19)

- **Fix: activities OOB pagination triple-render** (`dashboard/templates/partials/activities_rows.html`): OOB pagination blocks in the partial were rendering as raw HTML on full-page loads (browser ejects `<div>` from `<tbody>` into visible page), causing 3 pagination controls to appear. Guarded the entire OOB section with `request.headers.get('HX-Request')` so OOB swaps only fire during HTMX requests; initial page load shows the pagination rendered directly in `activities.html`.

## Previous: Test plan report open bugs (2026-05-19)

- **Test plan report: open bugs section + product-aware closed-state detection** (`core/bug_manager.py`, `dashboard/routers/test_plans.py`, `dashboard/templates/test_plan_report_pdf.html`): `BugManager.list_bugs()` gains a `linked_plan_id` filter. `_DEFAULT_STATUSES` now carries `is_open: True/False` on each entry (new/open/in_progress/deferred = open; resolved/closed/wont_fix = closed). New `BugManager.closed_state_names(product)` method reads `is_open` from the product's configured statuses (custom statuses without the field default to open). Report renderer calls `closed_state_names` instead of a hardcoded set, then passes `open_bugs` to the template. PDF/HTML report includes an "Open Bugs" table (ID, title, priority, severity, state, component, linked TC) between the run history and scope sections. Badge styles added for all bug states.

## Previous: Activities top pagination (2026-05-19)

- **Activities: top pagination added and synced via HTMX OOB** (`dashboard/templates/activities.html`, `dashboard/templates/partials/activities_rows.html`): Added a second pagination control above the table (`id="activities-pagination-top"`). The partial now emits two `hx-swap-oob` blocks — one for each pagination div — so both are updated in sync on every HTMX page/filter change. Initial page load renders both via Jinja2 using plain `href` links; after any HTMX swap both switch to `hx-get` powered links.

## Previous: Bugs custom statuses + workflow (2026-05-19)

- **Bugs: custom statuses per product with configurable workflow** (`core/bug_manager.py`, `dashboard/routers/config/_bugs.py`, `dashboard/routers/pages.py`, `dashboard/templates/config.html`, `dashboard/templates/bugs.html`, `dashboard/templates/partials/config_bug_statuses.html` (new), `dashboard/templates/partials/config_bug_transitions.html`): Per-product `bug_statuses` list in `config.yaml` — each entry has `name`, `label`, `color`. `_get_statuses(product)` in BugManager falls back to 7 hardcoded defaults. Config > Bug Workflow tab split into two sections: Statuses (add/remove custom statuses with name, label, color) + Transitions matrix (renders with product's actual statuses). `bugs.html` filter dropdown server-rendered from product statuses; JS color maps replaced by `_COLOR_PALETTE` data + `_statusMeta()` lookup; `stateLabel()` for display text; transition modal drops hardcoded wont_fix/deferred logic.

## Previous: AppExplorerAgent (2026-05-19)

- **AppExplorerAgent — eliminate test generation hallucination** (`ai/skills/app_exploration.py` (new), `ai/agents/app_explorer_agent.py` (new), `sentinelflux/commands/explore_cmd.py` (new), `ai/prompts/prompt_templates.py`, `ai/skills/test_case_doc_kb.py`, `ai/skills/test_script_gen.py`, `ai/agents/doc_gen_agent.py`, `ai/agents/script_gen_agent.py`, `ai/pipeline/orchestrator.py`, `ai/agents/__init__.py`, `dashboard/routers/agents.py`, `dashboard/agent_meta.py`, `sentinelflux/cli.py`): New pre-generation exploration phase. `AppExplorationSkill` uses Playwright to crawl the running application — extracts form fields with DOM-verified CSS selectors ranked by stability (data-testid > id > name > aria-label > placeholder), buttons, navigation links, and real validation error messages (by submitting empty forms). Outputs: (1) `LIVE APPLICATION EXPLORATION CONTEXT` block injected into both doc-gen and script-gen prompts, grounding the LLM to verified elements only; (2) `locators/web/<page>.json` with primary + alternative selectors; (3) `pages/web/<page>.py` page object skeleton with real selectors (never overwrites existing). Pipeline: `--explore --base-url http://... --explore-pages /path1,/path2 --login-url /auth/login` runs exploration as Phase 0 before doc/script gen. Prompt rules updated: LLM told to use ONLY fields/selectors from exploration context; script rule added that page.fill/click must use DOM-verified selectors. `sentinelflux explore` CLI command for standalone exploration without full pipeline. Registered in all 4 agent checklist locations.

## Previous: Bugs configurable state transitions (2026-05-19)

- **Bugs: configurable per-product state transitions** (`core/bug_manager.py`, `dashboard/routers/bugs.py`, `dashboard/routers/config/_bugs.py` (new), `dashboard/routers/config/__init__.py`, `dashboard/templates/config.html`, `dashboard/templates/partials/config_bug_transitions.html` (new), `dashboard/templates/bugs.html`): `BugManager` now reads `bug_transitions` from `config.yaml` per product, falling back to hardcoded defaults. New `GET /api/bugs/{id}/transitions` endpoint returns product-aware allowed transitions. `loadTransitions()` in `bugs.html` calls the endpoint instead of a hardcoded JS map. Config page gains a "Bug Workflow" admin tab with a checkbox matrix (from-state rows × to-state columns) to configure allowed transitions per product, with Save and Reset to Defaults actions.

## Previous: Bugs UI improvements (2026-05-19)

- **Bugs: transition dropdown + Update Bug button** (`dashboard/templates/bugs.html`): Replaced flat transition button row with a compact `<select>` dropdown ("Move to…") that fires the existing transition modal. Removed `@blur` auto-save from all textarea/text-input fields in the Details tab; added explicit "Update Bug" button that PATCHes all text fields in one call. Select dropdowns (assignee, priority, severity, component, type) still auto-save on `@change`.

## Previous: Runs analyzed flag fix (2026-05-19)

- **Runs: fix analyzed flag never flipping** (`dashboard/routers/runs.py`): `_run_post_suite` called `patch_run` with `post_suite_summary={}` — not a DB column — causing the entire call to fail silently (same unknown-column pattern as `progress_total`). `result_analyzer` was running successfully but `analyzed` stayed `0`. Dropped the non-existent field; `analyzed=True` and `failure_categories` now commit correctly. Manually recovered `run_9d157fc3`.

## Previous: VAPT SSH multi-auth (2026-05-19)

- **VAPT SSH multi-auth: key path, key paste, password** (`core/vapt_manager.py`, `dashboard/routers/vapt.py`, `products/reportportal/tests/vapt_infra_int/conftest.py`, `core/vapt_test_generator.py`, `dashboard/templates/vapt.html`): Scope gains `ssh_auth_method` (key_path | key_paste | password), `ssh_key_content`, `ssh_password`. UI: radio selector switches between server key path input, PEM textarea (paste), and password field. Runner injects the matching env var (`VAPT_SSH_KEY_PATH` / `VAPT_SSH_KEY_CONTENT` / `VAPT_SSH_PASSWORD`) plus `VAPT_SSH_AUTH_METHOD`. Conftest handles all three: key_paste writes content to a `tempfile.mkstemp` PEM file (chmod 600), connects, then deletes the temp file immediately. Pre-flight check validates the correct field per method. Generator template updated to match.

## Previous: Runs DB columns + stuck-run fix (2026-05-19)

- **Runs: missing DB columns + stuck-run fix** (`core/db.py`, `dashboard/routers/runs.py`): `progress_total`, `progress_done`, `summary_error` were missing from `test_runs` schema — `patch_run` calls in `_execute_run` silently threw `OperationalError`, leaving runs stuck in `running` and "Collecting tests…" never advancing. Added columns to `CREATE TABLE` (fresh installs) + `ALTER TABLE` migrations (existing DBs). `apply_schema` now swallows `duplicate column name` so restarts are idempotent. Manually recovered `run_26a4ee07`. Root cause of `exitcode: 3` (pytest INTERRUPTED) is uvicorn `--reload` sending SIGTERM to child processes — open issue.

## Previous: VAPT scope SSH fix (2026-05-19)

- **VAPT scope: SSH credentials section always visible** (`dashboard/templates/vapt.html`): SSH credentials section was gated on `scopeForm.test_types.includes('infra_int')` but `infra_int` is not in the Test Domains checkbox list (`['web','api','mobile']`), so it was permanently hidden. Removed the `x-show` guard — section now always visible, matching the pattern of Infrastructure Targets and Mobile App Path fields.

## Previous: infra_int pre-flight check (2026-05-19)

- **VAPT infra_int: pre-flight SSH credentials check** (`dashboard/routers/vapt.py`): Without SSH credentials in scope all 7 tests silently skip and the scan lands as "completed 0/0/7" with no explanation. Added a pre-flight check in `_execute_vapt_scan` that detects missing `ssh_username`/`ssh_key_path` before spawning the subprocess, fails the scan immediately with a human-readable `summary_error` visible in the scan card: "SSH credentials not configured — set SSH Username and SSH Key Path in the Scope tab before running an Internal Infrastructure scan".

## Previous: VAPT findings scan-type filter (2026-05-19)

- **VAPT findings tab: scan-type filter fix** (`dashboard/templates/vapt.html`): `filteredFindings`, `uniqueOwaspRefs`, `hasOpenFindings`, and the report-tab severity summary (Critical/High/Medium/Low open counts) were all reading from the full `findings` array regardless of `scanTypeSel`. Promoted the existing `scanTypeFindings()` method to a reactive Alpine getter scoped to the current scan type's scan IDs; wired into all four consumers. Empty-state "No findings" message and N-of-M counter also corrected to use scan-type scope.

## Previous: V-01 VAPT internal infra SSH scan (2026-05-19)

- **VAPT: Infrastructure (Internal) grey-box SSH scan — V-01** (`products/reportportal/tests/vapt_infra_int/`, `core/vapt_test_generator.py`, `dashboard/routers/vapt.py`, `core/vapt_manager.py`, `dashboard/templates/vapt.html`, `requirements.txt`): New `infra_int` scan type alongside existing external `infra`. Test suite has 7 SSH hardening checks (PermitRootLogin, PasswordAuthentication, MaxAuthTries, AllowUsers/AllowGroups, SUID/SGID files, sensitive file permissions, audit log). paramiko session fixture yields factory callable `ssh_client(host)` to avoid scope mismatch with function-parametrized `vapt_host`. `pytest_runtest_setup` hook fast-skips all SSH tests when env vars missing. Scope model adds `ssh_username` + `ssh_key_path` (key-path only). Runner injects `VAPT_SSH_USER`/`VAPT_SSH_KEY_PATH` env vars. Generator templates added. Dashboard: "Internal Infra" scan type selector button, SSH credentials section in scope tab (shown only when `infra_int` in test_types, finalize-lockable). `paramiko>=3.0` added to requirements.

## Previous: Runs UX fixes (2026-05-19)

- **Runs UX: errored status + Re-run + queued indicator** (`dashboard/templates/runs.html`, `dashboard/routers/pages.py`): Diagnosed three runs stuck as errored — root cause was server restart killing FastAPI BackgroundTasks mid-execution (trigger: plan). Fixed three UX gaps: (1) `errored` runs now show orange badge/dot and a Re-run button (previously only `completed`/`failed` had one); (2) `queued` run cards now show a pulsing "Waiting to start…" inline indicator (previously only `running` had a progress row); (3) `any_running` banner/auto-refresh scoped to current page runs instead of full filtered list (was showing banner even when in-progress run was on another page). Also added `errored` option to the status filter dropdown.

## Previous: Bugs module (2026-05-19)

- **Bugs module** (`core/bug_manager.py`, `core/db.py`, `dashboard/routers/bugs.py`, `dashboard/templates/bugs.html`, `dashboard/templates/bug_report_pdf.html`, `utils/constants.py`, `dashboard/app.py`, `dashboard/routers/pages.py`, `dashboard/templates/base.html`, `dashboard/routers/config/_products.py`, `dashboard/templates/partials/config_products.html`, `dashboard/templates/failures.html`, `ai/context/progress/backlog.yaml`): Full defect tracking module. Four new SQLite tables: `bugs` (full metadata — product, title, description, priority P0-P3, severity blocker-trivial, state, bug_type, component, environment, build_version, reporter, assignee, steps/expected/actual/root_cause/fix_notes, tags, linked_tc_id, linked_run_id, linked_plan_id), `bug_state_history` (every transition recorded), `bug_comments`, `bug_artifacts` (type/mime/size/storage_path). `BugManager`: create/get/list/patch/delete, `transition()` with enforced state machine (new→open→in_progress→resolved→closed, plus deferred/wont_fix paths with reopen support), get_history, add/list comments, add/list/delete artifacts, counts_by_state. 14 REST endpoints under `/api/bugs`: list, create, get, patch, delete (admin), transition with comment, history, comments, artifact upload (multipart, 100 MB cap, auto-inferred type), artifact download/serve, artifact delete, HTML/PDF incident report, `POST /api/bugs/from-run/{run_id}` pre-fills from test failure. `bugs.html`: split-panel UI — left list with state/priority filters + state count chips; right detail with 4 tabs: Details (inline editing of all fields via blur-patch), Artifacts (drag-and-drop upload, screenshot thumbnail grid + lightbox, inline video player, download table for logs/HAR/docs), History (timeline), Comments (threaded + add form). State transition modal with required comment for wont_fix/deferred. Create Bug modal. Export PDF button → WeasyPrint incident report. `bugs_enabled` product flag added — Config → Products toggle + sidebar nav item. Failures page gets "File Bug" button per row that calls `from-run` endpoint and opens `/bugs?highlight=<id>` in new tab. Backlog item P6-01 added for future S3 artifact storage migration.

## Previous: Data: VAPT findings test data (2026-05-19)

- **Data: VAPT findings test data** (`data/vapt_findings/reportportal/eng-25d78fab7eae.json`): Morphed the Q2 2026 Security Assessment engagement with 5 realistic findings to exercise the full findings flow in the dashboard UI. F-001: Sensitive Ports Exposed — Redis 6379/Mongo 27017 (Critical, open, infra). F-002: No Rate Limiting on Login (High, still_open, web). F-003: SSH on Default Port 22 (Medium, accepted_risk, infra). F-004: CORS Wildcard on Authenticated Endpoints (Medium, open, web). F-005: Server Version Disclosure (Low, fixed, infra). Infra scan updated to 3 failed / 5 passed; web scan to 2 failed / 28 passed. Three infra test_log entries flipped from confirmed_secure → finding. All findings include full description, evidence, and remediation text.

## Previous: VAPT infra scan bug fixes + multi-target (2026-05-19)

- **VAPT infra scan: bug fixes + multi-target** (`products/reportportal/tests/vapt_infra/`, `core/vapt_test_generator.py`, `ai/context/progress/backlog.yaml`): Three bugs fixed across generated test files and generator templates. (1) `pytest.xfail` → `pytest.fail` for `test_INFRA_sensitive_service_ports_not_exposed` and `test_INFRA_ssh_port_not_on_default` — exposed ports and SSH-on-22 are real security findings, not "expected" failures. (2) Zone transfer test now sends a raw DNS-over-TCP AXFR packet (struct + socket, no new deps) and reads RCODE + ancount from response — only fails if transfer actually succeeds; a locked-down nameserver passes even with port 53 open. (3) `conftest.py` replaced `vapt_infra_targets` + single-host `vapt_host` session fixtures with `_resolve_targets()` + `pytest_generate_tests` — all `vapt_host`-dependent tests now run once per IP when multiple targets are entered in the UI. `vapt_domain` downgraded to function scope; `vapt_https_port` stays session-scoped. Backlog item `V-01` added for future authenticated SSH (grey-box) scanning.

## Previous: Agents: filter product-domain agents from public registry (2026-05-19)

- **Agents: filter product-domain agents from public registry** (`dashboard/routers/agents.py`, `dashboard/routers/pages.py`): Added `_PUBLIC_REGISTRY` (filters `_AGENT_REGISTRY` by `domain != "product"`) so internal product-review agents (QA Architect, Dev Architect, etc.) are not exposed via the public `/api/agents` list/get endpoints or counted on the home dashboard. Home page and agents page both import `_PUBLIC_REGISTRY`.

## Previous: Product filter retention fix (2026-05-19)

- **Fix: product filter retention across all nav pages; suppress on Insights** (`dashboard/templates/base.html`, `dashboard/templates/insights.html`): VAPT, Performance, Accessibility, API Contract, and Visual Regression sidebar nav links now carry `?product=<value>` when a product is selected — previously these were hardcoded hrefs so the selected product was lost on navigation. The main nav_items loop already did this correctly; the five special-access pages were missed. Added empty `{% block header_filter %}` override to `insights.html` to suppress the global product filter on the Product Insights page (consistent with `admin_users.html` pattern).

## Previous: Visual Regression compare modal + empty-state fix (2026-05-19)

- **Visual Regression: baseline vs current screenshot compare modal** (`dashboard/routers/visual.py`, `dashboard/templates/visual.html`): New `GET /api/visual/engagement/{eng_id}/screenshot` endpoint serves stored PNG files from disk — `type=baseline` reads from `eng.baselines[page_path]`, `type=scan&scan_id=...` reads from the scan's `pages_results`. Template adds a full-screen lightbox modal (two-column: Baseline | Current) with diff % badge in header; each per-page row in a completed comparison scan gets a "View" button that opens the modal. Images load via session-cookie auth.
- **Empty-state card alignment fix** (`a11y.html`, `contract.html`, `perf.html`, `visual.html`): "No … suites yet" messages were bare `div`s with `py-8`; now match the sibling "Select a product" card style (`bg-slate-50 border border-slate-200 rounded-xl p-6`).

## Previous: Startup orphan run reaper (2026-05-19)

- **Startup: reap orphaned queued/running runs** (`dashboard/app.py`): `_reap_orphaned_runs()` added to the startup event — marks any run still in `queued` or `running` state as `errored` with `finished_at = now`. Fixes runs that were submitted as FastAPI background tasks getting permanently stuck after a server restart (tasks are lost on restart, so those runs would never complete). Users can then retrigger from the Test Plans UI.

## Previous: Insights CTO agent + Strategic Roadmap (2026-05-19)

- **Insights: CTO agent + Strategic Roadmap + deduplication fix** (`ai/agents/cto_agent.py`, `core/roadmap_manager.py`, `core/db.py`, `core/insights_manager.py`, `dashboard/routers/insights.py`, `dashboard/templates/insights.html`, `ai/agents/__init__.py`, `dashboard/routers/agents.py`, `dashboard/agent_meta.py`): New `CTOAgent` reads all `active` insights from the 4 expert agents, presents them numbered to the LLM, and selects the top 4–5 most strategically important with a per-item rationale. New `roadmap_items` SQLite table: `source_insight_id UNIQUE` (prevents duplicates across CTO runs), `agent_type`, title/description/recommendation copied from source, `cto_rationale`, `status (planned|done)`, `promoted_at`, `done_at`. `RoadmapManager`: create (INSERT OR IGNORE), list, update_status (planned→done), delete + restore source insight to active. New `/api/insights/roadmap` CRUD + `/roadmap/run` background trigger + CTO run state in `_run_state`. Strategic Roadmap panel at top of `/insights` page (above persona tabs): gradient header with CTO Review button + last-run timestamp; planned item cards showing source persona badge (color-coded), priority+category pills, description, Recommendation block, CTO Rationale block (indigo background); Mark Done + Remove actions; collapsible Completed section with strikethrough + done timestamp. Removing an item restores source insight to `active`. Deduplication fix: `save_insights()` now deletes existing `active` rows for that `agent_type` before inserting fresh ones — re-running an expert agent replaces its active insights rather than accumulating duplicates. `planned`/`punted`/`discarded` rows preserved (user decisions respected). CTO only reads `active` insights so already-promoted (`planned`) and done-roadmap-source (`planned`) items are naturally excluded from CTO selection.

## Previous: Fix runs latest-first + test plan → run navigation (2026-05-19)

- **Fix: runs show latest first + test plan → run navigation** (`dashboard/routers/pages.py`, `dashboard/templates/runs.html`, `dashboard/templates/test_plans.html`): `reversed(rm.all_runs())` in `runs_page` and `failures_page` was flipping `all_runs()`'s DESC order to ASC (oldest first) — removed both `reversed()` calls. Added `?highlight=<run_id>` param to `runs_page`: auto-calculates the page the run lives on, renders it, and scrolls to the card via JS `scrollIntoView`. Run cards now have `id="run-{{ run.id }}"` anchors with an indigo ring when highlighted. Run IDs in Test Plans → Execution → Automated Run History are now clickable links opening `/runs?product=...&highlight=<run_id>#run-<run_id>` in a new tab. Client-side sort changed from `localeCompare` to direct `>` string comparison (locale-safe for ISO dates).

## Previous: Insights run error surfacing (2026-05-19)

- **Insights: run error surfacing** (`dashboard/routers/insights.py`, `dashboard/templates/insights.html`): `_run_agent_task` previously swallowed all exceptions silently. Now wraps the full run in try/except, sets in-memory `_run_state[agent_type]` to `{state: error, error: msg}` on any failure (no client, no insights parsed, exception). `/api/insights/runs` now returns `state` dict alongside `runs`. UI polling detects `state === 'error'` and shows error toast immediately instead of waiting 40 polls. Error banner below run-control bar shows the last failure message persistently. Added already-running guard on trigger endpoint.

## Previous: Product Insights module (2026-05-19)

- **Product Insights module** (`ai/agents/product_review_agents.py`, `core/insights_manager.py`, `dashboard/routers/insights.py`, `dashboard/templates/insights.html`): Master-admin-only `/insights` page showing AI-driven expert review from 4 perspectives — Product Manager, Dev Architect, QA Architect, UX Architect. Each agent reads relevant codebase context (RESUME.md, db.py, conftest.py, base.html, backlog.yaml) and calls the LLM to produce 5–8 structured insights (title, description, recommendation, category, priority). Insights stored in new `product_insights` SQLite table. UI: persona tab selector with active-count badges, run-control bar with last-run timestamp, status filter chips (active/planned/punted/discarded), card grid with expandable descriptions, inline status transitions, polling-based run completion detection. All 4 agents registered in `__init__.py`, `_AGENT_REGISTRY`, and `AGENT_META`. Nav item gated by `master_admin` flag in `base.html`.

## Previous: Test Plans report export + latest runs on top (2026-05-18)

- **Test Plans: report export + latest runs on top** (`dashboard/routers/test_plans.py`, `dashboard/templates/test_plan_report_pdf.html`, `dashboard/templates/test_plans.html`): New `GET /{plan_id}/report?format=pdf|html` endpoint renders a full execution report — cover page with plan metadata, milestones table, progress metric cards with stacked colour bar, TC execution status table grouped by domain (with colour-coded status badges), automated run history table, scope summary. WeasyPrint PDF via `_to_pdf()` helper; HTML preview served directly. "Preview Report" (new tab) and "Export PDF" (download) buttons added to the Execution tab. Linked runs now sorted latest-first in both API (`sorted(...reverse=True)`) and client (`localeCompare` sort after fetch).

## Previous: Nav access flags fix (2026-05-18)

- **Fix: nav access flags missing from /config page** (`dashboard/routers/config/__init__.py`): `config_page` was building its own context dict and only included `vapt_access`; the 4 new module flags (`perf_access`, `a11y_access`, `contract_access`, `visual_access`) were undefined (falsy) there, causing those nav items to disappear when navigating to /config. Replaced duplicated `vapt_access` inline logic with a shared `_has_flag(flag)` helper that covers all 5 flags consistently. Nav items now show/hide correctly on every page.

## Previous: Test Plans empty-modules UX (2026-05-18)

- **Test Plans: empty-modules UX fix** (`dashboard/templates/test_plans.html`): Empty state for Scope tab now shows the expected path (`products/{product}/tests/{domain}/`) and the file pattern (`test_*.py`) so users know where to add scripts. API failures in `loadAvailableModules` now trigger `sfToast` instead of silently leaving the list blank. Added `scopeLoadError` state flag to distinguish "API call failed" from "legitimately no test scripts". `scopeLoadError` is reset on plan change and at start of each load.

## Previous: Config feature flag toggles (2026-05-18)

- **Config: feature flag toggles for new modules** (`dashboard/routers/config/_products.py`, `dashboard/templates/partials/config_products.html`): Added On/Off toggle buttons for Performance Testing, Accessibility Testing, API Contract Validation, and Visual Regression in Configurations → Products, matching the VAPT toggle pattern. Backend: shared `_set_flag()` helper + 4 POST endpoints (`/ui/config/products/set-perf|a11y|contract|visual`) that write `perf_enabled`/`a11y_enabled`/`contract_enabled`/`visual_enabled` to `config.yaml`. Template: coloured pill buttons (blue/sky/emerald/pink) per module, active state shows filled colour, inactive shows greyed-out "Off" label.

## Previous: 4 new testing modules (2026-05-18)

- **4 new testing modules: Performance, Accessibility, API Contract, Visual Regression** (`core/perf_manager.py`, `core/a11y_manager.py`, `core/contract_manager.py`, `core/visual_manager.py`, `dashboard/routers/perf.py`, `dashboard/routers/a11y.py`, `dashboard/routers/contract.py`, `dashboard/routers/visual.py`, 8 HTML templates, `dashboard/app.py`, `dashboard/routers/pages.py`, `dashboard/templates/base.html`, `requirements.txt`): All 4 modules follow the VAPT pattern — FileLock JSON storage under `data/{module}/{product}/`, FastAPI router, Alpine.js dashboard with modals + polling, WeasyPrint PDF report. Feature flags `perf_enabled`/`a11y_enabled`/`contract_enabled`/`visual_enabled` in product config. Nav items in sidebar, access guards via `_module_access()` in pages.py. (1) **Performance**: engagement holds profiles (load/stress/spike/soak, VUs, duration, ramp-up, endpoints, thresholds) + runs; `_run_load_test()` spawns N async httpx workers with ramp-up stagger, collects p50/p75/p95/p99, throughput, error rate, per-threshold pass/fail. (2) **Accessibility**: engagement holds base_url, pages, WCAG level; scan opens each page in headless Playwright, injects axe-core from CDN, calls `axe.run()`, collects violations by impact. (3) **API Contract**: loads OpenAPI spec from URL or file (YAML/JSON), iterates paths+methods, skips required path-param routes, makes real requests, validates actual status vs expected and response body vs jsonschema. (4) **Visual Regression**: `capture-baseline` scan takes Playwright full-page screenshots per page and stores to `data/visual/{product}/screenshots/`; comparison scan diffs current screenshot against stored baseline using Pillow `ImageChops.difference`, pixel diff % vs configurable threshold. `Pillow>=10.0.0` added to requirements.txt.

## Previous: Test Plan feature + filter fix (2026-05-18)

- **Test Plan feature + filter fix** (`core/db.py`, `core/test_plan_manager.py`, `dashboard/routers/test_plans.py`, `dashboard/templates/test_plans.html`, `dashboard/routers/pages.py`, `dashboard/templates/base.html`, `dashboard/app.py`, `CLAUDE.md`): Full test plan lifecycle for product release readiness. Four new SQLite tables: `test_plans` (metadata: name, product, owner, dates, milestones, risks, exit/pass criteria, status), `test_plan_scope` (module-level in-scope items per domain with per-TC exclusion list), `test_plan_tc_status` (per-TC execution status: not_run/pass/fail/blocked, synced from TC docs on scope save), `test_plan_run_links` (automated runs triggered from a plan). `TestPlanManager` (SQLite, same pattern as RunManager): CRUD, `set_scope()` (replace + re-sync), `upsert_tc_statuses()` (ON CONFLICT preserves existing status), `remove_tc_statuses_not_in_scope()`, `update_tc_status()`, `link_run()`, `get_progress()` (counters + pass_rate). API router at `/api/test-plans/` (12 endpoints): plan CRUD, scope GET/PUT, available-modules, module-tcs (per-module TC list from docs), tc-status GET/PATCH, execute (triggers runs per scope item via `_execute_run` background task + links them), progress, runs. Dashboard page at `/test-plans`: left panel plan list with inline progress bar; right panel 3-tab detail — Overview (metadata + inline milestone/risk editors), Scope (domain tabs → module checkboxes → expandable TC exclusion list loaded from docs), Execution (progress counters + bar, TC table with inline status dropdowns + notes, "Run Automated Tests" button, linked runs table). TC sync: scope save calls `_tcs_for_module()` which strips `test_` prefix from module stem to find doc file, parses TC index via `_parse_tc_index()`, upserts in-scope TCs, removes de-scoped ones. Filter fix: removed duplicate product `<select>` from page content (global filter bar in `base.html` owns this via `?product=` + `applyProductFilter()`); rule added to `CLAUDE.md` § Dashboard UI Conventions → Global Product Filter.

## Previous: VAPT APK/IPA static analysis + mobile/infra scope + scan delete + per-type reports/certs (2026-05-18)

- **VAPT: APK/IPA static analysis + mobile/infra scope inputs + scan delete + per-type reports/certs** (`core/vapt_manager.py`, `core/vapt_test_generator.py`, `dashboard/routers/vapt.py`, `dashboard/templates/vapt.html`, `vapt_certificate_pdf.html`, `vapt_report_pdf.html`, `requirements.txt`): (1) Per-scan-type reports and certificates — `check_certifiable`/`issue_certificate` filter findings by scan type; certs stored in `eng["certificates"][scan_type]` with web backward compat; download endpoints accept `scan_type` query param and filter report/cert rendering accordingly; scan type toggle moved above sub-tabs as global context. (2) Delete scan history — `VaptManager.delete_scan()` + `DELETE /vapt/engagement/{eng_id}/scan/{scan_id}`; admin Delete button on scan cards (blocked while running). (3) Infra targets — `scope.infra_targets[]` field, textarea in scope form (one IP/hostname per line), passed as `VAPT_INFRA_TARGETS` env var to infra scan subprocess; infra conftest `vapt_infra_targets` fixture reads env var, `vapt_host` uses first target. (4) Mobile app path — `scope.mobile_app_path` field, text input in scope form, passed as `VAPT_MOBILE_APP_PATH`; mobile conftest `vapt_mobile_app_path` fixture returns Path or None. (5) APK static analysis — 2 new generated test files: `test_vapt_mobile_apk_manifest.py` (androguard; checks debuggable, allowBackup, usesCleartextTraffic, exported components, taskAffinity) and `test_vapt_mobile_apk_static.py` (pure Python: private key files, hardcoded secrets in assets, http:// URLs, weak crypto in DEX; androguard: DEX string pool secrets, cert pinning, Log calls near sensitive literals). All APK tests skip gracefully without APK or androguard. `androguard>=3.3.5` added to requirements.txt.

## Previous: Docs TC create/delete UX fixes (2026-05-18)

- **Docs TC create/delete UX fixes** (`dashboard/routers/partials.py`, `dashboard/templates/docs.html`, `dashboard/templates/partials/doc_tc_view.html`): (1) Success toast: `tc_create` redirect now appends `?created=TC_ID`; `docsPage.init()` reads the param, fires `sfToast("Test case X created successfully.", 'info')`, then removes the param via `history.replaceState` so a page refresh doesn't re-fire it. (2) Delete confirm: replaced inline Alpine Yes/No confirm div with `sfConfirm` modal — Delete button calls `await sfConfirm(...)` and only submits the hidden form via `htmx.trigger($refs.deleteForm, 'submit')` on confirmation. (3) Alpine timing fix: `tcCreateForm` function moved from partial `<script>` tag to `docs.html` `{% block scripts %}` so it's defined at page load before any HTMX swap, eliminating the race where Alpine's MutationObserver fired before HTMX re-executed the inline script.

## Previous: Coverage gap pipeline + pipeline hardening (2026-05-18)

- **Coverage gap pipeline + pipeline hardening** (`ai/pipeline/orchestrator.py`, `ai/skills/test_script_gen.py`, `ai/prompts/prompt_templates.py`, 4 new docs, 4 updated scripts): Ran CoverageGapAgent for orangehrm across all domains — found 96 untested KB scenarios (43 api, 12 web, 41 mobile), all logged to activity. Ran full pipeline (DocGen → DocReview → ScriptGen → ScriptReview) for 4 undocumented scripts, bringing doc coverage from 67% → 100%: `security_api.md` (OH-API-029..039), `security_web.md` (OH-WEB-083..125), `leave.md` (OH-WEB-124..128), `login_mobile.md` (OH-MOB-017..026). Three systemic pipeline bugs fixed: (1) normalizer regex `(?!not_automatable)` → `(?!not_automat)` to also skip `not_automated` rows; (2) `max_tokens` 3000→5000 in script gen to prevent truncation on 10+ TC docs; (3) mobile convention CRITICAL block — model was passing `base_url` to mobile POM constructors which take `(driver, platform)` only. Hardcoded credentials eliminated: api convention rewritten with `{product}_client` / `{product}_api_base_url` / `{product}_credentials` patterns + two new NEVER rules in prompt template. `test_security_api.py` rewritten (was using wrong `rest_client` + `authenticate()` helper with hardcoded creds). `test_login_mobile.py` rewritten with `orangehrm_credentials` / `orangehrm_ess_credentials` fixtures and OH-MOB TC IDs. Added `orangehrm_ess_credentials` fixture to `products/orangehrm/conftest.py` and `ess_username`/`ess_password` to `env_qa.yaml`.

## Previous: Docs: manual test case creation (2026-05-18)

- **Docs: manual test case creation** (`dashboard/routers/partials.py`, `dashboard/templates/docs.html`, `dashboard/templates/partials/doc_tc_create.html`): Added "Add Test Case" button to the Docs page header. Clicking it loads a structured form into the right-panel viewer (via HTMX). TC ID is auto-generated from the highest existing ID in the selected product+domain (scans all feature .md files at form load). Product abbreviation is derived from existing TC IDs. Feature/module is a dropdown of existing modules for the selected product+domain with an "Add new module" fallback text input. Script is restricted to actual `test_*.py` files on disk; selecting one that's already referenced in any TC shows an amber inline warning (allowed but flagged). Owner is a dropdown from `config.yaml` users. On save: appends a new index row (matching existing column count) and detail block to an existing .md, or creates the file from scratch with full header. Duplicate TC ID is rejected. On success, `HX-Redirect` to `/docs?product=X` so the left panel refreshes. Alpine `| safe` bug fixed: JSON was placed raw into a double-quoted HTML attribute, breaking HTML parsing — Jinja2 auto-escaping now handles `"` → `&#34;` correctly. Script `<script>` block moved to top of partial so it executes before Alpine's MutationObserver fires.

## Previous: VAPT report PDF fix + historical test log backfill (2026-05-18)

- **VAPT report: PDF fix + historical test log backfill** (`dashboard/routers/vapt.py`, `dashboard/templates/vapt_report_pdf.html`): WeasyPrint 68.1 installed (was not present, causing 500 on PDF download). For scans that predate `test_log` persistence, added `_infer_test_log_from_files(product, scan_id, findings)` — walks `products/{product}/tests/vapt/test_*.py`, parses `def test_` declarations, extracts the OWASP ref from the embedded prefix (e.g. `test_A01_...`) using a `_`-delimited regex (word-boundary `\b` fails inside underscore-joined identifiers), falls back to keyword inference only if no prefix found. `_make_title()` updated to strip the leading OWASP prefix from human-readable titles. `_render_report_html` calls the fallback for any completed scan missing `test_log`. Template adds a disclaimer footnote on inferred scans. Section 6 Scan History gains Skipped and Duration columns.

## Previous: VAPT report per-test execution detail section (2026-05-18)

- **VAPT report: per-test execution detail section** (`dashboard/routers/vapt.py`, `dashboard/templates/vapt_report_pdf.html`): Report previously showed only failed tests (findings) and aggregate scan counts — passed/skipped tests were thrown away after scan. Fix: `_execute_vapt_scan` now stores a slim `test_log` list (test_id, title, owasp_ref, owasp_category, severity, status) on each completed scan record before deleting the raw pytest JSON. `_render_report_html` collects `test_log` from all completed scans and passes `scan_test_logs` to the template. Added section 7 "Test Execution Details" to `vapt_report_pdf.html` — a per-scan table of all 31 tests showing OWASP ref, severity, and ✓ Secure / ✗ Finding / — Skipped result. Section 6 Scan History gains Skipped and Duration columns.

## Previous: VAPT bug fixes (2026-05-18)

- **VAPT bug fixes** (`dashboard/routers/config/__init__.py`, `dashboard/routers/vapt.py`, `dashboard/templates/vapt.html`): Three bugs fixed. (1) VAPT nav link invisible on config page — `config_page()` built its own context dict without `vapt_access`; `base.html` gated the nav link on that key so it was always hidden. Added inline admin-or-vapt-enabled-product check directly in the config route. (2) Scope save data lost on re-select — `saveScope()` updated `this.selectedEng` but not the `this.engagements` array; clicking another engagement then back re-populated the form from the stale list entry. Fixed with `engagements.splice(idx, 1, updated)` after each successful PUT. Same fix applied to `updateFinding`. (3) Report generation blocked with zero findings — backend raised 400 if `eng.findings` was empty; UI hid the report form behind a findings-count gate. Both guards removed; reports generate regardless of findings count.

## Previous: TC doc section spacing (2026-05-18)

- **TC doc section spacing** (`ai/prompts/prompt_templates.py`, `ai/pipeline/orchestrator.py`, 23 docs): LLM was generating `**Pre-conditions:**`, `**Steps:**` etc. with no blank line before them, making sections run together. Fixed in three places: (1) prompt templates — added blank lines between every section in the web and API format examples; (2) `_clean_doc()` in orchestrator — added `_TC_HEADERS` regex normalizer that ensures a blank line before every `**<section>...**` header on every pipeline run (also strips inline ``` fences some models inject around TC blocks); (3) all 23 existing docs reformatted in one pass. Key bug: pattern must be `\*\*<keyword>[^*]*\*\*` not `\*\*<keyword>\*\*[:\s]` because the colon sits inside the closing `**`, not after it.

## Previous: Quality metrics VAPT exclusion + doc-gen signal (2026-05-18)

- **Quality metrics: VAPT exclusion + low-coverage doc-gen signal** (`dashboard/routers/quality.py`, `dashboard/templates/quality.html`): VAPT tests (`products/*/tests/vapt/`) excluded from all quality metrics (script count, test function count, doc coverage denominator) — they are template-generated with no KB docs. Added `_EXCLUDED_DOMAINS = {"vapt"}` constant applied in `_script_features()`, `_scripts_by_domain()`, `_count_test_functions()`. Added `_undocumented_with_domain(product)` returning `[{feature, domain}]` for scripts missing test case docs. Health signals section now shows a per-product low-coverage card when `doc_coverage < 70%` with collapsible list of undocumented scripts; each script has a "Generate Doc" button that POSTs to `/api/pipeline/trigger` with `skip_script=true` (generates doc only, preserves existing script), button shows pending/queued/error state via Alpine + `sfToast`.

## Previous: VAPT exhaustive test suite + template viewer (2026-05-18)

- **VAPT exhaustive test suite + template viewer** (`core/vapt_test_generator.py`, `dashboard/routers/vapt.py`, `vapt.html`): Expanded from 5 to 9 test files (31 tests) covering full OWASP A01–A10. New files: `test_vapt_injection.py` (A03 — SQL, XSS, path traversal, SSTI), `test_vapt_session.py` (A07 — HttpOnly/Secure/SameSite cookie flags, session not in URL), `test_vapt_web.py` (A01/A05 — clickjacking, open redirect, referrer policy, HTML comments), `test_vapt_ssrf.py` (A10 — IMDS probes, RFC-1918 rebinding). OWASP inference fixed: `clickjack` moved A03→A05, added `path_traversal`, `httponly`, `samesite`, `dns_rebinding` keywords. Template viewer panel in Scans tab — "View Standard Test Templates" collapsible with per-file OWASP context and code. `vapt._vapt_products()` is now the single source of truth — `pages.py` `vapt_page()` no longer duplicates the filtering logic. RP result: 25 passed, 3 skipped, 3 xfailed.

## Previous: Script TC ID normalizer (2026-05-18)

- **Script TC ID normalizer** (`ai/pipeline/orchestrator.py`): Added `_normalize_script_fn_ids()` — code-level backstop that runs after `ScriptGenAgent` and before `ScriptReview`. Reads TC IDs from the doc index table (skipping `not_automatable` rows) in order, matches them to test function declarations in order, renames any function whose embedded ID doesn't match (e.g. `test_OH_API_001_x` → `test_OH_API_014_x`). Also handles functions with no ID prefix at all by prepending it. Silently skips if function count ≠ doc ID count (mismatch = human review needed). Closes the gap where models consistently ignored the TC IDs in the doc and numbered from 001.

## Previous: Quality dashboard metrics overhaul (2026-05-18)

- **Quality dashboard metrics overhaul** (`dashboard/routers/quality.py`, `dashboard/templates/quality.html`): Pass rate now computed from actual pytest results in `test_runs` table (was incorrectly using `activity_log` agent status). Added: automated test function count (`def test_` grep, not file count — 169 functions vs 25 scripts), execution stats card (total/passed/failed from real runs), 7-day pass rate trend from `test_runs` daily aggregates, composite risk score 0–100 (pass rate gap 50pt + quarantine rate 20pt + doc gap 20pt + flaky 10pt). Template expanded from 5 to 6 summary cards; each card has an `ⓘ` Alpine tooltip explaining its formula. Per-product table updated: automated test count, real pass rate, execution breakdown, risk badge.

## Previous: ScriptReview fix + Timesheets pipeline (2026-05-18)

- **ScriptReview KeyError fix** (`ai/agents/script_review_agent.py`): `_REWRITE_PROMPT` template had unescaped `{"positive", "negative", "edge"}` set literals — Python's `str.format()` raised `KeyError` silently caught by the orchestrator, skipping ALL ScriptReview passes. Fixed by doubling the braces (`{{...}}`).
- **Orchestrator fixes** (`ai/pipeline/orchestrator.py`): (1) DocReview now always runs even when `--doc` (skip_doc=True) is used — was only running on freshly generated docs. (2) `--doc` path now resolved to absolute so `relative_to(ROOT_DIR)` never fails. (3) Default doc-model changed from `mistral:7b-instruct-v0.3-q4_K_M` to `qwen2.5-coder:14b-instruct-q4_K_M`.
- **Timesheets test scripts corrected**: API script rewritten with correct IDs OH-API-014..028 (was 001..011), real status-code + body assertions, `orangehrm_client` + `shared_state` fixtures. Web script completed with all 11 TCs OH-WEB-072..082 (was 5 of 11), added validation-error helper assertions for 074–077, stubs for 078–082.

## Previous: VAPT standard test suite generation (2026-05-18)

- **VAPT standard test suite generation** (`core/vapt_test_generator.py`): `VaptTestGenerator.generate(product, force)` creates `products/<product>/tests/vapt/` with a product-aware `conftest.py` (auto-detects `base_url`/`api_token` from `env_*.yaml`) and 5 test files covering OWASP A01/A02/A04/A05/A07 — 17 tests total. Tests use `xfail` for infrastructure-dependent checks (rate limiting) and `skip` for environment-dependent ones (HTTPS). Enabling VAPT via the Config toggle auto-generates tests for that product. Two new endpoints: `GET /api/vapt/products/{product}/test-info` + `POST .../generate-tests`. Scans tab in `vapt.html` shows test count and a Regenerate Tests button (admin only). First generated suite for `reportportal`: 13 passed, 2 skipped, 2 xfailed against live RP.

## Previous: VAPT security review fixes (2026-05-18)

- **Doc generation robustness** (`ai/pipeline/orchestrator.py`): `_clean_doc()` strips markdown code-fence wrappers that some models emit before TC ID normalization runs. `_normalize_tc_ids()` now also handles literal `TC_ID` placeholder tokens.
- **VAPT certifiability fix** (`core/vapt_manager.py`): `check_certifiable()` now checks for completed scans (not just presence of findings).
- **ReportPortal VAPT security scan** — all 5 auth-enforcement tests passed against live RP (`localhost:8080`).

## Previous: TC ID generation hardening (2026-05-17)

- **TC ID generation hardening** (3 files): `kb_loader.py` — fixed `get_increments_context()` crash when `feature` key is a plain string (was silently skipping DocReview on every pipeline run). `test_case_doc_kb.py` — `_build_tc_id_instruction()` now emits a concrete 4-step example sequence and an explicit "NEVER start from PREFIX-001" rule. `orchestrator.py` — `_normalize_tc_ids()` post-processes every generated doc; remaps LLM-produced IDs to the correct sequential range starting at `tc_start`, providing a reliable backstop independent of model quality.

## Previous: TC ID conflict prevention + DocReview pass (2026-05-17)

- **TC ID conflict prevention** (`ai/context/conventions.md`): Added full "Test Case ID Rules" section — prefix table for all product/layer combos, 5 conflict-prevention rules (automated tests as source of truth, global uniqueness, auto tc_start, manual ID placement, grep-before-assign), current highest ID snapshot table.
- **Pipeline tc_start auto-detection** (`ai/pipeline/orchestrator.py`): `_find_highest_tc_id()` scans existing docs to find the highest NNN for a given prefix. `main()` auto-computes `tc_start = highest + 1` when prefix is set and user did not override `--tc-start`, preventing silent ID collisions across pipeline runs.
- **Stronger ID uniqueness prompt** (`ai/skills/test_case_doc_kb.py` `_build_tc_id_instruction()`): Explicit CRITICAL warning that starting below tc_start causes silent ID collisions; prohibition on range headings; TC Index table requirement.
- **Doc ID conflict fixes** (15 existing docs): Renumbered manual test IDs that collided with automated IDs in other module docs. Manual tests pushed to 058–071 range (OH-WEB), 012–014 range (RB-WEB). Affected: login.md, pim_employee.md, admin_users.md, leave_list.md (OH), booking.md + admin.md (RB).
- **New test case docs** (9 new files): Created docs for security/accessibility/mobile tests that had no doc: OH web+api security (OH-SEC-001-012), OH web accessibility (OH-A11Y-001-006), OH mobile login (OH-MOB-001-016, full rewrite), RB web+api security (RB-SEC-001-009), RB web accessibility (RB-A11Y-001-004), RB API booking (RB-API-001-022, full rewrite), RB mobile booking (RB-MOB-001-006, new dir).
- **DocReviewAgent run on all new/updated docs** (15 docs): Structural audit + LLM rewrite pass for pre-conditions, numbered steps, expected result format.

## Previous: VAPT + ScriptReviewAgent + AI assertions (2026-05-17)

- **VAPT module** (`core/vapt_manager.py` + `dashboard/routers/vapt.py` + `dashboard/templates/vapt*.html`): Full vulnerability assessment engagement lifecycle. `VaptManager` handles engagement CRUD, scope definition/finalization, scan records, findings (upsert + patch), certificate issuance (with pass-threshold check), and per-product storage under `data/vapt_findings/<product>/`. REST API at `/vapt/*` (15 endpoints). Dashboard page at `/vapt` with PDF export for plan, report, and certificate.
- **ScriptReviewAgent** (`ai/agents/script_review_agent.py`): Post-generation quality gate for pytest scripts. Static AST pass detects hardcoded URLs/credentials, `time.sleep()`, duplicate test names, POM missing `base_url`. LLM rewrite pass fixes weak/missing assertions, missing domain markers, missing status-code checks on API tests, and exact-equality checks on AI output. Integrated into `TestPipelineOrchestrator` after `_generate_script()`. Registered in `__init__`, `_AGENT_REGISTRY`, `AGENT_META`.
- **AI assertion utilities** (`utils/ai_assertions.py`): Hard assertions for non-deterministic AI output — `assert_confidence_above/below`, `assert_category_in`, `assert_text_contains_any/all`, `assert_text_similarity` (difflib, no extra dep), `assert_response_within`, `assert_field_present`. `SoftAssertions` context manager collects all failures and raises one combined `AssertionError` at block exit. Thresholds centralised in `constants.py` (`AI_CONFIDENCE_THRESHOLD=0.70`, `AI_TEXT_SIMILARITY_RATIO=0.75`, `AI_RESPONSE_TIMEOUT_S=30.0`). ScriptReviewAgent rewrite prompt updated to emit these helpers instead of raw comparisons.

## Previous: SQLite migration + DocReviewAgent + Hetzner (2026-05-15–16)

- **SQLite storage** (`core/db.py`): Replaced FileLock+JSON/YAML with SQLite WAL mode (`data/sentinelflux.db`). All shared state — runs, schedules, approvals, pipeline jobs, activity log, quarantine, run history — now in DB. Supersedes D-01/D-02.
- **DocReviewAgent** (`ai/agents/doc_review_agent.py`): Post-generation quality gate. Detects batched TC headings, missing mandatory sections (Pre-conditions, Steps, Expected Result), and thin TCs (<3 steps). Rewrites each failing TC via targeted LLM prompt + KB context. Integrated into `TestPipelineOrchestrator._review_doc()` (best-effort, never raises). Visible in `/agents` dashboard.
- **DocGenAgent prompt hardening**: `TEST_CASE_DOC_PROMPT` and `API_TEST_CASE_DOC_PROMPT` upgraded with mandatory Fields-in-Scope rule, prohibition on range headings, min-3-steps rule. max_tokens raised: web/feature 3000→6000, API 3000→4000.
- **Analyze All bulk endpoint** + Re-analyze button for already-analyzed runs on `/runs` page.
- **Hetzner deployment**: Server setup and deployment scripts added (`scripts/`).
- **Remote runner** (`dashboard/routers/runner.py`): Pull-based execution — `GET /api/runner/claim` returns next queued run, `POST /api/runner/{id}/progress` streams progress, `POST /api/runner/{id}/result` ingests JSON report and triggers AI analysis. Bearer token auth (bcrypt hashed).
- **Runner token admin** (`dashboard/routers/config/_runners.py`): Admin CRUD for runner tokens. `POST` returns plain token once; only bcrypt hash stored.
- **`sentinelflux runner` CLI daemon** (`sentinelflux/commands/runner_cmd.py`): Polls claim endpoint, resolves test path from product/domain/module, runs pytest subprocess, streams progress every 5s, posts JSON report.
- **Debt D-01–D-06 resolved**: `utils/paths.py` centralisation, config_router split into subpackage (`dashboard/routers/config/`), unit tests for core utils, OpenAI/Anthropic wired to AI client (all later subsumed by SQLite migration).

## Previous: Per-product Run Config + Env Injection (2026-05-15)

- **Per-product Run Config** (`/config` → Run Config tab): CRUD for environment profiles (name, base URL, API URL), browser profiles (chromium/firefox/webkit, headless), device profiles (platform, appium URL, capabilities JSON), credentials (username + password env var ref), and saved defaults per product.
- **Run trigger with config**: Trigger panel and schedule form now load the product's run config profiles on product selection; browser shown only for web/all, device only for mobile/all; defaults pre-selected.
- **Env injection into pytest**: `_execute_run` resolves the chosen profiles and injects `SF_ENV`, `SF_BASE_URL`, `SF_API_URL`, `SF_BROWSER`, `SF_HEADLESS`, `SF_APPIUM_URL`, `SF_DEVICE_PLATFORM`, `SF_DEVICE_CAPABILITIES` into the subprocess environment.
- **Run history snapshot**: Each run record stores `run_config_snapshot`; shown as monospace pills in run history cards. Reruns inherit the original config.

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
ai/agents/                      11 agents: ResultAnalyzer, FlakyDetector, RegressionGuard,
                                  CoverageGap, LocatorHealer, QuarantineManager, DocGen,
                                  DocReview, ScriptGen, ScriptReview, SentinelOrchestrator
ai/agents/doc_review_agent.py   Post-generation quality gate (regex audit + LLM rewrite)
ai/agents/sentinel_orchestrator.py  Post-suite monitoring pipeline (chains all agents)
ai/pipeline/orchestrator.py     End-to-end KB → doc → script (supports --output-base)
api/rest_client.py              REST API test client (supports data_dir param)
api/graphql_client.py           GraphQL test client
pages/base_page.py              Base POM with self-healing locators
sentinelflux/                   CLI commands (init, run, generate, doctor)
utils/constants.py              All magic numbers
utils/ai_factory.py             AI client instantiation (do not duplicate in conftest)
core/vapt_manager.py            VAPT engagement lifecycle: CRUD, scope, scans, findings, certificate issuance
core/db.py                      SQLite connection + schema (WAL mode). Single source of truth for all shared state.
core/approval_manager.py        Human-in-the-loop approvals → sentinelflux.db
core/run_manager.py             Test run records + schedules → sentinelflux.db
conftest.py                     Generic fixtures — NO product references
products/orangehrm/             OrangeHRM example (web + API + KB)
products/restfulbooker/         Restful Booker example (API + KB)
data/sentinelflux.db            SQLite database — runs, schedules, approvals, pipeline jobs, activity log, quarantine
data/product_config/<product>.yaml  Per-product run config (envs, browsers, devices, credentials, defaults)
dashboard/app.py                FastAPI app entry point — registers all routers
dashboard/routers/pages.py      All UI page routes (/, /runs, /agents, /activities, /kb, etc.)
dashboard/routers/runs.py       Test run API + trigger + schedule endpoints; env injection
dashboard/routers/pipeline.py   AI pipeline job trigger + job history
dashboard/routers/config/       Config subpackage: _helpers, _meta, _users, _products, _assignments, _run_config, _runners
dashboard/routers/config/_run_config.py  Per-product run config CRUD — reads/writes data/product_config/<product>.yaml
dashboard/routers/config/_runners.py     Admin CRUD for runner tokens (bcrypt-hashed in config.yaml runner_tokens)
dashboard/routers/runner.py     Remote runner API: /api/runner/claim, /progress, /result (Bearer token auth)
sentinelflux/commands/runner_cmd.py  `sentinelflux runner` daemon — polls claim, runs pytest, posts report
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
- Do not write shared state to raw JSON/YAML files — use `core/db.py` (`get_conn()`) which handles SQLite WAL concurrency automatically
- Do not add new agents to `_AGENT_REGISTRY` in `agents.py` without also adding metadata to `dashboard/agent_meta.py`

---

## AI Doc Generation — Anti-Hallucination Rules

1. **Only test KB-listed fields.** If a field is not in the KB context, it does not exist on that form.
2. **Do not use training-data knowledge of the AUT.** KB context is the only truth.
3. **Add Employee ≠ Employee Profile.** OrangeHRM's Add Employee form has 4 fields only: First Name, Last Name, Middle Name, Employee ID.
4. **Use real credentials.** OrangeHRM demo: `Admin / admin123`. Restful Booker: `admin / password123` (API), `admin / password` (web).
5. **Prompt templates enforce this** via STRICT RULES blocks — if modifying prompts, preserve those blocks.
