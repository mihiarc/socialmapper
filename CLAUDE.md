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
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run black socialmapper/
uv run isort socialmapper/

# Lint code
uv run ruff check socialmapper/

# Type checking
uv run mypy socialmapper/

# Build package
uv run hatch build


# Run CLI
uv run socialmapper --help
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

### Recent Changes (v0.6.1)

- Fixed isochrone export functionality (`enable_isochrone_export()`)
- Isochrones now properly export to GeoParquet format
- Enhanced API documentation with isochrone export examples

### Previous Changes (v0.6.0)

- Streamlined codebase by removing experimental features
- Enhanced core ETL pipeline for better maintainability
- Improved neighbor system performance
- Enhanced Rich terminal UI
- Focused on core demographic and accessibility analysis
- Enhanced travel speed handling for more accurate isochrones

## Travel Speed Handling

SocialMapper uses OSMnx 2.0's sophisticated speed assignment system for accurate travel time calculations:

### Speed Assignment Hierarchy

When generating isochrones, OSMnx assigns edge speeds using this priority:

1. **OSM maxspeed tags**: Uses actual speed limits from OpenStreetMap data when available
2. **Highway-type speeds**: Falls back to our configured speeds for each road type (e.g., motorway: 110 km/h, residential: 30 km/h)
3. **Statistical imputation**: For unmapped highway types, uses the mean speed of similar roads in the network
4. **Mode-specific fallback**: As a last resort, uses the travel mode's default speed (walk: 5 km/h, bike: 15 km/h, drive: 50 km/h)

### Highway-Specific Speeds

The system defines realistic speeds for different road types:

**Driving speeds (km/h)**:
- Motorway: 110 (highways/freeways)
- Trunk: 90 (major roads)
- Primary: 65 (primary roads)
- Secondary: 55 (secondary roads)
- Residential: 30 (neighborhood streets)
- Living street: 20 (shared spaces)

**Walking speeds (km/h)**:
- Footway/sidewalk: 5.0
- Path: 4.5
- Steps: 1.5 (stairs)
- Residential: 4.8

**Biking speeds (km/h)**:
- Cycleway: 18 (dedicated bike lanes)
- Primary/secondary: 18-20
- Residential: 15
- Footway: 8 (shared with pedestrians)

These speeds ensure more accurate isochrone boundaries that reflect real-world travel times based on road infrastructure.