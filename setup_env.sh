#!/bin/bash
# setup_env.sh - Environment setup script for SocialMapper

# Stop on error
set -e

# Check if Python 3.9+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.9 or later."
    exit 1
fi

echo "===== SocialMapper Environment Setup ====="
echo "This script will set up the environment for SocialMapper."

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

echo ""
echo "===== Setup Complete ====="
echo "To run the SocialMapper Streamlit app:"
echo "1. Activate the virtual environment:"
echo "   For Linux/macOS: source .venv/bin/activate"
echo "   For Windows: .venv\Scripts\activate"
echo "2. Run the Streamlit app:"
echo "   streamlit run app.py"
echo ""
echo "For more information, see STREAMLIT_README.md" 