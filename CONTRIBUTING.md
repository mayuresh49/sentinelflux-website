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
ai/               AI test generation pipeline
api/              Generic REST + GraphQL clients
pages/            Base page objects
utils/            Shared utilities (step tracking, AI registry, locator manager)
sentinelflux/     CLI (typer) + project scaffold templates
config/           Generic environment profiles
products/         Self-contained example projects
  orangehrm/      OrangeHRM demo — web UI + API suites
tests/            Generic framework-level tests
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
