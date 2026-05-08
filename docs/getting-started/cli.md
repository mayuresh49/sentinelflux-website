# CLI Reference

## `sentinelflux init <project>`

Scaffold a new project directory.

```bash
sentinelflux init my-project
```

Creates the full directory structure with starter `conftest.py`, `pytest.ini`, and `config/env_qa.yaml`.

---

## `sentinelflux run`

Run tests via pytest with SentinelFlux defaults.

```
sentinelflux run [SUITE] [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `SUITE` | _(all tests)_ | Test path or marker, e.g. `tests/web` or `web` |
| `--env` | `qa` | Environment profile |
| `--browser` | `chromium` | Playwright browser |
| `-n` | `1` | Parallel worker count |
| `--session-login` | off | Reuse one login per worker |
| `--extra` | — | Extra pytest args (quoted) |

```bash
sentinelflux run web --env staging --browser firefox -n 4
sentinelflux run tests/api/test_users.py --extra "-k smoke"
```

---

## `sentinelflux generate`

Generate test cases from the knowledge base using AI.

```
sentinelflux generate [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--config` | `config/env_qa.yaml` | Config path |
| `--output` | — | Output path for generated doc |
| `--endpoint` | — | API endpoint (triggers API mode) |
| `--method` | `GET` | HTTP method for API mode |
| `--script` | off | Also generate pytest script from doc |

```bash
sentinelflux generate --output docs/test_cases/web/login.md
sentinelflux generate --endpoint /users --method POST --output docs/test_cases/api/users.md
```

---

## `sentinelflux doctor`

Check that the environment is correctly configured.

```bash
sentinelflux doctor
```

Checks: Python version, required packages, Playwright browsers, AI package, config file, locators directory.
