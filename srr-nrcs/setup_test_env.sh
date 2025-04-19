#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv-test" ]; then
  echo "Creating new virtual environment with uv..."
  uv venv -p 3.11 .venv-test
fi

# Activate virtual environment
source .venv-test/bin/activate

# Install package in development mode with testing extras
echo "Installing package with test dependencies..."
uv pip install -e ".[dev]"

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

echo "Test environment setup complete. You can activate it with: source .venv-test/bin/activate" 