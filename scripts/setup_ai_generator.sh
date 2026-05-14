#!/bin/bash
# SentinelFlux AI setup — installs framework + AI extras, verifies Ollama + Qwen model
# Run once before using run_pipeline.sh or `sentinelflux generate`

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OLLAMA_URL="http://localhost:11434"
DEFAULT_MODEL="qwen2.5-coder:14b-instruct-q4_K_M"
MODEL="${1:-$DEFAULT_MODEL}"

echo ""
echo "=== SentinelFlux AI Setup ==="
echo ""

# ── 1. Install sentinelflux with AI extras ────────────────────────────────
echo "Installing sentinelflux[ai]..."
pip install -e ".[ai]" -q
echo "  done"
echo ""

# ── 2. Ollama health check ────────────────────────────────────────────────
echo "Checking Ollama at $OLLAMA_URL ..."
if ! curl -sf "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
  echo ""
  echo "ERROR: Ollama is not running."
  echo "  Start it with:  ollama serve"
  echo "  Install guide:  https://ollama.com"
  exit 1
fi
echo "  Ollama OK"
echo ""

# ── 3. Check model availability ───────────────────────────────────────────
echo "Checking model: $MODEL ..."
TAGS=$(curl -sf "$OLLAMA_URL/api/tags" | python3 -c "
import sys, json
data = json.load(sys.stdin)
names = [m['name'] for m in data.get('models', [])]
print('\n'.join(names))
" 2>/dev/null || echo "")

if echo "$TAGS" | grep -qF "$MODEL"; then
  echo "  Model found: $MODEL"
else
  echo "  Model not found locally. Pulling $MODEL ..."
  echo "  (this may take several minutes on first run)"
  ollama pull "$MODEL"
  echo "  Pull complete"
fi
echo ""

# ── 4. Smoke test — verify sentinelflux CLI is accessible ─────────────────
echo "Verifying sentinelflux CLI..."
if sentinelflux --help > /dev/null 2>&1; then
  echo "  sentinelflux CLI OK"
else
  echo "  WARNING: sentinelflux CLI not found in PATH."
  echo "  Try: pip install -e . --quiet"
fi
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Quick start:"
echo "  # Generate test case doc + script for a product"
echo "  ./run_pipeline.sh orangehrm login web"
echo "  ./run_pipeline.sh restfulbooker booking api"
echo ""
echo "  # Or use the CLI directly:"
echo "  sentinelflux generate \\"
echo "      --kb-dir ai/knowledge_base/orangehrm \\"
echo "      --output products/orangehrm/docs/test_cases/web/login.md \\"
echo "      --script"
echo ""
echo "  Model in use: $MODEL"
echo "  To use a different model: ./setup_ai_generator.sh <model-name>"
echo ""
