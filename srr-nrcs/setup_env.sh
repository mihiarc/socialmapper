#!/bin/bash
set -e

# NRCS Conservation Study Area Analysis Environment Setup
# This script sets up a Python 3.11 virtual environment using uv

echo "Setting up NRCS Conservation Study Area Analysis environment..."

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 is required but not found."
    echo "Please install Python 3.11 and try again."
    echo "On macOS, you can use: brew install python@3.11"
    echo "On Ubuntu, you can use: sudo apt install python3.11 python3.11-venv"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is required but not found. Installing uv..."
    curl -sSf https://install.ultraviolet.rs | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create required directories
echo "Creating required directories..."
mkdir -p data output/maps

# Create a virtual environment with uv using Python 3.11
echo "Creating virtual environment with Python 3.11..."
uv venv .venv --python=python3.11

# Install dependencies using uv (no need to activate first with uv)
echo "Installing dependencies with uv..."
uv pip install --upgrade pip
uv pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Create an activation script for convenience
cat > activate.sh << 'EOF'
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
EOF

chmod +x activate.sh

echo ""
echo "Environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "source activate.sh"
echo ""
echo "The following directories have been created:"
echo "- data/: For storing input and intermediate data files"
echo "- output/maps/: For storing generated maps"
echo "" 