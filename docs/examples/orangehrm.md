# OrangeHRM Example

Full end-to-end test suite for [OrangeHRM](https://opensource-demo.orangehrmlive.com), demonstrating web UI and REST API testing with SentinelFlux.

Located at: `products/orangehrm/`

## What's covered

| Suite | Tests |
|---|---|
| Login page — valid, invalid, validation | 8 |
| PIM module — add, search, edit, delete employees | 11 |
| Admin → User Management — add, search, delete | 7 |
| Leave module — apply, approve, reject | 5 |
| REST API — employee and leave endpoints | 5 |
| REST API — admin user CRUD | 5 |

## Running

```bash
cd products/orangehrm
pip install sentinelflux[ai]
playwright install chromium

# All tests
python3 -m pytest

# Web only, parallel
python3 -m pytest tests/web/ -m web -n 4

# API only
python3 -m pytest tests/api/ -m api
```

## How it's structured

The example uses **namespace packages** — no `__init__.py` in `pages/` directories. Python merges `products/orangehrm/pages/web/` with the framework root `pages/` so both `LoginPage` (example) and `BasePage` (framework) are importable without path hacks.

The `conftest.py` injects both `products/orangehrm/` and the framework root onto `sys.path` at collection time.

See `products/orangehrm/README.md` for full setup and configuration details.
