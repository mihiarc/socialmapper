# Bug Report: Concurrent Processing Produces Incorrect Isochrones for Some Locations

## Summary
When processing 10+ POIs concurrently, SocialMapper generates severely truncated isochrones for certain locations. The same locations produce correct isochrones when processed individually. This leads to dramatic underestimation of service areas and incorrect accessibility analysis results.

## Environment
- **SocialMapper Version**: 0.6.1
- **Python Version**: 3.11
- **Operating System**: macOS Darwin 24.5.0
- **OSMnx Version**: 2.0
- **Installation Method**: `uv pip install -e .`

## Bug Description
When analyzing multiple POIs (≥10) in batch, some locations receive abnormally small isochrones. For example, the Goodland, KS Walmart shows:
- **Batch processing**: 57.9 km² isochrone (incorrect)
- **Individual processing**: 3,761.3 km² isochrone (correct)

This is a **65x difference** in coverage area.

## Steps to Reproduce

1. Create a POI list with 10+ locations including Goodland, KS Walmart:
```python
poi_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "poi_id": "custom_0",
                "poi_name": "Walmart Supercenter Goodland",
                "poi_type": "walmart"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-101.7285206, 39.3343285]
            }
        },
        # ... 9+ more POIs ...
    ]
}
```

2. Process with SocialMapper:
```python
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        poi_data=poi_data,
        travel_time=30,
        travel_mode="drive"
    )
```

3. Compare with individual processing:
```python
# Process just Goodland alone
single_poi_data = {
    "type": "FeatureCollection", 
    "features": [poi_data["features"][0]]  # Just Goodland
}

with SocialMapperClient() as client:
    single_result = client.analyze(
        poi_data=single_poi_data,
        travel_time=30,
        travel_mode="drive"
    )
```

## Expected Behavior
All locations should generate consistent isochrones regardless of batch size. The Goodland, KS Walmart should have a ~3,761 km² isochrone representing 30-minute drive coverage in rural Kansas.

## Actual Behavior
In batch processing (10+ POIs), some locations receive tiny isochrones:
- Goodland: 57.9 km² (only 13 polygon vertices)
- Several other rural locations show similar truncation
- Urban locations seem less affected

## Visual Evidence
![Goodland Isochrone Comparison](https://github.com/user-attachments/assets/goodland-comparison.png)
*Left: Batch processing (57.9 km²) | Right: Individual processing (3,761.3 km²)*

## Root Cause Analysis

### What We've Ruled Out:
1. **Not a clustering issue**: DBSCAN clustering verification shows Goodland is processed individually even in batch mode
2. **Not an OSM data issue**: Direct OSMnx testing successfully downloads 5,030 nodes for Goodland's network
3. **Not a coordinate issue**: Same coordinates work perfectly when processed alone

### Likely Causes:
The issue appears when `use_concurrent=True` (auto-enabled for 10+ POIs). Potential causes:
1. **Race conditions** in network graph downloading/caching
2. **Shared state corruption** between ThreadPoolExecutor workers
3. **Graph cache conflicts** when multiple workers access similar geographic areas
4. **Resource contention** in the ProcessPoolExecutor for isochrone calculations

## Impact
This bug causes severe underestimation of service coverage in rural areas:
- Kansas grocery analysis showed 0% food deserts (clearly incorrect)
- Rural accessibility metrics are unreliable with batch processing
- Any analysis with 10+ POIs may have incorrect results

## Workaround
Process POIs individually or in small batches (<10) to avoid concurrent processing:

```python
# Workaround: Process in small batches
results = []
batch_size = 5
for i in range(0, len(features), batch_size):
    batch = features[i:i+batch_size]
    batch_data = {
        "type": "FeatureCollection",
        "features": batch
    }
    result = client.analyze(poi_data=batch_data, ...)
    results.append(result)
```

## Additional Information
- Small isochrones identified: indices [26, 36, 48, 66, 74, 102, 107] in 116-location dataset
- All problematic isochrones are < 100 km² (vs expected 1,000-4,000 km²)
- Issue is reproducible across multiple runs
- No error messages or warnings are generated

## Suggested Fix
1. Add thread-safe locking for network graph cache access
2. Ensure each worker has isolated graph copies
3. Add validation to detect abnormally small isochrones
4. Consider making concurrent processing opt-in rather than automatic
5. Add warning when isochrone area is suspiciously small relative to travel time

## Files for Reproduction
- Test script: `kansas_grocery_analysis/src/debug_goodland_batch.py`
- Visualization: `kansas_grocery_analysis/src/visualize_goodland_isochrone.py`
- Full dataset: `kansas_grocery_analysis/data/kansas_walmarts_cleaned.csv`