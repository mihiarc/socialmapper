#!/bin/bash
# Backend API Development Setup Script

set -e

echo "Setting up SocialMapper Backend API development environment..."

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

# Install the main SocialMapper package in development mode
echo "Installing SocialMapper package..."
if [ -f "../pyproject.toml" ]; then
    pip install -e ..
else
    echo "Warning: Main SocialMapper package not found. Install manually if needed."
fi

# Install API-specific dependencies
echo "Installing API dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo "Backend API development environment setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  uvicorn api_server.main:app --reload --port 8000"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs will be available at: http://localhost:8000/docs"