# Working with Demographics

SocialMapper integrates US Census data to help you understand the population characteristics within travel time areas.

## Available Census Variables

SocialMapper provides access to a wide range of census variables. The most commonly used variables include:

```python
# Common demographic variables
census_variables = [
    "total_population",        # Total population count
    "median_age",             # Median age
    "median_household_income", # Median household income
    "percent_poverty",        # Percentage below poverty line
    "percent_without_vehicle" # Percentage of households without vehicles
]
```

For a complete list of all available census variables, see the [Census Variables Reference](../reference/census-variables.md).

### Using Variables

```python
from socialmapper import run_socialmapper

results = run_socialmapper(
    state="North Carolina",
    county="Wake County", 
    place_type="library",
    travel_time=15,
    census_variables=["total_population", "median_income"]
)
```

## Variable Format

SocialMapper accepts both user-friendly names and Census Bureau variable codes. Here are some examples:

| Friendly Name | Description | Census Code |
|--------------|-------------|-------------|
| `total_population` | Total population | B01003_001E |
| `median_age` | Median age | B01002_001E |
| `median_household_income` | Median household income | B19013_001E |
| `median_income` | Same as above | B19013_001E |
| `percent_poverty` | % below poverty line | B17001_002E |
| `percent_without_vehicle` | % households no vehicle | (calculated) |

See the [Census Variables Reference](../reference/census-variables.md) for the complete list of available variables.

## Working with Results

Census data is returned in the `census_data` list:

```python
# Access census data
for block_group in results['census_data']:
    population = block_group.get('total_population', 0)
    income = block_group.get('median_household_income', 0)
    print(f"Block group {block_group['GEOID']}: Pop={population}, Income=${income}")
```

## Calculating Totals

Sum values across all block groups:

```python
# Total population within travel time
total_pop = sum(
    row.get('total_population', 0) 
    for row in results['census_data']
)

print(f"Total population: {total_pop:,}")

# Average median income (weighted by population)
total_income = 0
total_pop_for_income = 0

for row in results['census_data']:
    pop = row.get('total_population', 0)
    income = row.get('median_household_income', 0)
    if income > 0:  # Exclude missing data
        total_income += income * pop
        total_pop_for_income += pop

avg_income = total_income / total_pop_for_income if total_pop_for_income > 0 else 0
print(f"Average median income: ${avg_income:,.0f}")
```

## Command Line Usage

```bash
# Specify multiple variables
socialmapper --poi --state "Texas" --county "Harris County" \
  --place-type "school" --travel-time 10 \
  --census-variables total_population median_age percent_poverty
```

## Geographic Levels

SocialMapper supports two geographic levels:

### Block Groups (Default)
- Smaller geographic units
- More precise demographics
- Better for urban analysis

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    geographic_level="block-group",  # Default
    census_variables=["total_population"]
)
```

### ZIP Code Tabulation Areas (ZCTA)
- Larger geographic units
- Approximate ZIP code boundaries
- Better for regional analysis

```python
results = run_socialmapper(
    custom_coords_path="locations.csv",
    geographic_level="zcta",
    census_variables=["total_population"]
)
```

## Handling Missing Data

Census data may be missing for some areas:

```python
# Safe data access
for row in results['census_data']:
    # Use .get() with default value
    population = row.get('total_population', 0)
    
    # Check for None values
    income = row.get('median_household_income')
    if income is not None and income > 0:
        print(f"Valid income: ${income}")
```

## Performance Tips

1. **Request only needed variables** - Each variable adds processing time
2. **Start with basic variables** - total_population is fastest
3. **Use block groups for local analysis** - More accurate for small areas
4. **Use ZCTA for regional analysis** - Faster for large areas

## Example Applications

### Demographic Profile

```python
# Create demographic profile of library service areas
results = run_socialmapper(
    state="California",
    county="San Diego County",
    place_type="library",
    travel_time=15,
    census_variables=[
        "total_population",
        "median_age",
        "median_household_income",
        "percent_poverty"
    ]
)

# Summarize demographics
total_pop = sum(r.get('total_population', 0) for r in results['census_data'])
avg_age = sum(r.get('median_age', 0) * r.get('total_population', 0) 
              for r in results['census_data']) / total_pop

print(f"Population within 15 min of libraries: {total_pop:,}")
print(f"Average median age: {avg_age:.1f}")
```

### Equity Analysis

```python
# Analyze access for vulnerable populations
results = run_socialmapper(
    custom_coords_path="health_clinics.csv",
    travel_time=20,
    census_variables=[
        "total_population",
        "percent_poverty",
        "percent_without_vehicle"
    ]
)

# Calculate vulnerable population
vulnerable_pop = 0
for row in results['census_data']:
    pop = row.get('total_population', 0)
    poverty_rate = row.get('percent_poverty', 0) / 100
    vulnerable_pop += pop * poverty_rate

print(f"Population in poverty within reach: {vulnerable_pop:,.0f}")
```

## Census Data Notes

- Data from American Community Survey (ACS)
- Usually 1-2 years old
- Some rural areas may have limited data
- Income values are in dollars
- Percentages are 0-100, not decimals

## Next Steps

- Learn about [exporting results](exporting-results.md)
- Explore [travel time options](travel-time.md)
- Find [different place types](finding-places.md)