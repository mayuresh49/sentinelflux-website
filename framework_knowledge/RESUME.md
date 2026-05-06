# SentinelFlux — AI Resume Context

> **READ THIS FIRST.** Any AI tool (Claude, Cursor, Gemini CLI, etc.) working on this project should read this file before anything else. It contains current state, active decisions, and the next action to take.

Last updated: 2026-05-06  
Framework version: 0.2.0

---

## What This Project Is

Solo-built test automation framework covering API, UI, Mobile, and Security. Dual purpose: learning vehicle + potential product. Owner has 13+ yrs QE/SDE experience. Budget-constrained (individual AI plan) — be token-efficient.

---

## Current State

| Layer | Status | Notes |
|---|---|---|
| REST API | Working | Full CRUD, schema validation, data-driven |
| GraphQL | Working | Query + variable support |
| Web UI | Working | POM + self-healing locators |
| Mobile | Scaffolded | Appium dep present, zero implementation |
| Security | Marker only | Not implemented |
| AI/KB Pipeline | Working | Doc generation from KB. Script gen not yet built. |

---

## What Was Just Done (Phase 2 — 2026-05-06)

**Phase 2 — AI Pipeline (KB → Doc → Script):**
- Added `TEST_SCRIPT_GEN_PROMPT` + `FEATURE_DOC_PROMPT` to `ai/prompts/prompt_templates.py`
- Built `ai/skills/test_script_gen.py` — `TestScriptGenSkill`: converts test case docs to runnable pytest code, domain-specific conventions (api/web/mobile/security), strips markdown fences from model output
- Built `ai/pipeline/orchestrator.py` — `TestPipelineOrchestrator`: full KB → doc → script pipeline with CLI  
  - `python -m ai.pipeline.orchestrator --feature booking --domain api`
  - `python -m ai.pipeline.orchestrator --increment feature_001.yaml --domain api`
  - `python -m ai.pipeline.orchestrator --doc docs/test_cases/api/booking.md --domain api --feature booking`
  - Updates `framework_knowledge/kb_increments_log.yaml` automatically

## What Was Done Before (Phase 0 + Phase 1 — 2026-05-06)

**Phase 0 — Stability fixes:**
- Removed hardcoded ReportPortal API key from `pytest.ini` → reads from `RP_API_KEY` env var via `conftest.py:pytest_configure`
- Added `timeout` to Mistral cloud API calls (`utils/constants.py:MISTRAL_CLOUD_TIMEOUT_S`)
- Added content-type guard in `api/rest_client.py:_validate_schema` before calling `.json()`
- Fixed `lru_cache` on instance methods in `kb_loader.py` → replaced with instance `_cache` dict (no memory leak)
- Added locale fallback logging in `utils/locator_manager.py`
- Extracted AI client factory into `utils/ai_factory.py`
- Created `utils/constants.py` — all magic numbers live here
- `pages/base_page.py` now uses `LOCATOR_HEAL_TIMEOUT_MS` constant

**Phase 1 — Tracking system:**
- Created `framework_knowledge/` with this file, architecture.md, conventions.md
- Created `framework_knowledge/progress/backlog.yaml` and `completed.yaml`
- Created `framework_knowledge/decisions/` for ADRs
- Created `ai/knowledge_base/increments/` for feature drop YAMLs

---

## Next Immediate Action

**Phase 4 — Security: OWASP-aligned test suite**

Files to create:
- `tests/security/test_auth_security.py` — auth bypass, token validation
- `tests/security/test_injection.py` — SQL injection, XSS (known issue: additionalneeds field unsanitized)
- `tests/security/test_idor.py` — access other user's booking IDs
- `utils/security_assertions.py` — shared security assertions

See `framework_knowledge/progress/backlog.yaml` for details.

---

## Key Architectural Decisions

- AI client: Mistral (cloud or local Ollama). Abstracted behind `AIClient` base. See `ADR-002`.
- KB structure: YAML files in `ai/knowledge_base/base/` (stable) + `ai/knowledge_base/increments/` (feature drops). See `ADR-001`.
- Schema location: `schemas/rest_schemas/` is canonical. `api/schemas/` is dead code — do not use.
- All magic numbers: `utils/constants.py`
- RP API key: env var `RP_API_KEY` only, never committed.

---

## Where Things Live

```
ai/knowledge_base/base/           Stable product KB (application, api_specs, ui_pages, product_knowledge)
ai/knowledge_base/increments/     Feature drop YAMLs (feature_001_booking_v2.yaml, etc.)
ai/knowledge_base/kb_loader.py    Loads base + increments, formats context for prompts
ai/clients/mistral_client.py      LLM client (cloud + local Ollama)
ai/skills/                        AI-powered skills (doc gen, script gen, self-healing)
ai/pipeline/orchestrator.py       [NOT YET BUILT] end-to-end KB → doc → script
api/rest_client.py                REST API test client
api/graphql_client.py             GraphQL test client
pages/base_page.py                Base POM with self-healing locators
utils/constants.py                All magic numbers
utils/ai_factory.py               AI client instantiation (do not duplicate in conftest)
framework_knowledge/              This tracking system
docs/test_cases/                  Generated test case docs (output)
tests/                            Generated + hand-written test scripts
```

---

## Conventions (quick ref)

- Test files: `tests/{domain}/test_{feature_name}.py`
- KB increments: `ai/knowledge_base/increments/feature_{NNN}_{name}.yaml`
- Generated docs: `docs/test_cases/{domain}/{feature_name}.md`
- Locator files: `locators/{platform}/{page_name}.json` with `primary` + `alternatives`
- Config per env: `config/env_{qa|staging|prod}.yaml`
- All timeouts/magic numbers: define in `utils/constants.py`, import everywhere

See `framework_knowledge/conventions.md` for full detail.

---

## Do Not

- Do not hardcode API keys or tokens anywhere — use env vars
- Do not add `@lru_cache` to instance methods — use `self._cache` dict
- Do not create files under `api/schemas/` — that directory is dead code
- Do not duplicate AI factory logic — use `utils/ai_factory.py`
- Do not add magic numbers inline — add to `utils/constants.py`

## AI Doc Generation — Anti-Hallucination Rules

These rules exist to prevent the LLM from inventing fields or behaviors not present in the AUT.

1. **Only test KB-listed fields.** If a field is not in the KB context passed to the prompt, it does not exist on that form. Do not add it.
2. **Do not use training-data knowledge of the AUT.** OrangeHRM, Restful-Booker, and other known apps exist in the LLM's training data. That knowledge is often wrong or version-mismatched. KB context is the only truth.
3. **Add Employee ≠ Employee Profile.** OrangeHRM's Add Employee form has 4 fields only: First Name, Last Name, Middle Name, Employee ID. Date of Birth, Gender, Department, Job Title are on separate profile tabs — NOT on the add form.
4. **Use real credentials.** OrangeHRM demo: `Admin / admin123`. Do not substitute generic placeholders.
5. **Prompt templates enforce this** via STRICT RULES blocks — if modifying prompts, preserve those blocks.
6. **product_knowledge.yaml has `add_employee_form_fields_only`** — this is the canonical field list for the Add Employee form. Update it when the AUT changes.
