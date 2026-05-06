# SentinelFlux — System Architecture

## Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  AI PIPELINE                                                     │
│  KB (base + increments) → TestCaseDocSkill → TestScriptGenSkill │
│  Orchestrator drives end-to-end                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ generates
┌─────────────────────────────▼───────────────────────────────────┐
│  TEST LAYER                                                      │
│  tests/api/   tests/web/   tests/mobile/   tests/security/      │
└──────────┬─────────┬───────────────┬─────────────┬─────────────┘
           │         │               │             │
     RestClient  GraphQL       BaseMobilePage   Security
     GraphQLClient  BasePage   (Appium)         assertions
           │         │
    api/endpoints  locators/
    api/payloads   pages/
    schemas/
└─────────────────────────────────────────────────────────────────┘

CROSS-CUTTING
  utils/constants.py    — magic numbers
  utils/ai_factory.py   — AI client creation
  utils/logger.py       — loguru logging
  utils/assertions.py   — custom assertions
  conftest.py           — session fixtures
  config/env_*.yaml     — environment profiles
```

## AI Pipeline Detail

```
Feature drop YAML (ai/knowledge_base/increments/)
    ↓
KnowledgeBaseLoader.load_increments()  ← merges with base KB
    ↓
Orchestrator selects domain (api/ui/mobile/security)
    ↓
TestCaseDocSkill → docs/test_cases/{domain}/{feature}.md
    ↓
TestScriptGenSkill (reads .md + conventions) → tests/{domain}/test_{feature}.py
    ↓
Human reviews diff → commits
```

## Knowledge Base Structure

```
ai/knowledge_base/
├── base/                      ← stable, rarely changes
│   ├── application.yaml       ← app metadata, URLs, test data templates
│   ├── api_specs.yaml         ← REST + GraphQL endpoint specs with neg cases
│   ├── ui_pages.yaml          ← page defs, fields, locators, scenarios
│   └── product_knowledge.yaml ← modules, personas, business rules, use cases
├── increments/                ← one YAML per feature drop
│   └── feature_NNN_name.yaml
└── kb_loader.py               ← loads and merges, formats prompt context
```

## Self-Healing Locator Flow

```
healed_locator(key, locator_file)
  → try primary locator (wait 2s)
  → if TimeoutError: try alternatives[0], alternatives[1]...
  → if all fail: raise TimeoutError with full attempted list
  → on fallback: log warning with which alternative worked
```

## Environment Configuration

```
config/env_{env}.yaml
  api.rest_base_url
  api.graphql_endpoint
  web.base_url
  browser.timeout
  logging.level / logging.file
  sentinelflux.ai.enabled / mode / local / model / api_key
```

## Test Markers

```
@pytest.mark.api      — REST and GraphQL
@pytest.mark.web      — Web UI (Playwright)
@pytest.mark.mobile   — Mobile (Appium)
@pytest.mark.security — Security (OWASP-aligned)
```

Run subset: `pytest -m api`, `pytest -m "api or web"`

## ReportPortal Integration

- Configured in `pytest.ini` (project, endpoint, launch name)
- API key: `RP_API_KEY` env var only — never committed
- Loaded in `conftest.py:pytest_configure`

## Planned Additions (not yet built)

- `pages/mobile/base_mobile_page.py` — Appium-based mobile POM
- `tests/security/` — OWASP injection, auth bypass, IDOR, rate limit tests
- `ai/pipeline/orchestrator.py` — end-to-end doc+script generation
- `ai/skills/test_script_gen.py` — pytest code from test case doc
