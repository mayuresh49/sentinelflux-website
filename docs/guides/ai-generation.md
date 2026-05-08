# AI Test Generation

SentinelFlux can generate test case documents and pytest scripts from a knowledge base using Mistral.

## Pipeline

```
Knowledge base (YAML)  →  Test case doc (Markdown)  →  pytest script (Python)
```

## Knowledge base

Drop feature YAML files in `ai/knowledge_base/increments/`. Each file describes a feature, its scenarios, and expected outcomes.

See `docs/KNOWLEDGE_BASE_GUIDE.md` for the full schema.

## Generate a test case doc

```bash
sentinelflux generate --output docs/test_cases/web/login.md
```

Or for an API endpoint:

```bash
sentinelflux generate --endpoint /users --method POST --output docs/test_cases/api/create_user.md
```

## Generate doc + script in one step

```bash
sentinelflux generate --output docs/test_cases/web/login.md --script
```

The `--script` flag also runs the script generator and writes the pytest file to `tests/`.

## Configuration

```yaml
# config/env_qa.yaml
sentinelflux:
  ai:
    enabled: true
    mode: mistral
    api_key: "your-mistral-api-key"
```

Or set `MISTRAL_API_KEY` environment variable — takes precedence over the config file value.

## Generated test conventions

- Web tests use `@pytest.mark.web` and take a `page` fixture
- Page object methods are decorated with `@step_method` — self-healing is automatic
- API tests use `@pytest.mark.api` and take a `rest_client` or `graphql_client` fixture
