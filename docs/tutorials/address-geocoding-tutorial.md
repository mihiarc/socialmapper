# Address Geocoding Tutorial

This tutorial teaches you how to convert street addresses into geographic coordinates (latitude/longitude) for spatial analysis. Address geocoding is essential when you have location data as addresses rather than coordinates.

## What You'll Learn

- Converting single addresses to coordinates
- Batch processing multiple addresses efficiently
- Understanding geocoding quality levels
- Choosing between geocoding providers
- Integrating geocoded addresses with SocialMapper
- Handling errors and edge cases

## Why Use Address Geocoding?

Address geocoding enables you to:
- **Convert address lists** into mappable coordinates
- **Analyze service accessibility** by street address
- **Integrate business locations** with demographic data
- **Create custom POI datasets** from address databases

## Available Providers

SocialMapper includes two geocoding providers:

| Provider | Coverage | Best For | Limitations |
|----------|----------|----------|-------------|
| **Nominatim** | Global | General use, international addresses | Rate limits on free tier |
| **Census Bureau** | US only | High accuracy for US addresses | US addresses only |

The system automatically falls back between providers for best results.

## Getting Started

### Import Required Components

```python
from socialmapper.geocoding import (
    geocode_address, 
    geocode_addresses, 
    AddressInput, 
    GeocodingConfig, 
    AddressProvider, 
    AddressQuality
)
```

## Example 1: Single Address Geocoding

Let's start by geocoding a famous address:

```python
# Create address input
address = AddressInput(
    address="1600 Pennsylvania Avenue NW, Washington, DC 20500",
    id="white_house",
    source="tutorial"
)

# Configure geocoding
config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    fallback_providers=[AddressProvider.CENSUS],
    min_quality_threshold=AddressQuality.APPROXIMATE
)

# Geocode the address
result = geocode_address(address, config)

if result.success:
    print(f"Coordinates: {result.latitude:.6f}, {result.longitude:.6f}")
    print(f"Quality: {result.quality.value}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Provider: {result.provider_used.value}")
else:
    print(f"Failed: {result.error_message}")
```

Output:
```
Coordinates: 38.897700, -77.036553
Quality: approximate
Confidence: 1.00
Provider: nominatim
```

## Understanding Quality Levels

Geocoding results have different quality levels based on precision:

```python
# Test different address types
test_addresses = [
    "1600 Pennsylvania Avenue NW, Washington, DC 20500",  # Street address
    "Washington, DC",                                      # City level
    "North Carolina"                                       # State level
]

for addr in test_addresses:
    address = AddressInput(address=addr)
    result = geocode_address(address, config)
    
    if result.success:
        print(f"{addr[:30]:<30} → Quality: {result.quality.value}")
```

Output:
```
1600 Pennsylvania Avenue NW, W → Quality: approximate
Washington, DC                 → Quality: centroid
North Carolina                 → Quality: approximate
```

### Quality Level Hierarchy

1. **EXACT**: Precise rooftop or parcel-level match
2. **INTERPOLATED**: Estimated along street segment
3. **APPROXIMATE**: Near the location but not exact
4. **CENTROID**: Geographic center of area (city/state)

## Example 2: Batch Address Processing

Process multiple addresses efficiently:

```python
# North Carolina city halls
addresses = [
    "100 N Tryon St, Charlotte, NC",
    "301 E Hargett St, Raleigh, NC", 
    "120 E Main St, Durham, NC",
    "100 N Greene St, Greensboro, NC",
    "100 Coxe Ave, Asheville, NC"
]

# Create address inputs
address_inputs = [
    AddressInput(
        address=addr,
        id=f"nc_{i}",
        source="city_halls"
    )
    for i, addr in enumerate(addresses, 1)
]

# Configure for batch processing
config = GeocodingConfig(
    primary_provider=AddressProvider.CENSUS,  # Better for US addresses
    fallback_providers=[AddressProvider.NOMINATIM],
    min_quality_threshold=AddressQuality.APPROXIMATE,
    enable_cache=True,
    batch_size=3,
    batch_delay_seconds=0.5  # Respect API rate limits
)

# Batch geocode
results = geocode_addresses(address_inputs, config, progress=True)

# Analyze results
successful = [r for r in results if r.success]
print(f"Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
```

### Displaying Batch Results

```python
import pandas as pd
from tabulate import tabulate

# Convert to DataFrame
data = []
for result in successful:
    data.append({
        'Address': result.input_address.address[:40],
        'Latitude': f"{result.latitude:.4f}",
        'Longitude': f"{result.longitude:.4f}",
        'Quality': result.quality.value
    })

df = pd.DataFrame(data)
print(tabulate(df, headers='keys', tablefmt='github', showindex=False))
```

Output:
```
| Address                                 | Latitude  | Longitude | Quality     |
|-----------------------------------------|-----------|-----------|-------------|
| 100 N Tryon St, Charlotte, NC           | 35.2271   | -80.8431  | approximate |
| 301 E Hargett St, Raleigh, NC           | 35.7804   | -78.6382  | approximate |
| 120 E Main St, Durham, NC               | 35.9940   | -78.8986  | approximate |
| 100 N Greene St, Greensboro, NC         | 36.0726   | -79.7920  | approximate |
| 100 Coxe Ave, Asheville, NC             | 35.5951   | -82.5515  | approximate |
```

