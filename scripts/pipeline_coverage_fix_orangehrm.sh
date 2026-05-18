#!/usr/bin/env bash
# Fix OrangeHRM doc coverage 67% → >90%
# Runs full pipeline (DocGen → DocReview → ScriptGen → ScriptReview) for 4 undocumented scripts.
# WARNING: existing scripts for these features will be overwritten by ScriptGen.

set -e
VENV=".venv/bin/python3"
PRODUCT="orangehrm"
OUTPUT_BASE="products/$PRODUCT"
KB_PROJECT="$PRODUCT"

run_pipeline() {
  local feature=$1
  local domain=$2
  local prefix=$3
  echo ""
  echo "================================================================"
  echo "PIPELINE: $feature | domain=$domain | prefix=$prefix"
  echo "================================================================"
  $VENV -m ai.pipeline.orchestrator \
    --feature "$feature" \
    --domain "$domain" \
    --project "$KB_PROJECT" \
    --output-base "$OUTPUT_BASE" \
    --tc-prefix "$prefix" \
    --local
}

# 1. security_api — api domain (overwrites tests/api/test_security_api.py)
run_pipeline "security_api" "api" "OH-API"

# 2. security_web — web domain (overwrites tests/web/test_security_web.py)
run_pipeline "security_web" "web" "OH-WEB"

# 3. leave — web domain (overwrites tests/web/test_leave.py)
run_pipeline "leave" "web" "OH-WEB"

# 4. login_mobile — mobile domain (overwrites tests/mobile/test_login_mobile.py)
run_pipeline "login_mobile" "mobile" "OH-MOB"

echo ""
echo "================================================================"
echo "ALL PIPELINES COMPLETE"
echo "Verifying doc coverage..."
echo "================================================================"
$VENV -c "
from pathlib import Path
product = 'orangehrm'
base = Path('products') / product
scripts = {py.stem.removeprefix('test_') for py in (base/'tests').rglob('test_*.py') if py.relative_to(base/'tests').parts[0] not in {'vapt'}}
docs = {md.stem for md in (base/'docs'/'test_cases').rglob('*.md') if md.stem != 'README'}
documented = scripts & docs
undocumented = scripts - docs
cov = round(len(documented)/len(scripts)*100) if scripts else 0
print(f'Scripts: {len(scripts)}, Documented: {len(documented)}, Coverage: {cov}%')
if undocumented:
    print(f'Still undocumented: {sorted(undocumented)}')
else:
    print('All scripts have matching docs!')
"
