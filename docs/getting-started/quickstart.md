# Quick Start

## 1. Scaffold a project

```bash
sentinelflux init my-project
cd my-project
```

This creates:

```
my-project/
  config/env_qa.yaml    ← edit with your app URL and credentials
  tests/web/            ← add your web tests here
  tests/api/            ← add your API tests here
  pages/web/            ← add your page objects here
  conftest.py
  pytest.ini
```

## 2. Configure your app

Edit `config/env_qa.yaml`:

```yaml
web:
  base_url: "https://your-app.example.com"
api:
  rest_base_url: "https://your-api.example.com"
```

## 3. Write a test

```python
# tests/web/test_login.py
import pytest
from pages.web.login_page import LoginPage

@pytest.mark.web
def test_login_valid(page, config):
    lp = LoginPage(page)
    lp.navigate()
    lp.login("user@example.com", "password")
    assert lp.is_logged_in()
```

## 4. Run

```bash
sentinelflux run
# or: python3 -m pytest tests/web/ -m web
```

HTML report: `reports/report.html`

## 5. Run in parallel

```bash
sentinelflux run --workers 4
```
