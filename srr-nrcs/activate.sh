#!/bin/bash
# Source this file to activate the virtual environment
# Usage: source activate.sh

# Activate the virtual environment
source .venv/bin/activate

# Set up environment variables from .env if it exists
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

echo "NRCS Conservation Study Area Analysis environment activated!"
echo "Python: $(which python)"
echo "Version: $(python --version)"
