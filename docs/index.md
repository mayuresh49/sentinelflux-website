# SentinelFlux

**Production-grade Python test automation framework** with AI-assisted test generation, same-session self-healing locators, and full failure artifact collection.

## What it does

- **Web UI** — Playwright + Page Object Model, `@step_method` decorator, step table in every HTML report
- **REST + GraphQL API** — per-test request/response log, curl-equivalent artifact on failure
- **3-tier self-healing** — Playwright → AI+HTML JS → AI+a11y JS, all in the same browser session
- **AI test generation** — knowledge base → test case doc → pytest script (Mistral)
- **Failure artifacts** — full-page screenshot, console log, network trace, API call log
- **ReportPortal** — all artifacts auto-attached on failure
- **CI/CD** — Jenkins + GitHub Actions, parallel execution via pytest-xdist

## Quick start

```bash
pip install sentinelflux
sentinelflux init my-project
cd my-project
playwright install chromium
sentinelflux run
```

## Example project

See [`examples/orangehrm/`](examples/orangehrm.md) — 41 tests covering web UI and API for the OrangeHRM demo application.
