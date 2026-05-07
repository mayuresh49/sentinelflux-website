# SentinelFlux Test Automation Framework

Production-grade Python test framework for API, Web UI, and Mobile automation with AI-assisted test generation, self-healing locators, environment profiles, ReportPortal reporting, and full failure artifact collection.

## Features

- REST API and GraphQL API test support
- Playwright Web UI automation with self-healing locators (3-tier: Playwright → Browser-Use → Skyvern)
- Mobile automation scaffold (Appium)
- External JSON locators with locale-aware fallback
- Environment profiles: QA, Staging, Prod (`config/env_*.yaml`)
- AI-driven test generation: KB → test case doc → pytest script (Mistral)
- ReportPortal integration: auto-attach screenshot, console log, trace on failure
- Failure artifacts: full-page screenshot, browser console log, Playwright network trace, screen recording
- Parallel execution via pytest-xdist with session-scoped login option
- Jenkins CI/CD pipeline with parameterized suites, browser, environment, and RP toggle

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

Run web tests (parallel, session login):
```bash
make web
# or directly:
python3 -m pytest tests/web/ -m web -n 4 --session-login
```

Run a specific suite:
```bash
python3 -m pytest tests/web/test_login.py -m web -n 4 --session-login
python3 -m pytest tests/web/test_pim_employee.py -m web -n 4 --session-login
```

Run API tests:
```bash
make api
```

## Environment Profiles

```bash
pytest --env=qa        # default
pytest --env=staging
pytest --env=prod
```

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--env` | `qa` | Environment profile |
| `--browser` | `chromium` | Playwright browser (`chromium`, `firefox`, `webkit`) |
| `-n` | — | xdist worker count (`-n 4` for parallel) |
| `--session-login` | off | Reuse one login per xdist worker instead of per-test |

## Step Tracking

Every `@step_method`-decorated page object method is automatically recorded as a numbered step. No changes needed in tests — decoration lives on the page object.

| Destination | What you see |
|---|---|
| HTML report (`reports/report.html`) | Inline step table per test: `#`, description, **PASS** (green) / **FAIL** (red) |
| ReportPortal | Log stream per test via `sentinelflux.steps` logger |

## 3-Tier Resilience (Self-Healing)

Every `@step_method`-decorated action routes through `BasePage.try_resilient()`:

```
Tier 1 — Playwright (deterministic, fast, zero overhead on happy path)
    ↓ only on playwright.sync_api.TimeoutError
Tier 2 — Browser-Use + local Ollama LLM  [self-healing: goal-based element discovery]
    ↓ only on Tier-2 failure
Tier 3 — Skyvern vision agent            [self-healing: screenshot/visual element discovery]
```

**Execution time impact:** zero on passing tests. Escalation only fires when Playwright already timed out — the test was going to fail anyway.

**Tier 2 prerequisites:** Ollama running locally with `qwen2.5:7b` (or override `BROWSER_USE_MODEL` in `utils/constants.py`). Install: `pip install browser-use langchain-ollama`.

**Tier 3 prerequisites:** Skyvern running at `SKYVERN_BASE_URL` (default `http://localhost:8000`). Install: `pip install httpx`.

**Auth:** `try_resilient` extracts `page.context.cookies()` and injects them into Browser-Use's browser context before the agent runs — the agent inherits the existing authenticated session and does not need to log in. Both tiers are lazy-imported: if not installed a `RuntimeError` is raised and only the current step fails.

## Failure Artifacts

On test failure, the following are collected automatically:

| Artifact | Location | Applies to |
|----------|----------|------------|
| Viewport screenshot | `test-results/<test>/` | Web |
| Full-page screenshot | `reports/artifacts/<test>/screenshot_full_page.png` | Web |
| Screen recording | `test-results/<test>/video.webm` | Web |
| Network + browser trace | `test-results/<test>/trace.zip` | Web |
| Browser console log | `reports/artifacts/<test>/console.log` | Web |
| API request/response log | `reports/artifacts/<test>/api_calls.log` | API |

`api_calls.log` — every request in the test as a curl-equivalent (auth headers redacted), status code, elapsed ms, and full JSON response.

Open trace files at [trace.playwright.dev](https://trace.playwright.dev) (no install needed).

## ReportPortal

When `RP_API_KEY` is set, all artifacts above are also attached to the RP launch automatically:

```bash
export RP_API_KEY=your_key_here
pytest tests/web/ -m web -n 4 --session-login
```

RP endpoint and project are configured in `pytest.ini` and `config/env_qa.yaml`.

For Jenkins: enable the `ENABLE_RP` parameter and add a `rp-api-key` Secret Text credential in the Jenkins credentials store.

## AI Test Generation

Generate a test case doc from the KB:
```bash
python3 -m ai.generate_test_case_doc --config config/env_qa.yaml \
    --output docs/test_cases/web/my_page.md
```

Generate an API test case doc:
```bash
python3 -m ai.generate_api_test_doc --endpoint /booking --method POST \
    --output docs/test_cases/api/booking_create.md
```

Run the full KB → doc → script pipeline:
```bash
./run_pipeline.sh
```

See `docs/` for full guides on KB structure, test generation, and AI skill usage.

## Project Structure

```
ai/               KB loader, Mistral client, test generation skills and pipeline
api/              REST and GraphQL clients
config/           Environment YAML profiles
conftest.py       Fixtures + artifact collection hooks
docs/             Guides and generated test case docs
framework_knowledge/  RESUME.md (start here), backlog, architecture decisions
locators/         JSON locator files (web + mobile)
pages/            Page Object Models (web + mobile)
pytest.ini        Test configuration, markers, RP settings
reports/          HTML reports + failure artifacts (gitignored)
tests/            Test suites (api/, web/, mobile/, integration/)
utils/            Logger, locator manager, AI factory, security utils
```

## CI/CD

```bash
# Jenkinsfile parameters (Build with Parameters):
# ENV             qa | staging | prod
# BROWSER         chromium | firefox | webkit
# PARALLEL_COUNT  4 | 2 | 1 | 8
# SESSION_LOGIN   true | false
# RUN_WEB_LOGIN   true | false
# RUN_WEB_PIM     true | false
# RUN_API         true | false
# ENABLE_RP       true | false  (requires rp-api-key Jenkins credential)
```
