#!/bin/bash
# SentinelFlux AI Pipeline Runner
# Usage: ./run_pipeline.sh <project> <feature> <domain> [doc-model] [script-model] [tc-prefix] [tc-start] [source]
# Domains: api | web | mobile | security | a11y
# source: path to OpenAPI spec (.yaml/.json), service code file (.py/.ts/etc), or URL
# Example: ./run_pipeline.sh orangehrm login web
#          ./run_pipeline.sh orangehrm booking api _ _ RB-API 1 products/restfulbooker/openapi.yaml
#          ./run_pipeline.sh orangehrm recruitment web qwen2.5-coder:14b-instruct-q4_K_M qwen2.5-coder:14b-instruct-q4_K_M OH-WEB 58
#          ./run_pipeline.sh orangehrm security_api security _ _ OH-SEC 1

set -e

PROJECT="${1:-orangehrm}"
FEATURE="${2:-login}"
DOMAIN="${3:-web}"
DOC_MODEL="${4:-qwen2.5-coder:14b-instruct-q4_K_M}"
SCRIPT_MODEL="${5:-qwen2.5-coder:14b-instruct-q4_K_M}"
TC_PREFIX="${6:-}"
TC_START="${7:-1}"
SOURCE="${8:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer venv Python over system python3
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3.11 > /dev/null 2>&1; then
  PYTHON="$(command -v python3.11)"
else
  PYTHON="$(command -v python3)"
fi

EXAMPLE_DIR="products/$PROJECT"
KB_DIR="ai/knowledge_base/$PROJECT"

if [ ! -d "$EXAMPLE_DIR" ]; then
  echo "ERROR: Example directory not found: $EXAMPLE_DIR"
  echo "Available projects: $(ls products/)"
  exit 1
fi

if [ ! -d "$KB_DIR" ]; then
  echo "ERROR: KB directory not found: $KB_DIR"
  echo "Available KBs: $(ls ai/knowledge_base/ | grep -v '\.yaml$' | grep -v '^increments$')"
  exit 1
fi

echo ""
echo "=== SentinelFlux Pipeline ==="
echo "Project   : $PROJECT"
echo "Feature   : $FEATURE"
echo "Domain    : $DOMAIN"
echo "DocModel  : $DOC_MODEL"
echo "ScrModel  : $SCRIPT_MODEL"
echo "OutputBase: $EXAMPLE_DIR"
[ -n "$TC_PREFIX" ] && echo "TC Prefix : $TC_PREFIX (start: $TC_START)"
[ -n "$SOURCE" ] && echo "Source    : $SOURCE"
echo ""

# --- Memory check ---
FREE_MB=$("$PYTHON" -c "
import subprocess
o=subprocess.check_output(['vm_stat']).decode()
free=int([l for l in o.split('\n') if 'Pages free' in l][0].split(':')[1].strip().rstrip('.'))*4096//1024//1024
print(free)
" 2>/dev/null || echo 0)

echo "Free RAM: ${FREE_MB} MB"
if [ "$FREE_MB" -lt 5000 ]; then
  echo ""
  echo "WARNING: Less than 5 GB free. Models may fail to load."
  echo "Close other applications and retry."
  echo ""
fi

# --- Ollama health check ---
echo "Checking Ollama..."
OLLAMA_RESP=$(curl -s http://localhost:11434/api/tags 2>/dev/null || echo "")
if [ -z "$OLLAMA_RESP" ]; then
  echo "ERROR: Ollama not responding at localhost:11434. Start Ollama first."
  exit 1
fi
echo "Ollama OK"
echo ""

# --- Guard: skip script generation if hand-written test already exists ---
HAND_WRITTEN_TEST="$EXAMPLE_DIR/tests/$DOMAIN/test_$FEATURE.py"
SKIP_SCRIPT_FLAG=""
if [ -f "$HAND_WRITTEN_TEST" ]; then
  echo "Hand-written test exists: $HAND_WRITTEN_TEST"
  echo "Script generation skipped — only regenerating test case doc."
  SKIP_SCRIPT_FLAG="--skip-script"
fi

# --- Build optional flags ---
TC_FLAGS=""
if [ -n "$TC_PREFIX" ]; then
  TC_FLAGS="--tc-prefix $TC_PREFIX --tc-start $TC_START"
fi
SOURCE_FLAG=""
if [ -n "$SOURCE" ]; then
  SOURCE_FLAG="--source $SOURCE"
fi

# --- Run pipeline ---
echo ">>> Generating: $FEATURE ($DOMAIN) ..."
"$PYTHON" -m ai.pipeline.orchestrator \
  --feature "$FEATURE" \
  --domain "$DOMAIN" \
  --project "$PROJECT" \
  --doc-model "$DOC_MODEL" \
  --script-model "$SCRIPT_MODEL" \
  --output-base "$EXAMPLE_DIR" \
  $SKIP_SCRIPT_FLAG \
  $TC_FLAGS \
  $SOURCE_FLAG

echo ""
echo "=== Done ==="
echo "Doc   : $EXAMPLE_DIR/docs/test_cases/$DOMAIN/$FEATURE.md"
echo "Script: $EXAMPLE_DIR/tests/$DOMAIN/test_$FEATURE.py"
