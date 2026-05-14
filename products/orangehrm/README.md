# OrangeHRM Example — SentinelFlux

End-to-end test suite for [OrangeHRM](https://opensource-demo.orangehrmlive.com) (open-source demo).
Demonstrates web UI and REST API testing with SentinelFlux.

## What's covered

| Suite | Tests | Description |
|---|---|---|
| `tests/web/test_login.py` | 5 | Login page — valid, invalid, field validation |
| `tests/web/test_pim_employee.py` | 12 | PIM module — add, search, edit, delete employees |
| `tests/web/test_admin_users.py` | 8 | Admin → User Management — add, search, delete users |
| `tests/api/test_orangehrm_api.py` | 8 | REST API — employee and leave endpoints |
| `tests/api/test_orangehrm_admin.py` | 8 | REST API — admin user CRUD |

## Setup

```bash
cd examples/orangehrm
python3 -m venv .venv && source .venv/bin/activate
pip install sentinelflux[ai]   # or: pip install -r ../../requirements.txt
playwright install chromium
```

## Run

```bash
# All tests
python3 -m pytest

# Web only, parallel
python3 -m pytest tests/web/ -m web -n 4

# API only
python3 -m pytest tests/api/ -m api

# With AI self-healing (set api_key in config/env_qa.yaml first)
python3 -m pytest tests/web/ -m web
```

## Configuration

Edit `config/env_qa.yaml` — credentials, timeouts, AI settings.

To enable self-healing:
```yaml
sentinelflux:
  ai:
    enabled: true
    self_healing: true
    api_key: "your-mistral-api-key"
```

## Structure

```
api/              OrangeHRM API client (cookie-auth, request logging)
config/           env_qa.yaml
pages/web/        Page objects: LoginPage, PIMPage, AdminUsersPage
tests/api/        API test suites
tests/web/        Web UI test suites
conftest.py       OrangeHRM-specific fixtures (config, credentials, client)
pytest.ini        Test config
```
