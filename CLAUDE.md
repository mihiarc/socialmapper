# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SocialMapper is an open-source Python toolkit that analyzes community connections by mapping demographics and access to points of interest (POIs). It creates isochrones (travel time areas) and integrates census data to provide insights about equitable access to community resources.

Key capabilities:
- Query OpenStreetMap for POIs (libraries, schools, parks, etc.)
- Generate travel time isochrones (walk/drive/bike)
- Integrate US Census demographic data
- Create both static and interactive maps
- AI-powered community boundary detection using satellite imagery

## Common Development Commands

```bash
# Install for development with all dependencies
pip install -e ".[dev,ai]"

# Run tests
pytest

# Format code
black socialmapper/
isort socialmapper/

# Lint code
ruff check socialmapper/

# Type checking
mypy socialmapper/

# Build package
hatch build

# Run Streamlit app locally
python -m socialmapper.streamlit_app

# Run CLI
socialmapper --help
```

## Architecture Overview

The codebase follows an ETL (Extract-Transform-Load) pipeline pattern:

1. **Extract**: Pull data from OpenStreetMap and Census APIs
2. **Transform**: Generate isochrones, calculate distances, process demographics
3. **Load**: Create visualizations and export data

### Core Components

- `socialmapper/core.py`: Main orchestrator that coordinates the ETL pipeline
- `socialmapper/data/`: Data management layer including census API integration and neighbor system
- `socialmapper/community/`: AI-powered community detection modules (spatial clustering, computer vision, satellite analysis)
- `socialmapper/visualization/`: Map generation (static with matplotlib, interactive with Plotly)
- `socialmapper/ui/`: User interfaces (CLI, Streamlit app, Rich terminal UI)
- `socialmapper/isochrone/`: Travel time area generation using OSMnx
- `socialmapper/geocoding/`: Address geocoding with caching

### Key Architectural Patterns

1. **Neighbor System**: Efficient parquet-based system for census block group lookups that reduces storage from 118MB to ~0.1MB
2. **Caching**: Extensive caching for geocoding results and isochrone calculations
3. **Configuration**: Pydantic-based configuration models for type safety
4. **Progress Tracking**: Rich terminal UI with real-time progress updates
5. **Error Handling**: Graceful degradation when dependencies are missing (e.g., AI features)

### Testing Strategy

- Unit tests in `tests/` directory
- Use pytest for test execution
- Mock external API calls (Census, OpenStreetMap)
- Test data fixtures for reproducible tests

### External Dependencies

- **Census API**: Requires `CENSUS_API_KEY` environment variable
- **OpenStreetMap**: Uses Overpass API and OSMnx for POI queries
- **Satellite Imagery**: Optional integration with geoai-py for satellite data
- **Maps**: Mapbox token optional for enhanced Plotly maps

### Recent Changes (v0.5.4)

- Added AI-powered community boundary detection
- Integrated satellite imagery analysis
- Fixed neighbor system import errors
- Enhanced Rich terminal UI
- Improved streaming census data system