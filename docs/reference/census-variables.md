# Census Variables Reference

This page provides a complete reference of all census variables available in SocialMapper. These variables can be used with the `--census-variables` CLI option or the `census_variables` parameter in the Python API.

## Variable Usage

Census variables can be specified using either their human-readable names or their official U.S. Census Bureau variable codes:

```bash
# Using human-readable names
socialmapper --location "Portland, OR" --poi amenity:library --census-variables population median_income

# Using census codes
socialmapper --location "Portland, OR" --poi amenity:library --census-variables B01003_001E B19013_001E

# Mixing both formats
socialmapper --location "Portland, OR" --poi amenity:library --census-variables total_population B19013_001E
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
- **ZIP Code Tabulation Area (ZCTA)**: Approximates ZIP code boundaries, useful for larger area analysis

Use the `--geographic-level` option to specify:

```bash
# Block group level (default)
socialmapper --location "Portland, OR" --poi amenity:library --census-variables population

# ZCTA level
socialmapper --location "Portland, OR" --poi amenity:library --census-variables population --geographic-level zcta
```

## Examples

### Basic demographic analysis
```bash
socialmapper --location "Austin, TX" --poi amenity:school \
  --census-variables population median_age median_income
```

### Equity-focused analysis
```bash
socialmapper --location "Chicago, IL" --poi amenity:hospital \
  --census-variables percent_poverty households_no_vehicle median_income
```

### Housing market analysis
```bash
socialmapper --location "Seattle, WA" --poi leisure:park \
  --census-variables median_home_value median_income households
```

### Comprehensive community profile
```bash
socialmapper --location "Boston, MA" --poi amenity:library \
  --census-variables population median_age median_income \
  education_bachelors_plus percent_poverty
```

## Python API Usage

When using the Python API, census variables work the same way:

```python
from socialmapper import SocialMapperClient

with SocialMapperClient() as client:
    result = client.analyze(
        location="Portland, OR",
        poi_type="amenity",
        poi_name="library",
        census_variables=["population", "median_income", "B01002_001E"]  # Mix of formats
    )
```

## Notes

- Variable names are case-insensitive (`population` and `POPULATION` are equivalent)
- The system automatically handles both human-readable names and census codes
- All monetary values are in inflation-adjusted dollars for the survey year
- Some variables may have null values for certain geographic areas due to data suppression or small sample sizes