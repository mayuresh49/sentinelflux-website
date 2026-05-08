# SentinelFlux — AI Resume Context

> **READ THIS FIRST.** Any AI tool working on this project should read this file before anything else.

Last updated: 2026-05-08  
Framework version: 0.1.0

---

## What This Project Is

Solo-built test automation framework covering API, UI, Mobile (scaffold), and Security (scaffold). Dual purpose: learning vehicle + potential product. Owner has 13+ yrs QE/SDE experience. Budget-constrained — be token-efficient.

---

## Current State

| Layer | Status | Notes |
|---|---|---|
| REST API | Working | Full CRUD, schema validation, data-driven, curl log on failure |
| GraphQL | Working | Query + variable support |
| Web UI | Working | POM + self-healing locators (3-tier) |
| Mobile | Scaffolded | Appium dep present, zero implementation |
| Security | Scaffolded | Marker only, nothing implemented |
| AI/KB Pipeline | Working | KB → doc → script (Mistral + Ollama/Qwen). `ai/pipeline/orchestrator.py` |
| CLI | Working | `sentinelflux init/run/generate/doctor` via typer |
| Examples | Working | OrangeHRM (web+api), Restful Booker (13 API tests passing) |
| Docs site | Built | mkdocs-material, `mkdocs serve` to preview |
| Package | Built | `pyproject.toml` + hatchling, `pip install sentinelflux` |

---

## What Was Just Done (Sprints 1–4 + cleanup — 2026-05-08)

**Productization sprints:**
- Sprint 1: Apache 2.0 license, `pyproject.toml`, CLI (`init/run/generate`), OrangeHRM moved to `examples/`, GitHub Actions CI
- Sprint 2: mkdocs docs site, `sentinelflux doctor`, PyPI publish workflow, CONTRIBUTING.md, issue templates
- Sprint 3: Restful Booker second example (22 tests, 13/13 API passing), `sentinelflux init` smoke-tested, doc fixes
- Sprint 4: Product KB separation — per-product `ai/knowledge_base/<product>/` dirs, `--kb-dir` CLI flag, `RestClient data_dir` param

**Cleanup (items 6–9):**
- `Makefile` — per-product targets (`orangehrm-web/api`, `restfulbooker-web/api`, `framework-tests`)
- `run_pipeline.sh` — passes `--output-base examples/$PROJECT` to orchestrator; correct output path echo
- `ai/pipeline/orchestrator.py` — added `--output-base` CLI flag + `output_base` param to route doc/script output to example dirs
- `setup_ai_generator.sh` — full rewrite: installs `sentinelflux[ai]`, checks Ollama, pulls model, shows quick start
- `docs/test_cases/form_test_cases.md` — deleted (stale generic file)

**README + CI (2026-05-08):**
- README rewritten as product landing page with CLI-first quick start, examples table, self-healing docs
- CI: added `restfulbooker` collection smoke check, removed `|| true` on root collect

---

## Next Immediate Actions

These require user action (run/verify locally or publish):

1. **Test `sentinelflux generate` end-to-end** — user has Qwen running at localhost:11434  
   `./run_pipeline.sh restfulbooker booking api`

2. **Run web tests** — `make restfulbooker-web` and `make orangehrm-web` against live demo sites

3. **`sentinelflux doctor` output check** — run and verify all checks pass

4. **TestPyPI smoke test** — `python -m build && twine upload --repository testpypi dist/*`

5. **GitHub Pages deploy** — `mkdocs gh-deploy`

6. **v0.1.0 tag + PyPI publish** — `git tag v0.1.0 && git push --tags`  
   Publish workflow in `.github/workflows/publish.yml` triggers on tag push.

Framework-level feature backlog: `framework_knowledge/progress/backlog.yaml`

---

## Key Architectural Decisions

- AI client: Mistral (cloud) or Ollama (local). Abstracted behind `AIClient` base. See `ADR-002`.
- KB structure: YAML files in `ai/knowledge_base/<product>/` (one dir per product). Increments in `ai/knowledge_base/increments/`.
- Per-product output: `examples/<product>/docs/test_cases/` and `examples/<product>/tests/`. Pass `--output-base examples/<product>` to orchestrator.
- Schema location: `schemas/rest_schemas/` is canonical. `api/schemas/` is dead code — do not use.
- All magic numbers: `utils/constants.py`
- RP API key: env var `RP_API_KEY` only, never committed.
- `BasePage.__init__(page, locale="en-US")` — NO base_url param; subclass stores URL as instance variable.
- `booking_client.py` lives at `examples/restfulbooker/` root (not `api/` subdir) — avoids namespace package collision under pytest.

---

## Where Things Live

```
ai/knowledge_base/<product>/   Per-product KB (application, api_specs, ui_pages, product_knowledge)
ai/knowledge_base/increments/  Feature drop YAMLs
ai/knowledge_base/kb_loader.py Loads base + increments, formats context for prompts
ai/clients/mistral_client.py   LLM client (cloud + local Ollama)
ai/skills/                     AI-powered skills (doc gen, script gen, self-healing)
ai/pipeline/orchestrator.py    End-to-end KB → doc → script (supports --output-base)
api/rest_client.py             REST API test client (supports data_dir param)
api/graphql_client.py          GraphQL test client
pages/base_page.py             Base POM with self-healing locators
sentinelflux/                  CLI commands (init, run, generate, doctor)
utils/constants.py             All magic numbers
utils/ai_factory.py            AI client instantiation (do not duplicate in conftest)
conftest.py                    Generic fixtures — NO product references
examples/orangehrm/            OrangeHRM example (web + API)
examples/restfulbooker/        Restful Booker example (API)
framework_knowledge/           This tracking system
```

---

## Conventions (quick ref)

- Test files: `examples/<product>/tests/{domain}/test_{feature_name}.py`
- KB per product: `ai/knowledge_base/<product>/`
- Generated docs: `examples/<product>/docs/test_cases/{domain}/{feature_name}.md`
- Generated scripts: `examples/<product>/tests/{domain}/test_{feature_name}.py`
- Locator files: `locators/{platform}/{page_name}.json` with `primary` + `alternatives`
- Config per env: `config/env_{qa|staging|prod}.yaml`
- All timeouts/magic numbers: define in `utils/constants.py`, import everywhere

---

## Do Not

- Do not hardcode API keys or tokens anywhere — use env vars
- Do not add `@lru_cache` to instance methods — use `self._cache` dict
- Do not create files under `api/schemas/` — dead code
- Do not duplicate AI factory logic — use `utils/ai_factory.py`
- Do not add magic numbers inline — add to `utils/constants.py`
- Do not put product-specific imports in root `conftest.py`
- Do not put `booking_client.py` inside `api/` subdir in examples — namespace collision under pytest

## AI Doc Generation — Anti-Hallucination Rules

1. **Only test KB-listed fields.** If a field is not in the KB context, it does not exist on that form.
2. **Do not use training-data knowledge of the AUT.** KB context is the only truth.
3. **Add Employee ≠ Employee Profile.** OrangeHRM's Add Employee form has 4 fields only: First Name, Last Name, Middle Name, Employee ID.
4. **Use real credentials.** OrangeHRM demo: `Admin / admin123`. Restful Booker: `admin / password123` (API), `admin / password` (web).
5. **Prompt templates enforce this** via STRICT RULES blocks — if modifying prompts, preserve those blocks.
