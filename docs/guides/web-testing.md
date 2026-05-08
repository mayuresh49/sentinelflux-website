# Web Testing

## Page Object Model

All page objects extend `BasePage`. `BasePage.__init__` takes `(page, locale="en-US")` — the app URL is passed to individual methods (or stored as an instance variable in the subclass), not to the constructor.

```python
from pages.base_page import BasePage
from utils.step import step_method

class LoginPage(BasePage):

    def __init__(self, page, base_url: str):
        super().__init__(page)
        self._base_url = base_url

    @step_method("Navigate to login")
    def navigate(self):
        self.page.goto(f"{self._base_url}/login")

    @step_method("Enter username")
    def enter_username(self, value: str):
        self.page.locator("#username").fill(value)

    @step_method("Click submit")
    def submit(self):
        self.page.locator("[type=submit]").click()
```

Each `@step_method` call:
1. Records the step for the HTML report
2. Routes through `try_resilient()` for automatic self-healing on timeout

## Writing tests

```python
import pytest
from pages.web.login_page import LoginPage

@pytest.mark.web
def test_login(page, config):
    base_url = config["web"]["base_url"]
    lp = LoginPage(page, base_url)
    lp.navigate()
    lp.enter_username("user@example.com")
    lp.submit()
    assert lp.is_logged_in()
```

## Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `page` | function | Fresh Playwright page per test |
| `config` | session | Loaded from `config/env_<env>.yaml` |
| `locale` | session | `--locale` CLI flag value |
| `browser_page` | function | Page with timeout from config applied |

## Parallel execution

```bash
sentinelflux run web -n 4
```

Each worker gets its own browser context. Use `--session-login` to share one authenticated session per worker.
