# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SocialMapper is an open-source Python toolkit that analyzes community connections by mapping demographics and access to points of interest (POIs). It creates isochrones (travel time areas) and integrates census data to provide insights about equitable access to community resources.

Key capabilities:
- Query OpenStreetMap for POIs (libraries, schools, parks, etc.)
- Generate travel time isochrones (walk/drive/bike)
- Integrate US Census demographic data
- Create static maps for analysis
- Export data for further analysis in other tools

## Common Development Commands

```bash
# Install for development with all dependencies
pip install -e ".[dev]"

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


# Run CLI
socialmapper --help
```

## Architecture Overview

The codebase follows an ETL (Extract-Transform-Load) pipeline pattern:

1. **Extract**: Pull data from OpenStreetMap and Census APIs
2. **Transform**: Generate isochrones, calculate distances, process demographics
3. **Load**: Create visualizations and export data

### Core Components

- `socialmapper/core.py`: Main API entry point that delegates to pipeline components
- `socialmapper/pipeline/`: Modular ETL pipeline implementation with separate extraction, transformation, and loading stages
- `socialmapper/data/`: Data management layer including census API integration and neighbor system
- `socialmapper/data/`: Data management layer including census API integration and neighbor system
- `socialmapper/ui/`: User interfaces (CLI, Rich terminal UI)
- `socialmapper/isochrone/`: Travel time area generation using OSMnx
- `socialmapper/geocoding/`: Address geocoding with caching

### Key Architectural Patterns

1. **Neighbor System**: Efficient parquet-based system for census block group lookups that reduces storage from 118MB to ~0.1MB
2. **Caching**: Extensive caching for geocoding results and isochrone calculations
3. **Configuration**: Pydantic-based configuration models for type safety
4. **Progress Tracking**: Rich terminal UI with real-time progress updates
5. **Error Handling**: Robust error handling for external API failures

### Testing Strategy

- Unit tests in `tests/` directory
- Use pytest for test execution
- Mock external API calls (Census, OpenStreetMap)
- Test data fixtures for reproducible tests

### External Dependencies

- **Census API**: Requires `CENSUS_API_KEY` environment variable
- **OpenStreetMap**: Uses Overpass API and OSMnx for POI queries
- **Maps**: Matplotlib for static map generation

### Recent Changes (v0.6.0)

- Streamlined codebase by removing experimental features
- Enhanced core ETL pipeline for better maintainability
- Improved neighbor system performance
- Enhanced Rich terminal UI
- Focused on core demographic and accessibility analysis