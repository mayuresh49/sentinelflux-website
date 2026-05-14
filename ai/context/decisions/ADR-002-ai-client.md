# ADR-002: AI Client Abstraction — Mistral with Local Fallback

Date: 2026-05-06  
Status: Accepted

## Decision

Use Mistral as default AI provider. Support local Ollama as a zero-cost fallback. Abstract behind `AIClient` base class. Instantiate only via `utils/ai_factory.py`.

## Context

Owner is budget-constrained on individual Claude plan. For high-volume test generation (many features, large KB), cloud Mistral costs can add up. Local Ollama (free) trades latency for cost.

## Consequences

- `ai/clients/base_client.py` defines the contract (`generate()`, `chat()`)
- `ai/clients/mistral_client.py` implements both cloud and local modes
- Adding a new provider (OpenAI, Gemini) = new class in `ai/clients/`
- `conftest.py` never instantiates clients directly — always via `utils/ai_factory.py`
- API keys in env vars, model selection in `config/env_*.yaml`

## Trade-offs

- Local Ollama model quality (Qwen 2.5 Coder) is lower than cloud Mistral/GPT-4
- Use local for bulk generation, cloud for final review pass
