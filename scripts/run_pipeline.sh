#!/bin/bash
# SentinelFlux AI Pipeline Runner
# Usage: ./run_pipeline.sh <project> <feature> <domain> [doc-model] [script-model] [tc-prefix] [tc-start] [source]
# Domains: api | web | mobile | security | a11y
# source: path to OpenAPI spec (.yaml/.json), service code file (.py/.ts/etc), or URL
#
# Exploration (web domain only) — pass via env vars before the command:
#   SF_EXPLORE=1              Enable AppExplorerAgent (doc-review → explore → script-gen)
#   SF_BASE_URL=http://...    App root URL
#   SF_LOGIN_URL=/auth/login  Login page path
#   SF_EXPLORE_PAGES=/p1,/p2  Comma-separated pages to visit (auto-extracted from doc if omitted)
#   SF_EXPLORE_USER / SF_EXPLORE_PASS  Credentials (never pass as positional args)
#
# Examples:
#   ./run_pipeline.sh orangehrm login web
#   ./run_pipeline.sh orangehrm booking api _ _ RB-API 1 products/restfulbooker/openapi.yaml
#   ./run_pipeline.sh orangehrm recruitment web qwen2.5-coder:14b-instruct-q4_K_M qwen2.5-coder:14b-instruct-q4_K_M OH-WEB 58
#   ./run_pipeline.sh orangehrm security_api security _ _ OH-SEC 1
#   SF_EXPLORE=1 SF_BASE_URL=http://localhost SF_LOGIN_URL=/web/index.php/auth/login \
#     SF_EXPLORE_USER=Kris.Chapman SF_EXPLORE_PASS=Admin123 \
#     ./run_pipeline.sh orangehrm ess web _ _ OH-WEB 129

set -e

PROJECT="${1:-orangehrm}"
FEATURE="${2:-login}"
DOMAIN="${3:-web}"
DOC_MODEL="${4:-qwen2.5-coder:14b-instruct-q4_K_M}"
SCRIPT_MODEL="${5:-qwen2.5-coder:14b-instruct-q4_K_M}"
TC_PREFIX="${6:-}"
TC_START="${7:-1}"
SOURCE="${8:-}"

# Exploration — driven by env vars (never positional to keep credentials out of shell history)
EXPLORE="${SF_EXPLORE:-}"
EXPLORE_BASE_URL="${SF_BASE_URL:-}"
EXPLORE_LOGIN_URL="${SF_LOGIN_URL:-}"
EXPLORE_PAGES="${SF_EXPLORE_PAGES:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

# Prefer venv Python over system python3
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
  PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3.11 > /dev/null 2>&1; then
  PYTHON="$(command -v python3.11)"
else
  PYTHON="$(command -v python3)"
fi

EXAMPLE_DIR="products/$PROJECT"
KB_DIR="products/$PROJECT/ai/knowledge_base"

if [ ! -d "$EXAMPLE_DIR" ]; then
  echo "ERROR: Example directory not found: $EXAMPLE_DIR"
  echo "Available projects: $(ls products/)"
  exit 1
fi

if [ ! -d "$KB_DIR" ]; then
  echo "ERROR: KB directory not found: $KB_DIR"
  echo "Available KBs: $(ls products/ | xargs -I{} sh -c '[ -d products/{}/ai/knowledge_base ] && echo {}')"
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
[ -n "$EXPLORE" ] && echo "Explore   : YES (base: $EXPLORE_BASE_URL)"
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

EXPLORE_FLAGS=""
if [ -n "$EXPLORE" ]; then
  if [ -z "$EXPLORE_BASE_URL" ]; then
    echo "ERROR: SF_EXPLORE=1 requires SF_BASE_URL to be set."
    exit 1
  fi
  EXPLORE_FLAGS="--explore --base-url $EXPLORE_BASE_URL"
  [ -n "$EXPLORE_LOGIN_URL" ] && EXPLORE_FLAGS="$EXPLORE_FLAGS --login-url $EXPLORE_LOGIN_URL"
  [ -n "$EXPLORE_PAGES" ] && EXPLORE_FLAGS="$EXPLORE_FLAGS --explore-pages $EXPLORE_PAGES"
  # SF_EXPLORE_USER / SF_EXPLORE_PASS are read directly by the orchestrator from env
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
  $SOURCE_FLAG \
  $EXPLORE_FLAGS

echo ""
echo "=== Done ==="
echo "Doc   : $EXAMPLE_DIR/docs/test_cases/$DOMAIN/$FEATURE.md"
echo "Script: $EXAMPLE_DIR/tests/$DOMAIN/test_$FEATURE.py"
