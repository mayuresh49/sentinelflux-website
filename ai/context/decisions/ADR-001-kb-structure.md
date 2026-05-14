# ADR-001: Knowledge Base Structure — Base + Increments

Date: 2026-05-06  
Status: Accepted

## Decision

Split KB into `base/` (stable product knowledge) and `increments/` (per-feature drops).

## Context

The AI pipeline needs product knowledge to generate test cases. This knowledge has two lifetimes:
- **Stable**: app structure, API specs, UI pages, personas, business rules — changes rarely
- **Incremental**: new feature specs that arrive as product evolves

Originally, all KB was in flat files in `ai/knowledge_base/`. This made it hard to add feature knowledge without risk of corrupting stable context.

## Consequences

- New features → drop a `feature_NNN_name.yaml` into `increments/` only
- `kb_loader.py` merges base + all increments at load time
- `kb_increments_log.yaml` tracks which increments have been processed into docs/scripts
- Stable KB files are rarely touched after initial setup
