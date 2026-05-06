# Web Test Generation Guide

This guide explains how to generate web UI test documentation using the SentinelFlux AI and Knowledge Base integration.

## Setup

1. Ensure the repository root is the working directory:
   ```bash
   cd /Users/mayureshkulkarni/Documents/Work/sentinelflux-framework
   ```
2. Activate the Python environment and install dependencies:
   ```bash
   source .venv_ai/bin/activate
   pip install -r requirements.txt
   playwright install
   ```
3. Confirm AI is enabled in `config/env_qa.yaml` under `sentinelflux.ai`.
4. Provide a valid `api_key` for cloud Mistral, or use `--local` for a local Ollama instance.

## Generate Web UI documentation

```bash
python3 -m ai.generate_test_case_doc \
  --page-url "https://app.com/booking" \
  --description "Booking form with validation" \
  --output docs/test_cases/web/booking_form_tests.md
```

## Output

- Generated docs are saved under `docs/test_cases/web/`
- Each file contains:
  - page and form description
  - positive and negative user flows
  - validation rules and edge cases
  - expected field behavior

## Notes

- The script uses `ai/knowledge_base/ui_pages.yaml` and other KB assets to provide context.
- Use `PYTHONPATH=.` if module imports fail:
  ```bash
  PYTHONPATH=. python3 ai/generate_test_case_doc.py --page-url "https://app.com/booking" --output docs/test_cases/web/booking_form_tests.md
  ```
