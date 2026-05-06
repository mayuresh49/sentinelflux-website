#!/bin/bash
# SentinelFlux AI Pipeline Runner
# Usage: ./run_pipeline.sh <project> <feature> <domain> [model]
# Example: ./run_pipeline.sh orangehrm login web
#          ./run_pipeline.sh orangehrm pim_employee web qwen2.5-coder:14b-instruct-q4_K_M

set -e

PROJECT="${1:-orangehrm}"
FEATURE="${2:-login}"
DOMAIN="${3:-web}"
DOC_MODEL="${4:-mistral:7b-instruct-v0.3-q4_K_M}"
SCRIPT_MODEL="${5:-qwen2.5-coder:14b-instruct-q4_K_M}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "=== SentinelFlux Pipeline ==="
echo "Project : $PROJECT"
echo "Feature : $FEATURE"
echo "Domain  : $DOMAIN"
echo "DocModel: $DOC_MODEL"
echo "ScrModel: $SCRIPT_MODEL"
echo ""

# --- Memory check ---
FREE_MB=$(python3 -c "
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

# --- Run pipeline ---
echo ">>> Generating: $FEATURE ($DOMAIN) ..."
python3 -m ai.pipeline.orchestrator \
  --feature "$FEATURE" \
  --domain "$DOMAIN" \
  --project "$PROJECT" \
  --doc-model "$DOC_MODEL" \
  --script-model "$SCRIPT_MODEL"

echo ""
echo "=== Done ==="
echo "Doc   : docs/test_cases/$DOMAIN/$FEATURE.md"
echo "Script: tests/$DOMAIN/test_$FEATURE.py"
