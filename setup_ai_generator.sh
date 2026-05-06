#!/bin/bash
# Setup and run the automated test case generator
# Prerequisites: Local LLM running at http://localhost:11434

set -e  # Exit on error

echo "=== Automated Test Case Generator Setup ==="
echo ""

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# Create virtual environment if not exists
if [ ! -d ".venv_ai" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv_ai
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv_ai/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip -q

# Install required packages
echo "Installing required packages..."
python -m pip install -q \
    browser-use \
    langchain-ollama \
    langchain-core \
    playwight

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the test case generator:"
echo "  source .venv_ai/bin/activate"
echo "  python ai/knowledge_base/auto_test_generator.py"
echo ""
echo "Prerequisites:"
echo "  ✓ Local LLM running at http://localhost:11434"
echo "  ✓ qwen2.5-coder:14b-instruct-q4_K_M model available"
echo ""
