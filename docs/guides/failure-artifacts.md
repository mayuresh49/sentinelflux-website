# Failure Artifacts

On test failure, the following are collected automatically into `reports/artifacts/<test-id>/`.

## Web tests

| Artifact | File | Description |
|---|---|---|
| Full-page screenshot | `screenshot_full_page.png` | Entire page, not just viewport |
| Browser console log | `console.log` | All console messages captured during the test |
| Network + browser trace | `trace.zip` | Open at [trace.playwright.dev](https://trace.playwright.dev) |
| Screen recording | `test-results/<test>/video.webm` | Written by pytest-playwright |

## API tests

| Artifact | File | Description |
|---|---|---|
| API request/response log | `api_calls.log` | Every request as a curl-equivalent (auth headers redacted), status code, elapsed ms, full JSON response |

## ReportPortal

When `RP_API_KEY` is set, all artifacts above are also attached to the RP launch automatically via Python's logging bridge — no additional configuration needed.

```bash
export RP_API_KEY=your_key_here
sentinelflux run
```

## Enabling recordings and traces

These are configured in `pytest.ini`:

```ini
addopts = --screenshot=on --video=retain-on-failure --tracing=retain-on-failure
```

Change `retain-on-failure` to `on` to collect for all tests, or `off` to disable.
