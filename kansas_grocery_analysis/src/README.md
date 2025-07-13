# Source Code Organization

This directory contains all the Python scripts for the Kansas Grocery Analysis project, organized by functionality.

## Directory Structure

```
src/
├── run.py                    # Main runner script - start here!
├── data_prep/               # Data preparation and cleaning
│   ├── prepare_data.py      # Fetch store data from OpenStreetMap
│   └── clean_walmart_data.py # Remove duplicate Walmart entries
├── analysis/                # Core analysis scripts
│   ├── analyze_access.py    # Main food access analysis
│   ├── identify_problem_stores.py # Find stores with isochrone issues
│   └── generate_report.py   # Generate analysis reports
├── visualization/           # Map and visualization generation
│   ├── create_census_map.py # Create demographic maps
│   └── visualize_problem_isochrones.py # Visualize isochrone issues
└── utils/                   # Utility functions (currently empty)
```

## Quick Start

To run the complete analysis:

```bash
# Option 1: Use the runner script (interactive)
uv run python src/run.py

# Option 2: Run scripts directly in sequence
uv run python src/data_prep/prepare_data.py
uv run python src/data_prep/clean_walmart_data.py
uv run python src/analysis/analyze_access.py
```

## Script Descriptions

### Data Preparation
- **prepare_data.py**: Fetches Walmart and small grocery store locations from OpenStreetMap
- **clean_walmart_data.py**: Removes auxiliary Walmart services (pharmacy, deli, etc.) to avoid duplicates

### Analysis
- **analyze_access.py**: Main analysis script that:
  - Generates isochrones for all stores
  - Integrates census demographic data
  - Identifies food deserts using USDA methodology
  - Creates maps and exports results
- **identify_problem_stores.py**: Identifies stores with suspiciously small isochrones (debugging tool)
- **generate_report.py**: Creates comprehensive markdown reports

### Visualization
- **create_census_map.py**: Generates choropleth maps of census demographics
- **visualize_problem_isochrones.py**: Creates detailed maps of problematic isochrones

## Known Issues

See [KNOWN_ISSUES.md](../KNOWN_ISSUES.md) for current bugs and workarounds, particularly regarding the concurrent processing issue with large datasets.