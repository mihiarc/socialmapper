# Frequently Asked Questions

## General Questions

### What is SocialMapper?
SocialMapper is a Python tool that analyzes community accessibility by combining travel time analysis with demographic data. It helps you understand who can reach important places like libraries, schools, and hospitals.

### What data sources does it use?
- **OpenStreetMap** for finding places (POIs)
- **US Census Bureau** for demographic data
- **OpenStreetMap road networks** for travel time calculations

### Is it free to use?
Yes! SocialMapper is open source and free to use. The data sources (OpenStreetMap and Census) are also free.

### Do I need a Census API key?
No, but having one improves reliability. Get a free key at [census.gov/developers](https://www.census.gov/developers/).

## Installation

### What Python version do I need?
Python 3.11 or higher. We recommend Python 3.12 for best performance.

### Why is installation taking so long?
First installation downloads several dependencies. This is normal and only happens once.

### Can I use it on Windows/Mac/Linux?
Yes! SocialMapper works on all major operating systems.

## Usage Questions

### How do I analyze my own addresses?
Create a CSV file with columns: name, latitude, longitude. Then:
```python
run_socialmapper(custom_coords_path="your_file.csv", travel_time=15)
```

### What census variables are available?
Common ones include:
- `total_population` - Total population
- `median_household_income` - Median income
- `median_age` - Median age
- `percent_poverty` - Poverty rate
- `percent_without_vehicle` - No vehicle access

### Can I analyze multiple locations at once?
Yes! Use a CSV file with multiple locations or loop through different searches.

### How accurate are the travel times?
Travel times use real road networks and are quite accurate. They assume:
- Normal traffic conditions
- Standard travel speeds
- No delays or stops

## Performance

### Why is my first run slow?
SocialMapper builds caches on first use. Subsequent runs will be much faster.

### How can I speed up analysis?
- Use fewer census variables
- Enable caching (default)
- Analyze smaller areas
- Use batch processing

### How much data will it download?
Initial setup may download 100-500MB for caches. After that, minimal data is needed.

## Troubleshooting

### "No POIs found"
- Check your place_type spelling
- Verify the county name
- Try a different place type
- Check internet connection

### "Census data error"
- Verify you're analyzing US locations
- Check coordinate accuracy
- Try without Census API key
- Reduce number of variables

### "Memory error"
- Analyze smaller areas
- Use fewer census variables
- Close other applications
- Increase system swap space

## Data Questions

### Can I use it outside the US?
POI finding works globally, but census data is US-only. For non-US analysis, omit census variables.

### How current is the data?
- OpenStreetMap: Live data
- Census: Latest American Community Survey (usually 1-2 years old)

### Can I save results?
Yes! Use `export_csv=True` for data files and `export_maps=True` for visualizations.

## Advanced Usage

### Can I customize travel modes?
Yes, options include:
- `walk` - Walking (default)
- `drive` - Driving
- `bike` - Cycling

### Can I change travel speeds?
Not directly, but OSMnx uses realistic defaults based on road types and travel modes.

### Is there an API?
Yes! SocialMapper has a full Python API. See the [API Reference](api-reference.md).

## Getting Help

### Where can I report bugs?
[GitHub Issues](https://github.com/mihiarc/socialmapper/issues)

### How can I contribute?
See our [Contributing Guide](https://github.com/mihiarc/socialmapper/blob/main/CONTRIBUTING.md)

### Where can I find more examples?
Check the [examples directory](https://github.com/mihiarc/socialmapper/tree/main/examples)