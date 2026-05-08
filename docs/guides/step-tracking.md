# Step Tracking

Every `@step_method`-decorated page object method is automatically recorded as a numbered step. No changes are needed in tests.

## HTML report

Each test result includes an inline step table:

| # | Step | Status |
|---|---|---|
| 1 | Navigate to login | PASS |
| 2 | Enter username | PASS |
| 3 | Click login button | FAIL |

Pass steps are green; the failing step is red.

## ReportPortal

Steps are logged to the `sentinelflux.steps` Python logger. When RP is active, each step appears as a log entry in the test's log stream.

## Decorator usage

```python
from utils.step import step_method

class PIMPage(BasePage):

    @step_method("Click Add Employee")
    def click_add(self):
        self.page.locator("button.add").click()

    @step_method("Fill first name")
    def fill_first_name(self, name: str):
        self.page.locator("#firstName").fill(name)
```

Composite methods (e.g. `create_employee()` that calls multiple decorated sub-methods) should **not** themselves be decorated — the sub-steps will appear individually in the report.
