# SocialMapper Demo Script

This demo script showcases the key features of your SocialMapper project in an easy-to-run format.

## What the Demo Shows

The demo script (`demo_script.py`) demonstrates four main features of SocialMapper:

### 1. **POI Analysis** 🏛️
- Searches for libraries in Raleigh, NC using OpenStreetMap data
- Analyzes demographics within 15-minute travel time
- Shows population, income, and education data

### 2. **Custom Coordinates** 📍
- Uses custom coordinates for analysis (Downtown Raleigh, NC State, RDU Airport)
- Demonstrates how to analyze specific locations you define
- Shows 10-minute travel time analysis

### 3. **Geographic Neighbors** 🗺️
- Explores state and county neighbor relationships
- Shows point geocoding capabilities
- Displays database statistics

### 4. **Batch Processing** 🔄
- Processes multiple POIs across different states
- Shows efficiency gains with neighbor inclusion
- Demonstrates scalable analysis

## How to Run the Demo

### Prerequisites
Make sure you have SocialMapper installed and your environment activated:

```bash
# If using the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Or if installed globally
pip install socialmapper
```

### Running the Demo

Simply run the demo script:

```bash
python demo_script.py
```

The script will:
1. Run each demonstration automatically
2. Show progress and results for each demo
3. Display generated output files
4. Provide a summary of what worked

### Expected Output

The demo will create files in the `output/` directory:
- **CSV files**: Demographic data with travel distances
- **GeoJSON files**: Isochrones and geographic boundaries  
- **JSON files**: POI data and metadata

## Understanding the Results

### CSV Files
The CSV files contain census data for areas within travel time of your POIs:
- `GEOID`: Census block group identifier
- `total_population`: Population count
- `median_household_income`: Income data
- `travel_distance_km`: Distance from POI

### GeoJSON Files
- **Isochrones**: Show areas reachable within specified travel time
- **Block Groups**: Census areas that intersect with isochrones

### What Each Demo Teaches

1. **Demo 1 (POI Analysis)**: How to analyze real-world points of interest
2. **Demo 2 (Custom Coordinates)**: How to analyze your own specific locations
3. **Demo 3 (Neighbors)**: How geographic relationships work in SocialMapper
4. **Demo 4 (Batch Processing)**: How to efficiently process multiple locations

## Next Steps After Running the Demo

1. **Explore the Output**: Check the `output/` directory for generated files
2. **Try the Streamlit App**: Run `python -m socialmapper.ui.streamlit.app` for an interactive interface
3. **Use the CLI**: Try `socialmapper --help` to see command-line options
4. **Customize**: Modify the demo script to analyze your own areas of interest

## Troubleshooting

If the demo fails:
- **Check internet connection**: POI queries need internet access
- **Verify dependencies**: Make sure all packages are installed
- **Check API limits**: OpenStreetMap queries may have rate limits
- **Run individual demos**: Comment out demos in `main()` to test one at a time

## Example Use Cases

After seeing the demo, you might want to analyze:
- **Food access**: Supermarkets and grocery stores
- **Healthcare access**: Hospitals and clinics  
- **Education access**: Schools and libraries
- **Transportation**: Bus stops and train stations
- **Recreation**: Parks and community centers

## Demo Script Features

The demo script includes:
- **Error handling**: Each demo runs independently
- **Progress tracking**: Shows what's happening at each step
- **Result summary**: Reports success/failure of each demo
- **File exploration**: Shows what files were created
- **Next steps**: Guides you on what to try next

This demo gives you a comprehensive overview of SocialMapper's capabilities in just a few minutes! 