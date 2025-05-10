#!/usr/bin/env bash

set -e

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate the environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install the package
echo "Installing SocialMapper package with uv..."
uv pip install --upgrade -e ".[streamlit]"

echo ""
echo "Installation completed successfully!"
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the Streamlit app, run:"
echo "  python -m socialmapper.streamlit_app"
echo "or"
echo "  streamlit run socialmapper/streamlit_app.py" 