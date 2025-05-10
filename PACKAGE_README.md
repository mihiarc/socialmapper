# SocialMapper Package

SocialMapper is now packaged as a proper Python package! This README describes how to install and use the packaged version.

## Installation

### Option 1: Installation with uv (Recommended)

The fastest and recommended way to install SocialMapper is using the provided installation scripts with uv:

#### On Unix/macOS:

```bash
# Make the script executable
chmod +x install_with_uv.sh

# Run the installation script
./install_with_uv.sh
```

#### On Windows:

```cmd
# Run the installation script
install_with_uv.bat
```

### Option 2: Manual Installation

You can also install SocialMapper manually:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the environment (Linux/macOS)
source .venv/bin/activate

# Or activate on Windows
# .venv\Scripts\activate

# Install with uv
uv pip install -e .
```

To install with Streamlit support:

```bash
uv pip install -e ".[streamlit]"
```

To install with development dependencies:

```bash
uv pip install -e ".[dev,streamlit]"
```

## Using SocialMapper

### Using the Command-line Interface

SocialMapper can be used directly from the command line:

```bash
# Show help
socialmapper --help

# Run with OpenStreetMap POI query
socialmapper --poi --geocode-area "Chicago" --state "Illinois" --poi-type "amenity" --poi-name "library" --travel-time 15 --census-variables total_population median_household_income

# Run with custom coordinates
socialmapper --custom-coords "path/to/coordinates.csv" --travel-time 20 --census-variables total_population median_household_income
```

### Using the Streamlit App

The Streamlit app provides a user-friendly interface:

```bash
# Run the Streamlit app
python -m socialmapper.streamlit_app

# Alternatively
streamlit run socialmapper/streamlit_app.py
```

### Using the Python API

You can import SocialMapper in your own Python code:

```python
from socialmapper import run_socialmapper, setup_directories

# Run with POI query
results = run_socialmapper(
    geocode_area="Chicago",
    state="IL",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    census_variables=["total_population", "median_household_income"]
)

# Run with custom coordinates
results = run_socialmapper(
    custom_coords_path="path/to/coordinates.csv",
    travel_time=20,
    census_variables=["total_population", "median_household_income"]
)
```

## Development

For development, install with the development dependencies:

```bash
uv pip install -e ".[dev,streamlit]"
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- Ruff for linting

Format your code with:

```bash
# Format with black
black socialmapper

# Sort imports
isort socialmapper

# Lint with ruff
ruff check socialmapper
``` 