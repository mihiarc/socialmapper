# Centralized I/O Module Implementation

## Overview

A dedicated I/O module has been implemented to centralize all file operations in SocialMapper, particularly for handling output maps and other generated files. This addresses the issue where maps for different travel modes were identical due to filename conflicts.

## Key Components

### 1. IOManager (`socialmapper/io/manager.py`)

The main class that handles all I/O operations:

- **Directory Management**: Automatically creates and manages output directory structure
- **File Tracking**: Tracks all generated files with metadata (travel mode, time, category)
- **Filename Generation**: Creates unique filenames that include travel mode to prevent overwriting
- **Output Manifest**: Saves a JSON manifest of all generated files

Key features:
```python
# Initialize IOManager
io_manager = IOManager("output")

# Save a file with automatic tracking
output_file = io_manager.save_file(
    content=data,
    category="maps",
    file_type="map",
    base_name="socialmapper",
    travel_mode="walk",  # This ensures unique filenames per mode
    travel_time=15,
    metadata={"dpi": 300}
)

# Get summary of all outputs
summary = io_manager.get_output_summary()
```

### 2. OutputTracker (`socialmapper/io/manager.py`)

Tracks all generated files during an analysis:

- Maintains a list of OutputFile objects with metadata
- Provides methods to query files by category, type, or travel mode
- Generates summaries and manifests
- Tracks file existence and size

### 3. Centralized Writers (`socialmapper/io/writers.py`)

Standardized file writers for all formats:
- CSV
- Parquet/GeoParquet
- GeoJSON
- JSON
- Maps (PNG/SVG)
- HTML

### 4. Centralized Readers (`socialmapper/io/readers.py`)

Standardized file readers for various input formats:
- POI data (JSON, CSV, GeoJSON)
- Census data (CSV, Parquet)
- Geospatial data (GeoJSON, GeoParquet, Shapefile)

## Integration Changes

### Pipeline Orchestrator

The pipeline orchestrator now uses IOManager for all file operations:

1. **Initialization**: Creates IOManager instance in `__init__`
2. **Export Stage**: Passes IOManager to export functions
3. **Map Generation**: Passes IOManager to map generation functions
4. **Results Compilation**: Includes file tracking information in results

### Export Module

Updated to use IOManager when available:
- Falls back to legacy path handling for backward compatibility
- Uses IOManager's `save_file` method for centralized tracking
- Prepares data using existing preparation functions

### Map Module

Updated to use IOManager for saving maps:
- Each map includes travel mode in filename
- Maps are tracked with full metadata
- Prevents overwriting between different travel modes

### Streamlit UI

Updated to handle both new IOManager structure and legacy structure:

1. **ZCTA Analysis Page**: 
   - Detects new vs legacy file structure
   - Displays files by category with proper filtering
   - Shows maps specific to the travel mode used

2. **Travel Modes Page**:
   - Properly filters maps by travel mode
   - Loads census data files with mode filtering
   - Export options handle new file structure

## Benefits

1. **Unique Filenames**: Travel mode is included in all filenames, preventing overwrites
2. **Centralized Tracking**: All generated files are tracked in one place
3. **Better Organization**: Files are organized by category (maps, census_data, isochrones, etc.)
4. **Metadata Support**: Each file can have associated metadata
5. **UI Integration**: Streamlit pages can easily display and filter files by mode
6. **Manifest Generation**: Automatic creation of output manifests for reproducibility

## File Naming Convention

Files now follow this pattern:
```
{base_name}_{travel_time}min_{travel_mode}_{suffix}.{extension}

Examples:
- socialmapper_15min_walk_accessibility_map.png
- socialmapper_15min_drive_accessibility_map.png
- socialmapper_15min_bike_census_data.csv
```

## Backward Compatibility

The implementation maintains backward compatibility:
- Streamlit pages detect and handle both old and new file structures
- Export and map modules fall back to legacy handling when IOManager is not provided
- Existing API remains unchanged

## Usage Example

```python
from socialmapper.pipeline.orchestrator import PipelineOrchestrator, PipelineConfig

# Configure pipeline
config = PipelineConfig(
    geocode_area="San Francisco, CA",
    poi_type="amenity",
    poi_name="library",
    travel_time=15,
    travel_mode="walk",  # This will be included in all filenames
    create_maps=True
)

# Run pipeline - IOManager is automatically used
orchestrator = PipelineOrchestrator(config)
results = orchestrator.run()

# Results now include file tracking info
print(results['file_summary'])
# Output: {'total_files': 5, 'categories': {...}, ...}
```

## Testing

The IOManager has been tested with a test script that verifies:
- Directory creation
- File saving with proper naming
- File tracking and retrieval
- Manifest generation
- UI-friendly file information

This implementation ensures that maps and other outputs for different travel modes are properly separated and tracked, resolving the issue where walking and driving maps were identical.