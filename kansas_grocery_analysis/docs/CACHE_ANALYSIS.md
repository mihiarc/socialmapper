# Cache System Analysis - Kansas Grocery Project

## Overview
The cache system stores intermediate data to speed up repeated analyses. Total cache size: **710 MB**

## Cache Components

### 1. Network Cache (`cache/networks/`)
- **Size**: 116 MB
- **Files**: 196 compressed network graphs (.pkl.gz)
- **Database**: SQLite index for spatial queries
- **Purpose**: Stores road network graphs from OpenStreetMap to avoid re-downloading

#### Network Cache Statistics:
- **Travel times cached**: 8, 10, 15, and 30 minutes
- **Most cached**: 30-minute networks (183 files, 91 MB)
- **Average cluster size**: 5.5 locations per network
- **Network type**: All "drive" networks
- **Compression**: Gzip compressed pickle files

#### Cache Hit Analysis:
- Some networks accessed 15-17 times (high reuse)
- Many networks accessed 2-6 times (moderate reuse)
- 153 networks accessed only once (69% single-use)

### 2. JSON Cache Files (`cache/*.json`)
- **Files**: 229 JSON files
- **Size**: ~594 MB (majority of cache)
- **Purpose**: Likely census data or geocoding results
- **Format**: Large JSON files (700KB+ each)

## Cache Efficiency Analysis

### Strengths:
1. **Network deduplication**: Avoids re-downloading same road networks
2. **Spatial indexing**: SQLite enables fast bbox queries
3. **Compression**: Network graphs are gzip compressed
4. **Access tracking**: Monitors cache hit rates

### Potential Issues:

1. **Large JSON files**: 229 files at ~2.6MB each is substantial
   - Consider compression or more efficient storage format
   - May contain redundant census data

2. **Single-use networks**: 69% of network caches used only once
   - Suggests many unique locations or poor cache key generation
   - Could indicate the concurrent processing bug creates unique bboxes

3. **No cache eviction**: No apparent size limits or cleanup
   - Cache will grow indefinitely
   - Old/unused entries never removed

## Recommendations

### Immediate Actions:
1. **Compress JSON cache**: Use gzip like network cache
2. **Implement cache limits**: Set max size and evict LRU entries
3. **Deduplicate census data**: Many JSON files may contain overlapping data

### Long-term Improvements:
1. **Use Parquet for census cache**: More efficient than JSON
2. **Improve cache keys**: Better bbox normalization to increase hits
3. **Add cache statistics**: Track compression ratios, hit rates
4. **Periodic cleanup**: Remove single-use entries older than X days

## Cache Usage by Analysis Phase

1. **Network Download** (116 MB)
   - Downloads road networks for each unique area
   - Caches by bbox + travel time + mode

2. **Census Data** (likely ~594 MB JSON)
   - Fetches demographic data for census block groups
   - Appears to cache full API responses

3. **Geocoding** (unclear if separate)
   - May be included in JSON cache
   - Should cache address -> coordinate mappings

## Impact on Performance

- **First run**: Slow due to network downloads and API calls
- **Subsequent runs**: Much faster due to cache hits
- **Cache misses**: Concurrent processing bug may reduce cache efficiency

## Storage Recommendations

For production use:
- Move cache to faster storage (SSD)
- Consider memory-mapped files for frequent access
- Implement cache warming for common areas
- Use read-through cache pattern