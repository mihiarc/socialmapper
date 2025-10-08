# Troubleshooting

Common issues and solutions when using SocialMapper.

## Installation Issues

### "No module named socialmapper"

**Problem**: Python can't find SocialMapper after installation.

**Solutions**:
1. Ensure installation completed: `pip install socialmapper`
2. Check you're using the right Python environment
3. Try reinstalling: `pip install --upgrade socialmapper`

### "Dependency conflict"

**Problem**: Package dependencies conflict with existing packages.

**Solutions**:
1. Use a virtual environment:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   pip install socialmapper
   ```
2. Update pip: `pip install --upgrade pip`

## Data Issues

### "No POIs found"

**Problem**: Search returns no results.

**Solutions**:
1. Check spelling of place_type (use singular: "library" not "libraries")
2. Verify county name includes "County" suffix
3. Try a broader search area
4. Check internet connection

**Debug**:
```python
# Try different parameters
results = run_socialmapper(
    state="CA",  # Try abbreviation
    county="Los Angeles County",  # Full name with "County"
    place_type="library"  # Singular form
)
```

### "No census data found"

**Problem**: No demographic data returned.

**Solutions**:
1. Verify coordinates are in the United States
2. Check coordinates aren't in water/uninhabited areas
3. Try a larger travel time
4. Use block-group instead of ZCTA for better coverage

### "Invalid coordinates"

**Problem**: Custom coordinates are rejected.

**Solutions**:
1. Check latitude is between -90 and 90
2. Check longitude is between -180 and 180
3. Verify coordinates aren't swapped (latitude first)
4. Ensure decimal format (35.7796, not 35°46'47"N)

## Performance Issues

### "Analysis taking too long"

**Problem**: Processing seems stuck or very slow.

**Solutions**:
1. Start with smaller travel times (5-10 minutes)
2. Analyze fewer locations at once
3. Request fewer census variables
4. First run is slower (building caches)

**Optimize**:
```python
# Start simple
results = run_socialmapper(
    custom_coords_path="one_location.csv",
    travel_time=5,
    census_variables=["total_population"]  # Just one variable
)
```

### "Memory error"

**Problem**: Running out of memory during analysis.

**Solutions**:
1. Process locations in batches
2. Use ZCTA instead of block-group
3. Reduce travel time
4. Close other applications

## Output Issues

### "Can't find output files"

**Problem**: Export files aren't where expected.

**Solutions**:
1. Check the output_dir parameter
2. Look in default "output/" directory
3. Ensure export parameters are True
4. Check for write permissions

**Verify**:
```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    export_csv=True,  # Must be True
    output_dir="my_output"  # Check this directory
)
```

### "Maps not generating"

**Problem**: No map files created.

**Solutions**:
1. Set `export_maps=True`
2. Check for matplotlib installation
3. Ensure valid census data exists
4. Look for error messages

## API Issues

### "Census API error"

**Problem**: Census data retrieval fails.

**Solutions**:
1. Works without API key (but less reliable)
2. Get free key at census.gov/developers
3. Check internet connection
4. Census API may be temporarily down

**Set API key**:
```bash
export CENSUS_API_KEY="your_key_here"
# Or in Python:
results = run_socialmapper(
    api_key="your_key_here",
    ...
)
```

### "Rate limit exceeded"

**Problem**: Too many requests to external services.

**Solutions**:
1. Enable caching (default)
2. Add delays between requests
3. Process in smaller batches
4. Wait and retry later

## Common Error Messages

### "ValueError: custom_coords_path must be provided"

You must specify either POI search parameters or a custom coordinates file.

### "FileNotFoundError"

Check the file path - use absolute paths if needed:
```python
import os
file_path = os.path.abspath("my_locations.csv")
results = run_socialmapper(custom_coords_path=file_path)
```

### "KeyError" when accessing results

Check the key exists before accessing:
```python
if 'census_data' in results:
    census_data = results['census_data']
else:
    print("No census data available")
```

## Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your analysis
results = run_socialmapper(...)
```

## Getting Help

If issues persist:

1. Check the [FAQ](faq.md)
2. Review [examples](https://github.com/mihiarc/socialmapper/tree/main/examples)
3. Search [GitHub issues](https://github.com/mihiarc/socialmapper/issues)
4. Open a new issue with:
   - Error message
   - Code that causes the error
   - Python and SocialMapper versions
   - Operating system