# Web Test Generation Guide

This guide explains how to generate web UI test documentation using the SentinelFlux AI and Knowledge Base integration.

## Setup

1. Ensure the repository root is the working directory:
   ```bash
   cd /Users/mayureshkulkarni/Documents/Work/sentinelflux-framework
   ```
2. Activate the Python environment and install dependencies:
   ```bash
   source .venv_ai/bin/activate
   pip install -r requirements.txt
   playwright install
   ```
3. Confirm AI is enabled in `config/env_qa.yaml` under `sentinelflux.ai`.
4. Provide a valid `api_key` for cloud Mistral, or use `--local` for a local Ollama instance.

## Generate Web UI documentation

```bash
python3 -m ai.generate_test_case_doc \
  --page-url "https://app.com/booking" \
  --description "Booking form with validation" \
  --output docs/test_cases/web/booking_form_tests.md
```

## Output

- Generated docs are saved under `docs/test_cases/web/`
- Each file contains:
  - page and form description
  - positive and negative user flows
  - validation rules and edge cases
  - expected field behavior

## 3-Tier Resilience in generated tests

`@step_method` routes every page object action through `BasePage.try_resilient()`:

1. **Playwright** — fast deterministic locator, zero overhead on success
2. **Browser-Use + Ollama** — fires only on `playwright.sync_api.TimeoutError`; uses the step description as a natural-language goal to find and interact with the element in its own browser session
3. **Skyvern** — fires only if Browser-Use also fails; screenshot/vision-based element interaction

No code changes in generated tests needed — the chain is automatic.

> **Auth note:** Tiers 2 and 3 do not share Playwright's session. For authenticated pages, include login context in `@step_method` descriptions when writing page objects for protected flows.

## Step tracking in generated tests

All page object action methods are decorated with `@step_method("description")` from `utils/step.py`.
Generated tests call page object methods normally — **no manual step calls needed**.

Steps are captured automatically and appear in two places:

| Destination | What you see |
|---|---|
| HTML report (`reports/report.html`) | Inline step table per test — `#`, step name, **PASS** (green) / **FAIL** (red) |
| ReportPortal | Log stream per test — each step emitted via `sentinelflux.steps` logger |

When the AI generates a new page object, annotate each public action method with `@step_method`:

```python
from utils.step import step_method

class MyPage(BasePage):
    @step_method("Navigate to my page")
    def navigate_to_list(self):
        ...

    @step_method("Fill search field")
    def fill_search(self, value: str):
        ...
```

Do **not** decorate pure getter/checker methods (`is_*`, `get_*`) — those are assertion helpers, not user actions.

## Notes

- The script uses `ai/knowledge_base/ui_pages.yaml` and other KB assets to provide context.
- Use `PYTHONPATH=.` if module imports fail:
  ```bash
  PYTHONPATH=. python3 ai/generate_test_case_doc.py --page-url "https://app.com/booking" --output docs/test_cases/web/booking_form_tests.md
  ```
