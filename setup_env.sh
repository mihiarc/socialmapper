#!/bin/bash
# setup_env.sh - Environment setup script for Community Mapper

# Stop on error
set -e

echo "===== Community Mapper Environment Setup ====="
echo "This script will set up the environment for Community Mapper."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    # Check if pip is installed first
    if ! command -v pip &> /dev/null; then
        echo "pip is not installed. Installing pip..."
        # For Linux/macOS
        if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py
            rm get-pip.py
        # For Windows
        elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python get-pip.py
            rm get-pip.py
        else
            echo "Unsupported OS type: $OSTYPE"
            exit 1
        fi
    fi
    
    # Use pip to install uv if not available
    pip install uv
fi

# Create virtual environment using uv
echo "Creating virtual environment with uv..."
uv venv
echo "Virtual environment created."

# Determine the activation script based on OS
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # macOS or Linux
    ACTIVATE_SCRIPT=".venv/bin/activate"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    ACTIVATE_SCRIPT=".venv/Scripts/activate"
else
    echo "Unsupported OS type: $OSTYPE"
    echo "Please activate the virtual environment manually."
    ACTIVATE_SCRIPT=""
fi

# Activate virtual environment
if [[ -n "$ACTIVATE_SCRIPT" ]]; then
    echo "Activating virtual environment..."
    source "$ACTIVATE_SCRIPT"
    echo "Virtual environment activated."
else
    echo "Could not activate virtual environment automatically."
    echo "Please activate it manually before continuing."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt
echo "Dependencies installed."

# Create required directories
echo "Creating required directories..."
mkdir -p pages
mkdir -p examples
mkdir -p output/{pois,isochrones,block_groups,census_data,maps}
echo "Directories created."

# Create .env file for Census API key if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat << EOF > .env
# Census API key (get one at https://api.census.gov/data/key_signup.html)
CENSUS_API_KEY=your-census-api-key
EOF
    echo ".env file created. Please edit it to add your Census API key."
else
    echo ".env file already exists."
fi

# Activate the virtual environment
source "$ACTIVATE_SCRIPT"
echo "Virtual environment activated."

echo ""
echo "===== Setup Complete ====="
echo "To run the Community Mapper Streamlit app:"
echo "type 'streamlit run app.py' into your terminal"
echo ""
echo "For more information, see STREAMLIT_README.md" 