# AI Skills Documentation

This document explains the AI skills layer in the SentinelFlux framework, including the main skill classes, how they connect to the AI client, and how they use the knowledge base.

## Purpose

- Describe the `ai/skills/` modules.
- Show where AI prompts are defined.
- Explain recommended usage patterns and entry points.

## Key modules

### `ai/skills/test_case_doc_kb.py`

- Main skill for generating test documentation using KB context.
- Uses `TestCaseDocumentationSkill(client, kb_loader)`.
- Supports:
  - `generate_document(page_url, description)`
  - `generate_api_test_document(endpoint, method, description, api_type)`

### `ai/skills/test_case_doc.py`

- Original UI test documentation skill.
- Useful as a reference for prompt structure and document generation patterns.

### `ai/skills/self_healing.py`

- Example AI-assisted locator healing workflow.
- Uses `MistralClient` and prompt templates to suggest locator fixes.

## Prompt templates

- Prompt templates are defined in `ai/prompts/prompt_templates.py`.
- These templates are used by AI skills to convert KB context into structured test documentation.

## How to run

Use the repository root as the working directory:

```bash
cd /path/to/sentinelflux-framework
python3 -m ai.generate_test_case_doc --config config/env_qa.yaml --output docs/test_cases/generated_test_case_doc.md
python3 -m ai.generate_api_test_doc --endpoint /booking --method POST --output docs/test_cases/api/booking_create_tests.md
```

If local package imports fail, run:

```bash
PYTHONPATH=. python3 ai/generate_test_case_doc.py --config config/env_qa.yaml --output docs/test_cases/generated_test_case_doc.md
```

## Notes

- `MistralClient` is defined in `ai/clients/mistral_client.py`.
- `KnowledgeBaseLoader` is defined in `ai/knowledge_base/kb_loader.py`.
- Treat generated markdown as source files that can be version controlled and reviewed.
