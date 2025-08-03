#!/bin/bash
# Frontend UI Development Setup Script

set -e

echo "Setting up SocialMapper Frontend UI development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install UI dependencies
echo "Installing UI dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your backend API URL"
fi

echo "Frontend UI development environment setup complete!"
echo ""
echo "To start the Streamlit app:"
echo "  source venv/bin/activate"
echo "  streamlit run streamlit_app.py --server.port 8501"
echo ""
echo "UI will be available at: http://localhost:8501"
echo ""
echo "Make sure the backend API is running at the configured URL!"