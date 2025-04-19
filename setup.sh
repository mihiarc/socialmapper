#!/bin/bash
# Setup script for Community Mapper

# Detect Python executable
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python not found. Please install Python 3.7+ to continue."
    exit 1
fi

# Check Python version
VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION+ is required, but you have $VERSION"
    exit 1
fi

echo "Setting up Community Mapper environment..."

# Run the setup_env.py script with the --all flag
$PYTHON setup_env.py --all

# Check if the setup was successful
if [ $? -eq 0 ]; then
    echo "Setup completed successfully!"
    echo ""
    echo "Virtual environment created in .venv directory"
    echo ""
    echo "To run examples:"
    echo "  python example.py --config your_config.yaml"
    echo "  python example.py --examples-only"
    echo ""
    echo "To analyze an isochrone:"
    echo "  python run_isochrone_census.py isochrones/your_isochrone.geojson --states 20 --output results/output.geojson"
else
    echo "Setup failed. Please check the error messages above."
    exit 1
fi 