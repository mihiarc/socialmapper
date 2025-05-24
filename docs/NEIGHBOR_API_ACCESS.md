# SocialMapper Neighbors API - Direct Access

The SocialMapper package provides **multiple ways** to access neighbor functionality directly, allowing users to utilize geographic neighbor relationships without running the full SocialMapper workflow.

## 🎯 **Access Methods**

### 1. **Package-Level Access** (Simplest)
Import directly from the main package:

```python
import socialmapper

# Get neighboring states
nc_neighbors = socialmapper.get_neighboring_states('37')  # North Carolina
print(nc_neighbors)  # ['13', '45', '47', '51'] (GA, SC, TN, VA)

# Get neighboring counties
wake_neighbors = socialmapper.get_neighboring_counties('37', '183')  # Wake County, NC
print(f"Wake County has {len(wake_neighbors)} neighbors")

# Geocode a point
geo = socialmapper.get_geography_from_point(35.7796, -78.6382)  # Raleigh, NC
print(f"State: {geo['state_fips']}, County: {geo['county_fips']}")
```

### 2. **Dedicated Neighbors Module** (Most Features)
Use the specialized neighbors module with enhanced functionality:

```python
import socialmapper.neighbors as neighbors

# State neighbors with abbreviations
nc_neighbors = neighbors.get_neighboring_states_by_abbr('NC')
print(nc_neighbors)  # ['GA', 'SC', 'TN', 'VA']

# Convert between FIPS codes and abbreviations
fips = neighbors.get_state_fips('NC')  # '37'
abbr = neighbors.get_state_abbr('37')  # 'NC'

# Database statistics
stats = neighbors.get_statistics()
print(f"Database has {stats['county_relationships']:,} county relationships")

# POI batch processing
pois = [
    {'lat': 35.7796, 'lon': -78.6382, 'name': 'Raleigh'},
    {'lat': 35.2271, 'lon': -80.8431, 'name': 'Charlotte'}
]
counties = neighbors.get_counties_from_pois(pois, include_neighbors=True)
```

### 3. **Census Module Access** (Original)
Import from the census module (original location):

```python
from socialmapper.census import (
    get_neighboring_states,
    get_neighboring_counties,
    get_geography_from_point
)

# Same functionality as package-level access
neighbors = get_neighboring_states('48')  # Texas
counties = get_neighboring_counties('48', '201')  # Harris County, TX
```

## 📚 **Available Functions**

### Core Functions
- `get_neighboring_states(state_fips)` - Get neighboring states
- `get_neighboring_counties(state_fips, county_fips)` - Get neighboring counties
- `get_geography_from_point(lat, lon)` - Geocode a point to get geographic IDs
- `get_counties_from_pois(pois, include_neighbors=True)` - Batch process POIs

### Convenience Functions (neighbors module only)
- `get_neighboring_states_by_abbr(state_abbr)` - Use state abbreviations
- `get_state_fips(state_abbr)` - Convert abbreviation to FIPS code
- `get_state_abbr(state_fips)` - Convert FIPS code to abbreviation
- `get_statistics()` - Get database statistics
- `get_neighbor_manager()` - Access advanced functionality

### Reference Data (neighbors module only)
- `STATE_FIPS_CODES` - Dictionary mapping abbreviations to FIPS codes
- `FIPS_TO_STATE` - Dictionary mapping FIPS codes to abbreviations

## 🚀 **Performance Benefits**

All access methods provide the same high-performance benefits:

- **Sub-millisecond lookups** for state neighbors
- **1-2ms lookups** for county neighbors  
- **Intelligent caching** for point geocoding
- **Batch processing** for multiple POIs
- **No external dependencies** (uses packaged database)

## 💡 **Use Cases**

### Research & Analysis
```python
import socialmapper.neighbors as neighbors

# Analyze regional connectivity
for state in ['NC', 'SC', 'GA', 'VA', 'TN']:
    neighbor_count = len(neighbors.get_neighboring_states_by_abbr(state))
    print(f"{state}: {neighbor_count} neighbors")
```

### Data Processing
```python
import socialmapper

# Process a dataset of locations
locations = [
    {'lat': 35.7796, 'lon': -78.6382, 'business': 'Restaurant A'},
    {'lat': 35.2271, 'lon': -80.8431, 'business': 'Store B'},
    # ... more locations
]

# Get all relevant counties (including neighbors for market analysis)
counties = socialmapper.get_counties_from_pois(locations, include_neighbors=True)
print(f"Market analysis should cover {len(counties)} counties")
```

### Geographic Validation
```python
from socialmapper.census import get_geography_from_point

def validate_location(lat, lon):
    geo = get_geography_from_point(lat, lon)
    if geo['state_fips'] and geo['county_fips']:
        return f"Valid: State {geo['state_fips']}, County {geo['county_fips']}"
    else:
        return "Invalid location"

print(validate_location(35.7796, -78.6382))  # Raleigh, NC
```

## 🔧 **Advanced Usage**

For advanced operations, access the neighbor manager directly:

```python
import socialmapper.neighbors as neighbors

# Get the manager for advanced operations
manager = neighbors.get_neighbor_manager()

# Access detailed statistics
stats = manager.get_neighbor_statistics()
print(f"Cross-state relationships: {stats['cross_state_county_relationships']}")

# Custom database path (for development)
custom_manager = neighbors.get_neighbor_manager('/path/to/custom/neighbors.duckdb')
```

## 📦 **Installation & Requirements**

The neighbor functionality is included with the standard SocialMapper installation:

```bash
pip install socialmapper
```

**No additional setup required!** The neighbor database is packaged with the installation and ready to use immediately.

## 🎯 **Summary**

| Access Method | Best For | Key Features |
|---------------|----------|--------------|
| **Package Level** | Simple integration | Direct import, minimal code |
| **Neighbors Module** | Full functionality | Abbreviations, convenience functions, statistics |
| **Census Module** | Existing code | Original API, backward compatibility |

All methods provide the same core functionality with different levels of convenience and features. Choose the one that best fits your workflow!

---

**Database Coverage**: Complete United States (51 states)  
**Relationships**: 18,560+ county neighbors  
**Performance**: Sub-millisecond to 2ms lookups  
**Dependencies**: None (self-contained package) 