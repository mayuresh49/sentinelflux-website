# Contributing to SentinelFlux

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
playwright install chromium
```

## Running tests

```bash
# Root generic tests (collection smoke)
python3 -m pytest --collect-only -q

# OrangeHRM example suite
cd products/orangehrm && python3 -m pytest --collect-only -q
```

## Code standards

- Lint: `ruff check .` (must pass before PR)
- No new OrangeHRM-specific code in the root framework — it belongs in `products/`
- No premature abstractions — extract only when there are 3+ real duplications
- One-line comments only, and only when the WHY is non-obvious

## Project structure

```
ai/               AI engine — agents, clients, skills, pipeline, KB loader
  context/        AI/Claude orientation docs + ADRs + backlog
core/             Framework services (run manager, approvals, activity log, AI factory)
dashboard/        FastAPI web dashboard
data/             Runtime app state (run history, pipeline jobs, approvals)
products/         Per-product test suites with KB, tests, pages, and docs
  orangehrm/      OrangeHRM — web UI + API suites
  restfulbooker/  Restful Booker — API suites
utils/            Test helpers (assertions, step, wait, locator manager)
api/              Generic REST + GraphQL clients
pages/            Framework-level page base classes
sentinelflux/     CLI (init, run, generate, doctor)
config/           Generic environment profiles
scripts/          Shell scripts (run_pipeline, setup_ai_generator, start-local)
tests/            Framework-level tests (unit, api, web, mobile)
.github/          CI/CD workflows, issue templates
```

## Submitting a PR

1. Branch from `main`
2. Make your changes
3. Run `ruff check .` and fix any issues
4. Verify both collection smoke checks pass (see above)
5. Open a PR — use the PR template

## Releasing

Releases are triggered by pushing a version tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

This triggers the PyPI publish workflow automatically.
