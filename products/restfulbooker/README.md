# Restful Booker Example — SentinelFlux

End-to-end test suite for [Restful Booker](https://restful-booker.herokuapp.com) (open-source hotel booking demo).
Demonstrates REST API and Web UI testing with SentinelFlux.

## What's covered

| Suite | Tests | Description |
|---|---|---|
| `tests/api/test_booking_api.py` | 10 | Booking CRUD — create, read, update, patch, delete, filter, edge cases |
| `tests/api/test_auth_api.py` | 3 | Auth — valid/invalid credentials, unauthenticated delete |
| `tests/web/test_admin_web.py` | 4 | Admin panel — login, menu visibility, logout |
| `tests/web/test_booking_web.py` | 5 | Booking form — room listing, form open, submit, validation |

## Setup

```bash
cd examples/restfulbooker
python3 -m venv .venv && source .venv/bin/activate
pip install sentinelflux        # or: pip install -r ../../requirements.txt
playwright install chromium
```

## Run

```bash
# All tests
python3 -m pytest

# API only
python3 -m pytest tests/api/ -m api

# Web only
python3 -m pytest tests/web/ -m web
```

## Configuration

`config/env_qa.yaml` — API base URL, web base URL, credentials.

API credentials (`admin` / `password123`) are the Restful Booker public demo defaults.
Web admin credentials (`admin` / `password`) are the automationintesting.online defaults.

## Structure

```
booking_client.py       Restful Booker API client (auth, CRUD, request logging)
config/                 env_qa.yaml
pages/web/              Page objects: AdminPage, HomePage
tests/api/              API test suites
tests/web/              Web UI test suites
ai/knowledge_base/      KB files for AI test generation
conftest.py             Fixtures (config, credentials, booking_client)
pytest.ini
```

## AI test generation

With a Mistral API key set in `config/env_qa.yaml`:

```bash
cd ../..   # framework root
python3 -m ai.generate_test_case_doc \
    --config examples/restfulbooker/config/env_qa.yaml \
    --output docs/test_cases/web/restfulbooker_home.md
```