## Integration with SocialMapper

Convert geocoded addresses into demographic analysis:

```python
# Save geocoded results to CSV
import pandas as pd

df = pd.DataFrame([{
    'name': r.input_address.address.split(',')[0],
    'latitude': r.latitude,
    'longitude': r.longitude,
    'address': r.input_address.address
} for r in successful])

df.to_csv('output/geocoded_addresses.csv', index=False)

# Use with SocialMapper
from socialmapper import SocialMapperClient, SocialMapperBuilder

with SocialMapperClient() as client:
    config = (SocialMapperBuilder()
        .with_custom_pois('output/geocoded_addresses.csv')
        .with_travel_time(15)
        .with_census_variables("total_population", "median_household_income")
        .with_exports(csv=True)
        .build()
    )
    
    result = client.run_analysis(config)
    
    if result.is_ok():
        analysis = result.unwrap()
        print(f"Analyzed {analysis.poi_count} geocoded locations")
        print(f"Census data for {analysis.census_units_analyzed} areas")
```

## Error Handling

Handle common geocoding issues gracefully:

```python
# Test problematic addresses
problem_addresses = [
    "This is not a real address",
    "123 Nonexistent Street, Nowhere, XX 99999",
    "",  # Empty address
    "Paris"  # Ambiguous - which Paris?
]

for addr in problem_addresses:
    if not addr:
        print("Empty address - skipping")
        continue
        
    address = AddressInput(address=addr)
    result = geocode_address(address, config)
    
    if result.success:
        print(f"'{addr}' → {result.latitude:.4f}, {result.longitude:.4f}")
        print(f"  ⚠️  Quality: {result.quality.value} - verify this is correct!")
    else:
        print(f"'{addr}' → Failed: {result.error_message}")
```

## Configuration Patterns

### High-Accuracy US Addresses

For government or medical applications requiring precision:

```python
config = GeocodingConfig(
    primary_provider=AddressProvider.CENSUS,
    min_quality_threshold=AddressQuality.EXACT,
    require_country_match=True,
    default_country='US'
)
```

### Fast Processing for Large Datasets

When speed matters more than fallback options:

```python
config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    fallback_providers=[],  # No fallbacks for speed
    min_quality_threshold=AddressQuality.APPROXIMATE,
    batch_size=10,
    batch_delay_seconds=0.1
)
```

### International Addresses

For global address datasets:

```python
config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    require_country_match=False,
    timeout_seconds=15,
    max_retries=3
)
```

## Best Practices

1. **Always validate results**: Check `result.success` before using coordinates
2. **Set appropriate quality thresholds**: 
   - Medical/Emergency: `EXACT` only
   - Business analysis: `APPROXIMATE` or better
   - Regional studies: `CENTROID` acceptable
3. **Use caching**: Avoid re-geocoding the same addresses
4. **Respect rate limits**: Add delays for batch processing
5. **Include fallback providers**: Improve success rates
6. **Clean addresses first**: Remove special characters, standardize format

## Performance Tips

- **Enable caching**: Geocoded addresses are cached automatically
- **Batch processing**: More efficient than individual requests
- **Provider selection**: Census for US, Nominatim for international
- **Preprocess addresses**: Clean and standardize before geocoding

## Common Issues and Solutions

**Issue**: "No matches found"
- **Solution**: Simplify address, remove apartment numbers, check spelling

**Issue**: "Rate limit exceeded"
- **Solution**: Add delays, reduce batch size, enable caching

**Issue**: "Wrong location returned"
- **Solution**: Add state/country, check quality level, verify provider

**Issue**: "Timeout errors"
- **Solution**: Increase timeout, check internet connection, try fallback provider

## Use Case Examples

### Business Locations Analysis
```python
# Geocode store locations and analyze demographics
store_addresses = pd.read_csv('store_locations.csv')
# ... geocode and analyze with SocialMapper
```

### Service Accessibility Study
```python
# Convert clinic addresses to coordinates for travel time analysis
clinic_addresses = load_clinic_addresses()
# ... geocode and create isochrones
```

### Address Data Cleaning
```python
# Validate and standardize addresses through geocoding
raw_addresses = get_customer_addresses()
# ... geocode to get standardized formatted addresses
```

## Next Steps

After completing this tutorial:

1. Try geocoding your own address datasets
2. Experiment with different quality thresholds
3. Compare provider accuracy for your region
4. Build complete address-to-demographics workflows
5. Create custom POI datasets from address lists

## Full Code

The complete tutorial script is available at:
[`examples/tutorials/05_address_geocoding.py`](https://github.com/mihiarc/socialmapper/blob/main/examples/tutorials/05_address_geocoding.py)

## Key Takeaways

- Address geocoding bridges text addresses and geographic analysis
- Quality levels indicate precision - choose based on use case
- Batch processing is more efficient for multiple addresses
- Provider selection affects accuracy and coverage
- Integration with SocialMapper enables demographic analysis
- Proper error handling ensures robust workflows