# Configuration Reference

Configuration is loaded from `config/env_<env>.yaml`. Use `--env` to select the profile (default: `qa`).

## Full schema

```yaml
api:
  rest_base_url: "https://your-api.example.com"
  graphql_endpoint: "https://your-graphql.example.com/graphql"

web:
  base_url: "https://your-app.example.com"

reportportal:
  endpoint: "http://localhost:8080/"
  project: "your-project"
  launch: "your-launch-name"
  # API key: set RP_API_KEY env var — never store in config

browser:
  timeout: 12000             # Playwright default timeout in ms

logging:
  level: "INFO"              # DEBUG | INFO | WARNING | ERROR
  file: "logs/sentinelflux.log"

mobile:
  appium_url: "http://localhost:4723"
  platform: "android"
  capabilities:
    platformName: "Android"
    deviceName: "emulator-5554"
    automationName: "UiAutomator2"
    appPackage: "com.example.app"
    appActivity: ".MainActivity"
    noReset: true
    newCommandTimeout: 60

sentinelflux:
  ai:
    enabled: false
    mode: mistral             # mistral | local
    self_healing: false
    api_key: ""               # or set MISTRAL_API_KEY env var
```

## Environment variables

| Variable | Description |
|---|---|
| `RP_API_KEY` | ReportPortal API key |
| `MISTRAL_API_KEY` | Mistral API key (overrides `sentinelflux.ai.api_key`) |
