# Known Issues and Workarounds

## 1. Concurrent Processing Bug in SocialMapper

**Issue**: When processing 10+ POIs concurrently, SocialMapper may generate severely truncated isochrones for some locations (especially rural areas). This is tracked as [Issue #45](https://github.com/mihiarc/socialmapper/issues/45).

**Current Workaround**: The analysis script filters out isochrones smaller than 500 km² as these are likely batch processing errors. This is not ideal as it may exclude some legitimately small service areas.

**Better Workaround**: Process POIs in batches smaller than 10 to avoid triggering concurrent processing:

```python
# Example batch processing
batch_size = 9  # Stay under the concurrent threshold
for i in range(0, len(pois), batch_size):
    batch_pois = pois[i:i+batch_size]
    # Process batch...
```

## 2. Duplicate Store Locations

**Issue**: OpenStreetMap data may include multiple entries for the same store (e.g., Walmart Pharmacy, Walmart Garden Center, etc. are separate from the main store).

**Solution**: Run `clean_walmart_data.py` to remove auxiliary services and keep only unique store locations.

## 3. Memory Usage with Large Datasets

**Issue**: Processing 400+ stores with isochrones can consume significant memory.

**Workaround**: 
- Process Walmart and small grocers separately
- Use GeoParquet format for efficient storage
- Consider processing by county or region for very large analyses