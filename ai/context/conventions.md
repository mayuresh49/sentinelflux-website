# SentinelFlux — Code & File Conventions

## File Naming

| Type | Pattern | Example |
|---|---|---|
| Test file | `tests/{domain}/test_{feature}.py` | `tests/api/test_booking.py` |
| Page object | `pages/{platform}/{page_name}.py` | `pages/web/booking_page.py` |
| Locator file | `locators/{platform}/{page_name}.json` | `locators/web/booking_page.json` |
| KB increment | `ai/knowledge_base/increments/feature_{NNN}_{name}.yaml` | `feature_002_booking_v2.yaml` |
| Generated doc | `docs/test_cases/{domain}/{feature}.md` | `docs/test_cases/api/booking.md` |
| Payload | `api/payloads/rest_payloads/{name}.json` | `create_booking.json` |
| Schema | `schemas/rest_schemas/{name}.json` | `booking_schema.json` |
| Config | `config/env_{env}.yaml` | `env_staging.yaml` |

## Test Structure

```python
@pytest.mark.api
def test_create_booking_returns_201(rest_client):
    response = rest_client.post("create_booking", payload_name="create_booking", schema_name="booking")
    assert response.status_code == 201
```

- One assertion focus per test (name describes the assertion)
- Test name format: `test_{action}_{expected_result}`
- Use fixtures from conftest, not direct instantiation
- Parametrize for data-driven cases, not separate test functions

## Page Object Pattern

```python
class BookingPage(BasePage):
    LOCATOR_FILE = "web/booking_page.json"

    def fill_firstname(self, name: str):
        self.fill("firstname", name, self.LOCATOR_FILE)

    def submit(self):
        self.click("submit_button", self.LOCATOR_FILE)
```

- One class per page/screen
- All locator access via `self.healed_locator()` (self-healing enabled)
- High-level domain methods only — no raw Playwright calls in tests
- `LOCATOR_FILE` as class constant

## Locator JSON Format

```json
{
  "firstname": "#firstname",
  "email_checkbox": {
    "primary": "#email",
    "alternatives": ["label[for='email']", "[data-testid='email-check']"]
  }
}
```

- Simple string for stable elements
- Object with `primary` + `alternatives` array for fragile elements
- For locale-aware: `{"en-US": "#firstname", "fr-FR": "#prenom", "default": "#firstname"}`

## KB Increment Format

```yaml
feature:
  name: "Booking V2 - Multi-room support"
  version: "2.1.0"
  release_date: "2026-Q2"
  status: "in_development"

new_endpoints:
  - path: /booking/multi
    method: POST
    description: Create multi-room booking

new_ui_pages:
  - name: Multi-room Booking Form
    url: /booking/multi
    fields: [...]

business_rules:
  - "Maximum 5 rooms per booking"
  - "Total guests must not exceed room capacity"

test_scenarios:
  api:
    - "POST /booking/multi with valid payload returns 201"
    - "POST /booking/multi exceeding room limit returns 400"
  ui:
    - "Multi-room form validates room count"
  security:
    - "Non-authenticated user cannot create multi-room booking"
```

## Constants Usage

All timeouts, sizes, and magic numbers go in `utils/constants.py`.

```python
# In any file:
from utils.constants import LOCATOR_HEAL_TIMEOUT_MS, DEFAULT_BROWSER_TIMEOUT_MS
```

Never inline: `timeout=2000` — always use the constant.

## AI Client Usage

```python
# Always use the factory — never instantiate directly in conftest or tests
from utils.ai_factory import create_ai_client
client = create_ai_client(ai_config)
```

## Environment Variables

| Var | Purpose |
|---|---|
| `RP_API_KEY` | ReportPortal API key |
| `MISTRAL_API_KEY` | Mistral cloud API key (alternative to config file) |

## What Goes Where

- Magic numbers → `utils/constants.py`
- AI client creation → `utils/ai_factory.py`
- Session fixtures → `conftest.py`
- Product/feature knowledge → `ai/knowledge_base/base/*.yaml`
- New feature context → `ai/knowledge_base/increments/feature_NNN_*.yaml`
- API keys → env vars, never committed
