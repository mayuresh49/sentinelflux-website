# Changelog

All notable changes to SentinelFlux are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-05-07

### Added
- Core test framework: pytest + pytest-playwright + pytest-xdist
- REST API client with per-test request/response logging (`api_calls.log`)
- GraphQL client
- Page Object Model base (`BasePage`) with `@step_method` decorator
- 3-tier same-session self-healing: Playwright → AI+HTML JS → AI+a11y JS via `page.evaluate()`
- Step tracking: inline step table in HTML report + ReportPortal log stream
- Failure artifact collection: full-page screenshot, console log, network trace, API call log
- AI-assisted test generation pipeline: KB → test case doc → pytest script (Mistral)
- Product knowledge YAML + incremental KB loader
- Environment profiles: QA, Staging, template (`config/env_*.yaml`)
- `sentinelflux` CLI: `init`, `run`, `generate` commands (typer)
- Apache 2.0 license
- OrangeHRM example: 41 tests across web UI and API suites (`products/orangehrm/`)
- Jenkins CI/CD pipeline with parameterized suites, browser, environment, and RP toggle
- GitHub Actions CI: lint (ruff) + package build check
