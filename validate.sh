#!/bin/bash
# SentinelFlux — Validate all test runs and optionally publish.
#
# Usage:
#   ./validate.sh                   # run all validation steps
#   ./validate.sh --skip-web        # skip browser (Playwright) tests
#   ./validate.sh --skip-pipeline   # skip Qwen/Ollama generation step
#   ./validate.sh --skip-docs       # skip mkdocs gh-deploy
#   ./validate.sh --testpypi        # upload build to TestPyPI (needs TESTPYPI_TOKEN)
#   ./validate.sh --publish         # tag v0.1.0 and push tags (triggers PyPI workflow)
#
# Environment variables:
#   TESTPYPI_TOKEN   — API token for TestPyPI upload (only needed with --testpypi)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Flags ────────────────────────────────────────────────────────────────────
SKIP_WEB=false
SKIP_PIPELINE=false
SKIP_DOCS=false
DO_TESTPYPI=false
DO_PUBLISH=false

for arg in "$@"; do
  case $arg in
    --skip-web)      SKIP_WEB=true ;;
    --skip-pipeline) SKIP_PIPELINE=true ;;
    --skip-docs)     SKIP_DOCS=true ;;
    --testpypi)      DO_TESTPYPI=true ;;
    --publish)       DO_PUBLISH=true ;;
  esac
done

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ PASS${NC}  $1"; }
fail() { echo -e "  ${RED}✗ FAIL${NC}  $1"; }
skip() { echo -e "  ${YELLOW}- SKIP${NC}  $1"; }
header() {
  echo ""
  echo -e "${BOLD}${CYAN}── $1 ──────────────────────────────────────────────${NC}"
}

# ── Step runner ───────────────────────────────────────────────────────────────
RESULTS=()   # "PASS:name" | "FAIL:name" | "SKIP:name"

run_step() {
  local name="$1"
  local dir="$2"
  shift 2
  header "$name"
  local orig_dir
  orig_dir="$(pwd)"
  [ -n "$dir" ] && cd "$dir"
  if "$@"; then
    pass "$name"
    RESULTS+=("PASS:$name")
  else
    fail "$name"
    RESULTS+=("FAIL:$name")
  fi
  cd "$orig_dir"
}

skip_step() {
  local name="$1"
  skip "$name"
  RESULTS+=("SKIP:$name")
}

# ── Step definitions ──────────────────────────────────────────────────────────

# 1. Restful Booker — API
run_step "Restful Booker API" "examples/restfulbooker" \
  python3 -m pytest tests/api/ -m api -q --tb=short

# 2. Restful Booker — Web
if $SKIP_WEB; then
  skip_step "Restful Booker Web"
else
  run_step "Restful Booker Web" "examples/restfulbooker" \
    python3 -m pytest tests/web/ -m web -n 4 --tb=short
fi

# 3. OrangeHRM — API
run_step "OrangeHRM API" "examples/orangehrm" \
  python3 -m pytest tests/api/ -m api -q --tb=short

# 4. OrangeHRM — Web
if $SKIP_WEB; then
  skip_step "OrangeHRM Web"
else
  run_step "OrangeHRM Web" "examples/orangehrm" \
    python3 -m pytest tests/web/ -m web -n 4 --tb=short
fi

# 5. Qwen pipeline (end-to-end generation)
if $SKIP_PIPELINE; then
  skip_step "Qwen pipeline"
else
  header "Qwen pipeline"
  if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    if bash run_pipeline.sh restfulbooker booking api; then
      pass "Qwen pipeline"
      RESULTS+=("PASS:Qwen pipeline")
    else
      fail "Qwen pipeline"
      RESULTS+=("FAIL:Qwen pipeline")
    fi
  else
    echo -e "  ${YELLOW}Ollama not running — skipping pipeline step${NC}"
    RESULTS+=("SKIP:Qwen pipeline (Ollama offline)")
  fi
fi

# 6. Build package
header "Build package"
if python3 -m build --quiet; then
  pass "Build package"
  RESULTS+=("PASS:Build package")
  WHEEL=$(ls dist/*.whl 2>/dev/null | tail -1)
  [ -n "$WHEEL" ] && echo -e "  ${CYAN}→ $WHEEL${NC}"
else
  fail "Build package"
  RESULTS+=("FAIL:Build package")
fi

# 7. TestPyPI upload
if $DO_TESTPYPI; then
  header "TestPyPI upload"
  if [ -z "$TESTPYPI_TOKEN" ]; then
    echo -e "  ${YELLOW}TESTPYPI_TOKEN not set — skipping upload${NC}"
    RESULTS+=("SKIP:TestPyPI upload (no token)")
  else
    if python3 -m twine upload \
        --repository-url https://test.pypi.org/legacy/ \
        --username __token__ \
        --password "$TESTPYPI_TOKEN" \
        dist/*; then
      pass "TestPyPI upload"
      RESULTS+=("PASS:TestPyPI upload")
    else
      fail "TestPyPI upload"
      RESULTS+=("FAIL:TestPyPI upload")
    fi
  fi
else
  skip_step "TestPyPI upload (use --testpypi to enable)"
fi

# 8. Docs deploy
if $SKIP_DOCS; then
  skip_step "Docs deploy"
else
  header "Docs deploy (mkdocs gh-deploy)"
  if command -v mkdocs > /dev/null 2>&1; then
    if mkdocs gh-deploy --quiet; then
      pass "Docs deploy"
      RESULTS+=("PASS:Docs deploy")
    else
      fail "Docs deploy"
      RESULTS+=("FAIL:Docs deploy")
    fi
  else
    echo -e "  ${YELLOW}mkdocs not installed — skipping (pip install mkdocs-material)${NC}"
    RESULTS+=("SKIP:Docs deploy (mkdocs not installed)")
  fi
fi

# 9. Tag and publish (safety gate — explicit --publish only)
if $DO_PUBLISH; then
  header "Tag v0.1.0 + push"
  FAIL_COUNT=$(printf '%s\n' "${RESULTS[@]}" | grep -c "^FAIL:" || true)
  if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "  ${RED}Skipping tag — $FAIL_COUNT step(s) failed above. Fix failures first.${NC}"
    RESULTS+=("SKIP:Tag v0.1.0 (failures present)")
  elif git tag v0.1.0 2>/dev/null && git push origin --tags; then
    pass "Tag v0.1.0 pushed — PyPI workflow triggered"
    RESULTS+=("PASS:Tag v0.1.0")
  else
    echo -e "  ${YELLOW}Tag v0.1.0 may already exist — check git tag -l${NC}"
    RESULTS+=("SKIP:Tag v0.1.0 (already exists?)")
  fi
else
  skip_step "Tag v0.1.0 (use --publish to enable)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Validation Summary${NC}"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}"
for entry in "${RESULTS[@]}"; do
  status="${entry%%:*}"
  name="${entry#*:}"
  case $status in
    PASS) echo -e "  ${GREEN}✓${NC}  $name" ;;
    FAIL) echo -e "  ${RED}✗${NC}  $name" ;;
    SKIP) echo -e "  ${YELLOW}-${NC}  $name" ;;
  esac
done
echo ""

FAIL_COUNT=$(printf '%s\n' "${RESULTS[@]}" | grep -c "^FAIL:" || true)
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo -e "  ${GREEN}${BOLD}All checks passed.${NC}"
  exit 0
else
  echo -e "  ${RED}${BOLD}$FAIL_COUNT check(s) failed.${NC}"
  exit 1
fi
