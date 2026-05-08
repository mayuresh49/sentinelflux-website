# Environment Profiles

SentinelFlux supports multiple environment profiles via YAML files in `config/`.

## Selecting an environment

```bash
sentinelflux run --env qa        # default
sentinelflux run --env staging
sentinelflux run --env prod
```

Or directly with pytest:

```bash
python3 -m pytest --env=staging
```

## Adding a new environment

Copy `config/env_template.yaml` to `config/env_<name>.yaml` and fill in the values:

```bash
cp config/env_template.yaml config/env_staging.yaml
```

## Keeping secrets out of config

Use environment variables for secrets — they are never committed:

```bash
export RP_API_KEY=your_rp_key
export MISTRAL_API_KEY=your_mistral_key
```

The framework reads these at runtime and merges them with the YAML config. The `api_key` field in YAML is a fallback for local development only.
