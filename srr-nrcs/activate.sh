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

# Helper function to run pipeline scripts
run_pipeline() {
    echo "Running NRCS Conservation Study Area Analysis pipeline..."
    
    # Store current directory
    local current_dir=$(pwd)
    
    # Ensure we're in the correct directory
    if [[ ! "$current_dir" == */srr-nrcs ]]; then
        if [ -d "srr-nrcs" ]; then
            cd srr-nrcs
        else
            echo "Error: Must be in or under the srr-nrcs directory"
            return 1
        fi
    fi
    
    # Run the Python pipeline script
    python scripts/run_pipeline.py
}

echo "NRCS Conservation Study Area Analysis environment activated!"
echo "Python: $(which python)"
echo "Version: $(python --version)"
echo ""
echo "To run the complete pipeline, use the command: run_pipeline"
