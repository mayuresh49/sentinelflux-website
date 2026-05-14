# API Test Generation Guide

This guide explains how to generate API test documentation using the SentinelFlux AI and Knowledge Base integration.

## Setup

1. Ensure the repository root is the working directory:
   ```bash
   cd /path/to/sentinelflux-framework
   ```
2. Activate the Python environment and install dependencies:
   ```bash
   source .venv_ai/bin/activate
   pip install -r requirements.txt
   playwright install
   ```
3. Confirm AI is enabled in `config/env_qa.yaml` under `sentinelflux.ai`.
4. Provide a valid `api_key` for cloud Mistral, or use `--local` for a local Ollama instance.

## Generate REST API documentation

```bash
python3 -m ai.generate_api_test_doc \
  --endpoint /booking \
  --method POST \
  --output docs/test_cases/api/booking_create_tests.md
```

## Generate GraphQL documentation

```bash
python3 -m ai.generate_api_test_doc \
  --endpoint countries_list \
  --method QUERY \
  --output docs/test_cases/api/countries_query_tests.md
```

## Output

- Generated docs are saved under `docs/test_cases/api/`
- Each file contains:
  - test scenario descriptions
  - positive and negative cases
  - expected response behavior
  - validation and edge cases

## Notes

- The script uses `ai/knowledge_base/api_specs.yaml` to resolve endpoint metadata.
- If the endpoint is not found in the KB, the script will fall back to the provided `--description`.
- Use `PYTHONPATH=.` if module imports fail:
  ```bash
  PYTHONPATH=. python3 ai/generate_api_test_doc.py --endpoint /booking --method POST
  ```
