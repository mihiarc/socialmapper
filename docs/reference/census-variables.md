# Census Variables Reference

This page provides a complete reference of all census variables available in SocialMapper. These variables can be used with the `variables` parameter in the `get_census_data()` function.

## Variable Usage

Census variables can be specified using either their human-readable names or their official U.S. Census Bureau variable codes:

```python
from socialmapper import create_isochrone, get_census_data

# Create an isochrone
iso = create_isochrone((45.5152, -122.6784), travel_time=15)

# Using human-readable names
census_data = get_census_data(iso, ["population", "median_income"])

# Using census codes
census_data = get_census_data(iso, ["B01003_001E", "B19013_001E"])

# Mixing both formats
census_data = get_census_data(iso, ["total_population", "B19013_001E"])
```

## Available Variables

### Population Metrics

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `population` | B01003_001E | Total population count |
| `total_population` | B01003_001E | Total population count (alias) |

### Economic Indicators

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `median_income` | B19013_001E | Median household income in the past 12 months (in inflation-adjusted dollars) |
| `median_household_income` | B19013_001E | Median household income (alias) |
| `percent_poverty` | B17001_002E | Population for whom poverty status is determined |

### Housing Characteristics

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `households` | B11001_001E | Total number of households |
| `housing_units` | B25001_001E | Total housing units |
| `median_home_value` | B25077_001E | Median value of owner-occupied housing units |

### Demographic Characteristics

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `median_age` | B01002_001E | Median age of the population |
| `white_population` | B02001_002E | White alone population |
| `black_population` | B02001_003E | Black or African American alone population |
| `hispanic_population` | B03003_003E | Hispanic or Latino population |

### Education

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `education_bachelors_plus` | B15003_022E | Population 25 years and over with a bachelor's degree or higher |

### Transportation

| Human-Readable Name | Census Code | Description |
|-------------------|-------------|-------------|
| `percent_without_vehicle` | B25044_003E + B25044_010E | Households without a vehicle available (calculated) |
| `households_no_vehicle` | B25044_003E + B25044_010E | Households without a vehicle available (alias) |

## Calculated Variables

Some variables are calculated from multiple census codes:

- **`percent_without_vehicle`** / **`households_no_vehicle`**: Sum of owner-occupied households with no vehicle (B25044_003E) and renter-occupied households with no vehicle (B25044_010E)

## Data Source

All census data comes from the American Community Survey (ACS) 5-Year Estimates, which provides the most reliable data for small geographic areas. The default year is 2021, but data from 2019-2023 is available.

## Geographic Levels

Census variables can be retrieved at different geographic levels:

- **Block Group** (default): The smallest geographic unit, typically containing 600-3,000 people
- **ZCTA**: ZIP Code Tabulation Areas can be queried directly using `get_census_blocks()` with specific parameters

Note: The current API returns block group level data by default when using isochrones.

## Examples

### Basic demographic analysis
```python
from socialmapper import create_isochrone, get_census_data

iso = create_isochrone((30.2672, -97.7431), travel_time=15)  # Austin, TX
data = get_census_data(iso, ["population", "median_age", "median_income"])
```

### Equity-focused analysis
```python
from socialmapper import create_isochrone, get_census_data

iso = create_isochrone((41.8781, -87.6298), travel_time=15)  # Chicago, IL
data = get_census_data(iso, ["percent_poverty", "median_income"])
```

### Housing market analysis
```python
from socialmapper import create_isochrone, get_census_data

iso = create_isochrone((47.6062, -122.3321), travel_time=15)  # Seattle, WA
data = get_census_data(iso, ["median_home_value", "median_income", "households"])
```

### Comprehensive community profile
```python
from socialmapper import create_isochrone, get_census_data

iso = create_isochrone((42.3601, -71.0589), travel_time=15)  # Boston, MA
data = get_census_data(
    iso,
    ["population", "median_age", "median_income", "percent_poverty"]
)
```

## Advanced Usage

When using the Python API, you can use census variable names or codes:

```python
from socialmapper import create_isochrone, get_census_data

# Create an isochrone
iso = create_isochrone(
    location=(45.5152, -122.6784),  # Portland, OR
    travel_time=15,
    travel_mode="drive"
)

# Get census data with mixed formats
census_data = get_census_data(
    location=iso,
    variables=["population", "median_income", "B01002_001E"],  # Mix of formats
    year=2023
)
```

## Notes

- Variable names are case-insensitive (`population` and `POPULATION` are equivalent)
- The system automatically handles both human-readable names and census codes
- All monetary values are in inflation-adjusted dollars for the survey year
- Some variables may have null values for certain geographic areas due to data suppression or small sample sizes