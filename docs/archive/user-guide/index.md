# User Guide

This guide covers everything you need to know to use SocialMapper effectively.

## Guide Overview

### [Finding Places](finding-places.md)
How to search for libraries, schools, hospitals, and other community resources.

### [Travel Time Analysis](travel-time.md)
Creating isochrones and understanding different travel modes.

### [Working with Demographics](demographics.md)
Using Census variables to analyze population characteristics.

### [Using Custom Locations](custom-locations.md)
Analyzing your own addresses and facilities.

### [Exporting Results](exporting-results.md)
Saving your analysis as CSV files, maps, and reports.

### [Command Line Usage](cli-usage.md)
Using SocialMapper from the terminal.

## Quick Reference

### Common Tasks

**Analyze library access:**
```python
run_socialmapper(
    state="California",
    county="Los Angeles County",
    place_type="library",
    travel_time=15
)
```

**Use custom locations:**
```python
run_socialmapper(
    custom_coords_path="my_locations.csv",
    travel_time=20,
    census_variables=["total_population"]
)
```

**Export maps:**
```python
run_socialmapper(
    state="Texas",
    county="Harris County",
    place_type="school",
    export_maps=True
)
```

### Common Questions

- **How do I find POI types?** → See [Finding Places](finding-places.md)
- **What census variables are available?** → See [Demographics](demographics.md)
- **How do I use my own addresses?** → See [Custom Locations](custom-locations.md)
- **Can I analyze multiple locations?** → Yes! See [Batch Analysis](custom-locations.md#batch-analysis)

## Need Help?

- Check the [FAQ](../faq.md)
- View [example code](https://github.com/mihiarc/socialmapper/tree/main/examples)
- Report issues on [GitHub](https://github.com/mihiarc/socialmapper/issues)