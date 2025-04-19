# Community Mapper

A geospatial toolkit for mapping communities that do not easily conform to administrative boundaries.

## Features

- Generate isochrones (travel time polygons) from Points of Interest
- Find census block groups that intersect with isochrones
- Fetch census block group data from the Census API

## Setup

This project uses Python with a virtual environment managed by `uv` for package management.

### Prerequisites

- Python 3.7+
- Census API key (get one at [api.census.gov](https://api.census.gov/data/key_signup.html))

### Installation

#### Automatic Setup (Recommended)

1. Clone this repository
2. Run the setup script:
   - On macOS/Linux: `./setup.sh`
   - On Windows: `setup.bat`
3. The script will:
   - Create a virtual environment in `.venv` directory
   - Install uv package manager
   - Install required dependencies
   - Create a template `.env` file for your API keys
4. Edit the `.env` file to add your Census API key

#### Manual Setup

If you prefer to set up manually:

1. Clone this repository
2. Run the Python setup script with options:
   ```
   python setup_env.py --all
   ```

   Additional options:
   - `--dirs`: Create required directories only
   - `--env`: Create `.env` file template only
   - `--upgrade`: Upgrade packages in existing environment
   - `--force`: Force recreation of virtual environment

3. Edit the `.env` file to add your Census API key

## Usage

### Full Pipeline Example

The `example.py` script demonstrates the complete workflow:

```bash
python example.py --config your_config.yaml --times 15 30 --states 20 08 48
```

This will:
1. Query POIs based on your config
2. Generate 15 and 30-minute isochrones for each POI
3. Find census block groups in the specified states that intersect with these isochrones
4. Save all results to appropriate files

### Find Census Block Groups Within an Isochrone

For just the census block group analysis:

```bash
python run_isochrone_census.py [path_to_isochrone] --states [state_fips_codes] --output [output_path]
```

Example:
```bash
python run_isochrone_census.py isochrones/isochrone15_walmart_supercenter.geojson --states 20 08 48 --output results/block_groups_walmart_15min.geojson
```

## Project Structure

- `poi_query/`: Main package with core functionality
  - `query.py`: POI query functionality
  - `isochrone.py`: Isochrone generation
  - `blockgroups.py`: Census block group analysis
- `setup_env.py`: Environment setup utilities
- `example.py`: End-to-end example workflow
- `run_isochrone_census.py`: Census block group analysis script
- `.venv/`: Virtual environment directory (created by setup)

## Data Sources

- Census block group geometries: [Census Bureau TIGER/Line API](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer)
- Isochrones: Generated from POIs using the OpenStreetMap road network via `isochrone.py`
- POIs: Retrieved from OpenStreetMap via Overpass API

## License

MIT