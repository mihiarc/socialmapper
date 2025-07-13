# Isochrone Validation Mechanisms

## Overview

The DuckDB isochrone cache now includes comprehensive validation to ensure only high-quality, accurate isochrones are stored. Invalid or suspicious isochrones are either rejected or flagged for review.

## Validation Criteria

### 1. **Geometry Validation**
- **Valid structure**: Must be a valid Polygon or MultiPolygon
- **Vertex count**: Between 10 and 10,000 vertices
- **Holes**: Warning if holes exceed 20% of total area
- **Empty check**: Rejects empty geometries

### 2. **Area Validation**
- **Absolute bounds**: 1-5,000 km²
- **Mode-specific expectations**:
  
  **Walking** (km²):
  - 15 min: 2-20
  - 30 min: 8-50
  - 45 min: 18-80
  - 60 min: 30-120
  
  **Biking** (km²):
  - 15 min: 20-100
  - 30 min: 80-400
  - 45 min: 180-900
  - 60 min: 320-1,600
  
  **Driving** (km²):
  - 15 min: 100-500
  - 30 min: 400-2,000
  - 45 min: 900-4,500
  - 60 min: 1,600-8,000

### 3. **Shape Quality**
- **Compactness**: Minimum 0.3 (1.0 = perfect circle)
- **Complexity**: Perimeter/sqrt(area) ratio < 5.0
- **Origin containment**: Origin should be inside isochrone
- **Maximum reach**: Reasonable distance from origin

### 4. **Network Quality**
- **Minimum nodes**: 50 nodes in road network
- **Minimum edges**: 25 edges in road network
- **Generation time**: Warning if > 30 seconds
- **Data freshness**: Warning if OSM data > 1 year old

### 5. **Logical Consistency**
- **Distance checks**: Maximum reach from origin
- **Speed validation**: Based on travel mode expectations
- **Topology**: No self-intersections or invalid geometry

## Validation Process

```python
# Example: Adding isochrone with validation
from utils.isochrone_cache import IsochroneCache

with IsochroneCache(validate=True) as cache:
    # Automatic validation on add
    success, message = cache.add_isochrone(
        isochrone_data,
        geometry,
        metadata={'network_nodes': 1000, 'network_edges': 500}
    )
    
    if not success:
        print(f"Validation failed: {message}")
```

## Validation Results

Each isochrone receives:
- **Status**: `valid`, `warning`, or `invalid`
- **Score**: 0.0-1.0 (weighted composite)
- **Detailed feedback**: Specific checks passed/failed

### Status Meanings:
- **Valid**: Passes all checks, automatically cached
- **Warning**: Minor issues, cached but flagged for review
- **Invalid**: Major issues, rejected unless forced

## Scoring System

Weighted scoring across categories:
- Geometry: 30%
- Area: 20%
- Shape: 20%
- Network: 15%
- Consistency: 15%

## Force Adding

For special cases, invalid isochrones can be force-added:

```python
# Override validation (use sparingly!)
success, message = cache.add_isochrone(
    isochrone_data,
    geometry,
    force=True  # Bypasses validation rejection
)
```

## Validation Statistics

Track validation performance:

```python
# Get validation summary
summary = cache.get_validation_summary()

# Shows:
# - Status distribution (valid/warning/invalid)
# - Common issues
# - Score distribution
```

## Custom Validation

Configure validation for specific needs:

```python
custom_config = {
    'min_area_km2': 5.0,  # Stricter minimum
    'expected_area_ranges': {
        'drive': {
            30: (300, 1500)  # Tighter bounds for Kansas
        }
    }
}

cache = IsochroneCache(validate=True, validation_config=custom_config)
```

## Migration Validation

When importing existing isochrones:

```python
# Migration tool validates during import
uv run python src/utils/migrate_to_cache.py

# Invalid isochrones are:
# 1. Logged with reasons
# 2. Skipped from import
# 3. Reported in summary
```

## Best Practices

1. **Always validate**: Keep validation enabled in production
2. **Review warnings**: Periodically check flagged isochrones
3. **Monitor trends**: Track common validation failures
4. **Adjust thresholds**: Tune for your specific region/use case
5. **Document overrides**: If forcing invalid isochrones, document why

## Common Issues & Solutions

### "Area too small"
- **Cause**: Network data incomplete or disconnected
- **Solution**: Check OSM data quality in area

### "Origin not contained"
- **Cause**: Geocoding offset or network gaps
- **Solution**: Verify geocoding accuracy

### "Low compactness"
- **Cause**: Fragmented road network or water bodies
- **Solution**: Expected in some areas, review case-by-case

### "Few network nodes"
- **Cause**: Rural area with sparse roads
- **Solution**: Adjust thresholds for rural analysis

## Validation Reporting

Generate validation reports:

```python
from utils.isochrone_validator import IsochroneValidator

validator = IsochroneValidator()
results = validator.validate_batch(isochrones)
report = validator.get_validation_report(results)

print(f"Pass rate: {report['summary']['pass_rate']:.1%}")
print(f"Common issues: {report['common_warnings']}")
```

## Future Enhancements

1. **ML-based validation**: Learn patterns from validated data
2. **Regional profiles**: Auto-adjust thresholds by region
3. **Visual validation**: Flag visually suspicious shapes
4. **Historical comparison**: Detect anomalies vs. past data
5. **User feedback loop**: Improve based on manual reviews