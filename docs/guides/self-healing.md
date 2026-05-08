# Self-Healing Locators

SentinelFlux uses a 3-tier escalation strategy when a Playwright locator times out. All three tiers operate **inside the existing browser session** — no new browser, no page reload, no replay of prior steps.

## How it works

```
Tier 1 — Playwright locator
    ↓ TimeoutError
Tier 2 — AI reads page HTML → generates JS → page.evaluate()
    ↓ still fails
Tier 3 — AI reads accessibility tree → generates JS → page.evaluate()
    ↓ still fails → step marked FAIL
```

SPA state, form data, stepper progress, and auth cookies are fully preserved throughout.

## Enabling self-healing

Set in `config/env_qa.yaml`:

```yaml
sentinelflux:
  ai:
    enabled: true
    self_healing: true
    api_key: "your-mistral-api-key"   # or set MISTRAL_API_KEY env var
```

## Using `@step_method`

Decorate page object methods with `@step_method`. Self-healing fires automatically on timeout — no changes needed in tests.

```python
from utils.step import step_method

class LoginPage(BasePage):

    @step_method("Enter username")
    def enter_username(self, username: str):
        self.page.locator("#username").fill(username)

    @step_method("Click login button")
    def click_login(self):
        self.page.locator("[type=submit]").click()
```

## Execution time impact

- **Zero overhead on passing tests.** Escalation only fires after Playwright already timed out.
- Tier 2 adds one Mistral API call (~1–2 s).
- Tier 3 adds a second call only if Tier 2 also failed.

## Without AI configured

If `ai.enabled` is `false` and a locator times out, a `RuntimeError` is raised immediately and only that step fails — the rest of the test continues to the next step.
