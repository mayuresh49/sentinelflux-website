# SentinelFlux

Production-grade Python test automation framework — API, Web UI, and AI-assisted test generation from a knowledge base.

- **REST + GraphQL API testing** with schema validation and curl-equivalent failure logs  
- **Playwright Web UI automation** with self-healing locators (3-tier: Playwright → AI HTML → AI a11y)  
- **AI test generation pipeline**: YAML knowledge base → test case doc → runnable pytest script  
- **Failure artifact collection**: screenshot, screen recording, network trace, browser console log  
- **Per-product examples** showing real applications end-to-end  

---

## Install

```bash
pip install sentinelflux
```

With AI generation support (Mistral or local Ollama/Qwen):

```bash
pip install "sentinelflux[ai]"
```

Requires Python ≥ 3.10.

---

## Quick Start

```bash
# Scaffold a new project
sentinelflux init my-project
cd my-project

# Verify your environment
sentinelflux doctor

# Generate a test case doc from your knowledge base
sentinelflux generate \
    --kb-dir ai/knowledge_base/my-product \
    --output docs/test_cases/web/login.md

# Generate doc + pytest script in one step
sentinelflux generate \
    --kb-dir ai/knowledge_base/my-product \
    --output docs/test_cases/api/booking.md \
    --script
```

---

## Run Tests

```bash
# API tests
pytest tests/api/ -m api

# Web tests (parallel, session-scoped login)
pytest tests/web/ -m web -n 4 --session-login

# Specific environment
pytest tests/api/ -m api --env staging
```

---

## Full AI Pipeline (local Qwen / Mistral)

```bash
# One-time setup — installs deps, checks Ollama, pulls model
./setup_ai_generator.sh

# Generate doc + script for a product
./run_pipeline.sh orangehrm login web
./run_pipeline.sh restfulbooker booking api
```

---

## Examples

| Example | Tests | Notes |
|---|---|---|
| [`products/orangehrm`](products/orangehrm) | Web UI + API | OrangeHRM HR system demo |
| [`products/restfulbooker`](products/restfulbooker) | API (13 tests) | Restful Booker hotel booking API |

Run an example:

```bash
cd products/restfulbooker
pytest tests/api/ -m api
```

Or from the root via Make:

```bash
make restfulbooker-api
make orangehrm-api
make orangehrm-web
```

---

## Self-Healing Locators

Every `@step_method`-decorated page object action is automatically resilient:

```
Tier 1 — Playwright locator              deterministic, zero overhead when passing
    ↓ TimeoutError
Tier 2 — AI reads page HTML → JS         same browser session, executes via page.evaluate()
    ↓ still fails
Tier 3 — AI reads accessibility tree → JS  richer semantic context
    ↓ still fails → test fails normally
```

All three tiers run inside the existing browser session — SPA state, cookies, and form data are preserved.

Enable in `config/env_qa.yaml`:

```yaml
sentinelflux:
  ai:
    enabled: true
    mode: mistral
    api_key: "your-key"   # or set MISTRAL_API_KEY env var
```

---

## Failure Artifacts

Collected automatically on test failure:

| Artifact | Applies to |
|---|---|
| Viewport + full-page screenshot | Web |
| Screen recording (`.webm`) | Web |
| Playwright network trace (`.zip`) | Web |
| Browser console log | Web |
| API request/response log (curl-equivalent) | API |

Open trace files at [trace.playwright.dev](https://trace.playwright.dev).

---

## AI Test Generation

### Knowledge Base

Drop feature YAML files in `ai/knowledge_base/<product>/`. Three template files:

- `application.yaml` — app metadata, base URLs, auth type
- `api_specs.yaml` — REST endpoints and GraphQL queries
- `ui_pages.yaml` — pages, elements, and test scenarios

```bash
# Copy templates for a new product
sentinelflux init my-project   # scaffolds the full structure
```

### Generate

```bash
# Web test case doc
sentinelflux generate \
    --kb-dir ai/knowledge_base/orangehrm \
    --output products/orangehrm/docs/test_cases/web/login.md

# API test case doc
sentinelflux generate \
    --endpoint /booking --method POST \
    --kb-dir ai/knowledge_base/restfulbooker \
    --output products/restfulbooker/docs/test_cases/api/booking_create.md

# Doc + script in one step
sentinelflux generate \
    --kb-dir ai/knowledge_base/restfulbooker \
    --output products/restfulbooker/docs/test_cases/api/booking.md \
    --script
```

Use local Ollama/Qwen instead of Mistral cloud:

```bash
./run_pipeline.sh restfulbooker booking api qwen2.5-coder:14b-instruct-q4_K_M
```

---

## Project Structure

```
ai/                   KB loader, AI clients, test generation skills and pipeline
  knowledge_base/     Per-product KB directories (orangehrm/, restfulbooker/)
  pipeline/           End-to-end orchestrator (KB → doc → script)
  skills/             AI skills (doc gen, script gen, self-healing)
api/                  REST and GraphQL clients
config/               Environment YAML profiles (env_qa.yaml, env_staging.yaml)
products/             Working example projects
  orangehrm/          OrangeHRM web + API tests
  restfulbooker/      Restful Booker API tests
pages/                Page Object Models (web)
sentinelflux/         CLI (init, run, generate, doctor)
tests/                Framework-level test stubs
utils/                Logger, locator manager, AI factory, constants
```

---

## CLI Reference

```
sentinelflux init <name>      Scaffold a new project
sentinelflux run              Run tests (wraps pytest)
sentinelflux generate         Generate test doc/script from KB
sentinelflux doctor           Check environment prerequisites
```

---

## Configuration

```yaml
# config/env_qa.yaml
sentinelflux:
  ai:
    enabled: true
    mode: mistral          # or "ollama" for local
    api_key: "..."         # or MISTRAL_API_KEY env var
    local_url: "http://localhost:11434"

web:
  base_url: "https://your-app.example.com"
  browser: chromium
  headless: true

api:
  base_url: "https://your-api.example.com"
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
