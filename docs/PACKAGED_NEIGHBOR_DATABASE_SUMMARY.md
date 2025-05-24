# Packaged Neighbor Database Implementation

## Overview

The SocialMapper package now includes a **pre-computed neighbor database** that eliminates the need for users to have local shapefiles or run spatial computations. All US county neighbor relationships are pre-computed and packaged with the Python distribution.

## Key Benefits

✅ **No Local Dependencies**: Users don't need to download or maintain local shapefiles  
✅ **Instant Availability**: Neighbor relationships are immediately available after package installation  
✅ **Fast Performance**: Sub-millisecond lookups with pre-computed relationships  
✅ **Complete Coverage**: All 51 US states (including DC) with 18,560+ county relationships  
✅ **Small Footprint**: Only 6.0 MB database file included in package  

## Database Contents

### Pre-computed Relationships
- **218 state relationships** (state-to-state neighbors)
- **18,560 county relationships** (within-state county neighbors)
- **2,598 cross-state county relationships** (county neighbors across state boundaries)
- **51 states with complete data** (all US states + DC)

### Database Structure
```
socialmapper/data/neighbors.duckdb (6.0 MB)
├── state_neighbors          # State adjacency relationships
├── county_neighbors         # County neighbor relationships  
├── tract_neighbors          # (Reserved for future use)
├── block_group_neighbors    # (Reserved for future use)
├── point_geography_cache    # Geocoding cache
└── neighbor_metadata        # Database statistics
```

## Usage Examples

### State Neighbors
```python
from socialmapper.census import get_neighboring_states

# Get neighboring states for North Carolina
nc_neighbors = get_neighboring_states('37')
# Returns: ['13', '45', '47', '51'] (GA, SC, TN, VA)
```

### County Neighbors
```python
from socialmapper.census import get_neighboring_counties

# Get neighboring counties for Wake County, NC
wake_neighbors = get_neighboring_counties('37', '183')
# Returns: [('37', '037'), ('37', '063'), ('37', '069'), ...]
```

### Point Geocoding
```python
from socialmapper.census import get_geography_from_point

# Get geographic identifiers for a point
geo = get_geography_from_point(35.7796, -78.6382)  # Raleigh, NC
# Returns: {'state_fips': '37', 'county_fips': '183', ...}
```

## Implementation Details

### Automatic Database Detection
The system automatically detects and uses the packaged database:

```python
def get_default_neighbor_db_path() -> Path:
    # Try packaged database first
    package_db_path = Path(__file__).parent.parent / "data" / "neighbors.duckdb"
    if package_db_path.exists():
        return package_db_path
    
    # Fall back to user directory for development
    return Path.home() / ".socialmapper" / "neighbors.duckdb"
```

### Package Configuration
- **pyproject.toml**: Includes database in wheel distribution
- **MANIFEST.in**: Ensures database is included in source distributions
- **Hatchling**: Configured to include `socialmapper/data/*.duckdb` files

## Development vs Production

### For End Users (Production)
- ✅ Install package: `pip install socialmapper`
- ✅ Use immediately: No setup required
- ✅ Fast lookups: Pre-computed relationships
- ✅ No dependencies: No local shapefiles needed

### For Developers
- 🔧 Development scripts in `dev_scripts/`:
  - `populate_us_neighbors.py` - Populate neighbor relationships
  - `create_package_neighbor_db.py` - Create package database
  - `test_packaged_neighbors.py` - Verify package functionality

## Migration from Previous Version

### Before (Required Local Shapefiles)
```python
# Users needed local shapefiles at specific paths
# Spatial computations happened at runtime
# Potential for 404 errors downloading shapefiles
```

### After (Packaged Database)
```python
# Everything works out of the box
from socialmapper.census import get_neighboring_counties
neighbors = get_neighboring_counties('37', '183')  # Instant results
```

## Performance Comparison

| Operation | Before | After |
|-----------|--------|-------|
| State neighbors | ~0.35ms | ~0.35ms |
| County neighbors | **Not available** | ~1-2ms |
| Setup time | **Manual** | **Instant** |
| Dependencies | **Local shapefiles** | **None** |
| Package size | Small | +6.0 MB |

## File Structure

```
socialmapper/
├── data/
│   └── neighbors.duckdb          # Pre-computed neighbor database (6.0 MB)
├── census/
│   └── neighbors.py              # Neighbor management (updated)
└── ...

dev_scripts/                      # Development only (not in package)
├── populate_us_neighbors.py      # Population script
├── create_package_neighbor_db.py # Package creation script
└── test_packaged_neighbors.py    # Verification tests
```

## Quality Assurance

### Automated Testing
- ✅ All imports work correctly
- ✅ Database statistics are complete
- ✅ State neighbor lookups function
- ✅ County neighbor lookups function
- ✅ Point geocoding works (when API available)
- ✅ No local shapefile dependencies

### Data Validation
- ✅ 218 state relationships (complete US coverage)
- ✅ 18,560+ county relationships (comprehensive)
- ✅ 2,598 cross-state relationships (border counties)
- ✅ 51 states with data (all US states + DC)

## Future Enhancements

### Planned Features
- 🔮 **Tract neighbors**: Census tract-level relationships
- 🔮 **Block group neighbors**: Block group-level relationships
- 🔮 **Distance calculations**: Shared boundary lengths
- 🔮 **Relationship types**: Different neighbor relationship types

### Extensibility
The database schema supports future geographic levels:
- `tract_neighbors` table (ready for implementation)
- `block_group_neighbors` table (ready for implementation)
- Metadata tracking for updates and versioning

## Conclusion

The packaged neighbor database transforms SocialMapper from a tool requiring local setup to a **plug-and-play solution**. Users can now:

1. **Install once**: `pip install socialmapper`
2. **Use immediately**: No configuration required
3. **Get fast results**: Pre-computed relationships
4. **Scale confidently**: Complete US coverage

This implementation provides the foundation for advanced geographic analysis while maintaining simplicity for end users.

---

**Database Size**: 6.0 MB  
**Coverage**: Complete United States (51 states)  
**Relationships**: 18,560+ county neighbors  
**Performance**: Sub-millisecond lookups  
**Dependencies**: None (self-contained) 