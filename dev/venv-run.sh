#!/bin/bash
# FILE: dev/venv-run.sh
# Universal wrapper to run commands in the virtual environment
# Usage: dev/venv-run.sh python script.py
#        dev/venv-run.sh python -m pytest tests/

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_ROOT"

# Find and activate virtual environment
VENV_ACTIVATED=false

if [ -d ".venv" ]; then
    source .venv/bin/activate
    VENV_ACTIVATED=true
elif [ -d "venv" ]; then
    source venv/bin/activate
    VENV_ACTIVATED=true
elif [ -d "env" ]; then
    source env/bin/activate
    VENV_ACTIVATED=true
fi

# If no venv found, check if we're already in one
if [ "$VENV_ACTIVATED" = false ] && [ -n "$VIRTUAL_ENV" ]; then
    VENV_ACTIVATED=true
fi

# Warn if no virtual environment is active
if [ "$VENV_ACTIVATED" = false ]; then
    echo "⚠️  Warning: No virtual environment found or activated!"
    echo "   Looked for: .venv/, venv/, env/"
    echo "   Please set up a virtual environment and try again."
    exit 1
fi

# Set PYTHONPATH for pytest runs to enable absolute imports
if [[ "$*" == *"pytest"* ]]; then
    export PYTHONPATH="shared:services/backend:services/ml_service:services/storage_service:${PYTHONPATH}"
fi

# Run the command passed as arguments
exec "$@"