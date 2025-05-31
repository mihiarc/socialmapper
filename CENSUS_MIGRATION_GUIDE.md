# SocialMapper v0.4.3 - Streaming Census System

## Overview

SocialMapper v0.4.3 introduces a lightweight streaming census system that eliminates the need for large database files while maintaining all functionality.

## Key Benefits

- **99.9% Storage Reduction**: From 118.7 MB to ~0.1 MB
- **Pure Streaming**: Direct access to Census APIs
- **No Database Maintenance**: Zero database files to manage
- **Always Current**: Latest data from Census APIs
- **Backward Compatible**: All existing code continues to work

## Usage

```python
from socialmapper.census import get_streaming_census_manager

# Get census manager (pure streaming)
manager = get_streaming_census_manager()

# Get block groups for states
block_groups = manager.get_block_groups(['06', '36'])

# Get census data with optional caching
manager = get_streaming_census_manager(cache_census_data=True)
census_data = manager.get_census_data(geoids, variables)
```

## Backward Compatibility

All existing APIs continue to work unchanged:

```python
from socialmapper.census import get_census_database, get_block_groups

# These now use streaming under the hood
db = get_census_database()
block_groups = get_block_groups(['06'])
```

The system automatically uses the most efficient streaming approach while maintaining the same interface.
