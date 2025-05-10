#!/usr/bin/env bash

set -e

echo "Testing SocialMapper package installation..."

# Create a temporary virtual environment
echo "Creating temporary test environment..."
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Use uv to create a virtual environment and install the package
echo "Setting up test environment with uv..."
uv venv
source .venv/bin/activate

# Install the package from the source
echo "Installing SocialMapper from source..."
uv pip install -e "$OLDPWD"

# Run the basic import test
echo "Testing basic imports..."
python -c "import socialmapper; from socialmapper import run_socialmapper, setup_directories; print(f'SocialMapper {socialmapper.__version__} imports successfully!')"

# Clean up
echo "Cleaning up..."
cd "$OLDPWD"
rm -rf "$TEMP_DIR"

echo "Installation test completed successfully!" 