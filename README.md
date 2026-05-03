# SentinelFlux Test Automation Framework

A scalable Python test framework for API, Web UI, and Mobile automation with AI-assisted test generation, POM design, externalized locators, environment profiles, and ReportPortal reporting.

## Features

- REST API and GraphQL API test support
- Playwright-based Web UI automation
- Mobile automation skeleton for `mobilewright` / Appium
- External JSON locators and locale-aware validation
- Environment profiles: QA, Staging, Prod
- ReportPortal integration with failure screenshot/video support
- Custom utilities: logging, assertions, data generation, self-healing locators
- AI helper modules for requirement parsing and test documentation

## Quick Start

1. Create a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

3. Run the sample tests:
   ```bash
   pytest -q
   ```

## Environment Profiles

Use `--env` to target a different profile:

```bash
pytest --env=qa
pytest --env=staging
pytest --env=prod
```

## ReportPortal

Default ReportPortal settings are populated for `sentinelflux` and `sentinelflux-launch`.
## AI Test Documentation Generation

A new AI doc-generation script is available at `ai/generate_test_case_doc.py`.

Run it with:
```bash
python3 ai/generate_test_case_doc.py --config config/env_qa.yaml --output docs/test_cases/generated_test_case_doc.md
```

This writes the generated test case document into `docs/test_cases/` so it can be version controlled.
## Notes

- Mobile tests are scaffolded and can be connected once the app package and device details are provided.
- AI modules are designed as helpers for generating test documentation and analyzing requirements.
