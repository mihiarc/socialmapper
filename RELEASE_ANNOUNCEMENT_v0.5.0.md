# SocialMapper v0.5.0 - Performance Optimization Release

**Release Date**: 1 June 2025  
**Status**: Pre-release (Alpha)  
**Performance**: 17.3x Performance Improvement  
**Breaking Changes**: Streamlit UI components affected  

---

## Overview

SocialMapper v0.5.0 is a minor release focused on significant performance optimizations of the core processing engine. While the underlying algorithms have been substantially improved, this release includes breaking changes to the Streamlit interface and should be considered a pre-release version.

### Key Changes

- **17.3x Performance Improvement**: Core processing engine optimized for large datasets
- **Internal Architecture Updates**: Modernized distance calculations and isochrone generation
- **Memory Optimization**: 84% reduction in memory usage through streaming
- **Breaking Changes**: Streamlit UI components require updates
- **Pre-release Status**: May contain bugs, not recommended for production use

### ⚠️ Important Notes

- **Streamlit App**: The web interface has breaking changes and may not function correctly
- **Pre-release Software**: This version may contain bugs and is not production-ready
- **API Changes**: Some internal APIs have changed, though main functions remain compatible
- **Testing Recommended**: Thoroughly test with your specific use cases before deployment

---

## Performance Improvements

### Benchmark Results

| Dataset Size | v0.4.3 | v0.5.0 | Improvement | Notes |
|-------------|--------|--------|-------------|-------|
| 50 POIs | ~45 minutes | 1.1 minutes | 41x faster | Core engine only |
| 500 POIs | ~4.5 hours | 5.2 minutes | 52x faster | Core engine only |
| 2,659 POIs | 5.3 hours | 18.5 minutes | 17.3x faster | Core engine only |

### Performance Metrics

- **Per-POI Processing**: Improved from 7.2s to 0.42s
- **Memory Usage**: 84% reduction through streaming architecture
- **CPU Utilization**: Better parallelization (45.7% usage)
- **Scaling**: Improved efficiency with larger datasets

---

## Technical Changes

### 1. Distance Engine Optimization

Updated the core distance calculation system:

```python
# Updated engine (internal changes)
from socialmapper.distance import VectorizedDistanceEngine

engine = VectorizedDistanceEngine(n_jobs=-1)
distances = engine.calculate_distances(poi_points, centroids)
# Significant performance improvement for large datasets
```

**Changes:**
- Implemented Numba JIT compilation
- Vectorized NumPy operations
- Improved parallelization
- Better memory management

### 2. Isochrone System Updates

Enhanced spatial processing and caching:

```python
# Updated clustering (may have API changes)
from socialmapper.isochrone import IntelligentPOIClusterer

clusterer = IntelligentPOIClusterer(max_cluster_radius_km=15.0)
clusters = clusterer.cluster_pois(pois, travel_time_minutes=15)
# 80% reduction in network downloads, improved caching
```

**Changes:**
- DBSCAN clustering implementation
- SQLite-based caching system
- Concurrent processing improvements
- Network download optimization

### 3. Data Pipeline Modernization

Streaming architecture implementation:

```python
# New data pipeline (experimental)
from socialmapper.data import StreamingDataPipeline

with StreamingDataPipeline() as pipeline:
    # Memory-efficient processing
    pipeline.process_data(data)
# Significant memory reduction for large datasets
```

**Changes:**
- Streaming data processing
- Modern file formats (Parquet support)
- Memory monitoring and optimization
- Improved error handling

---

## Breaking Changes

### Streamlit Interface

⚠️ **The Streamlit web interface has breaking changes:**

- Some UI components may not function correctly
- Configuration options may have changed
- Visualization features may be affected
- Requires updates to work with new backend

### API Changes

While main functions remain compatible, some internal APIs have changed:

- Distance calculation internals updated
- Isochrone clustering parameters may differ
- Configuration system restructured
- Some utility functions relocated

---

## Installation and Testing

### Installation

```bash
# Install pre-release version
pip install socialmapper==0.5.0

# Or with uv
uv add socialmapper==0.5.0
```

### Testing Recommendations

Before using in production:

1. **Test Core Functions**: Verify distance calculations work with your data
2. **Check Memory Usage**: Monitor memory consumption with large datasets
3. **Validate Results**: Compare outputs with previous version
4. **Avoid Streamlit**: Web interface may not work correctly
5. **Report Issues**: Submit bug reports for any problems found

### System Requirements

- **Python**: 3.11+ (3.12 recommended)
- **Memory**: 4GB minimum, 8GB+ for large datasets
- **CPU**: Multi-core recommended for performance benefits
- **Storage**: SSD recommended for caching

---

## Migration Notes

### Core API Compatibility

Most existing code should continue to work:

```python
# Main functions remain compatible
import socialmapper

result = socialmapper.run_socialmapper(
    poi_data=poi_data,
    travel_time_minutes=15,
    output_dir="output"
)
# Should work but test thoroughly
```

### Known Issues

- Streamlit interface requires updates
- Some configuration options may have changed
- Error messages may be different
- Performance characteristics changed (mostly improved)

### Rollback Plan

If issues occur, rollback to previous version:

```bash
pip install socialmapper==0.4.3
```

---

## Testing and Validation

### Internal Testing

- Core engine tested with 2,659 POI dataset
- Memory usage validated under various conditions
- Performance benchmarks completed
- Basic functionality verified

### Known Limitations

- Streamlit interface not fully updated
- Limited testing on edge cases
- Some error conditions may not be handled optimally
- Documentation may be incomplete for new features

### User Testing Needed

- Real-world dataset validation
- Integration with existing workflows
- Performance testing on different hardware
- Identification of remaining bugs

---

## Future Plans

### v0.5.1 (Patch Release)

- Fix Streamlit interface compatibility
- Address reported bugs
- Improve error handling
- Update documentation

### v0.6.0 (Next Minor Release)

- Stable Streamlit interface
- Additional performance optimizations
- Enhanced error handling
- Production readiness improvements

---

## Support and Reporting

### Getting Help

- **Documentation**: [GitHub repository](https://github.com/mihiarc/socialmapper)
- **Bug Reports**: [GitHub Issues](https://github.com/mihiarc/socialmapper/issues) (please report any issues found)
- **Discussions**: [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)

### Reporting Issues

When reporting bugs, please include:
- Python version and operating system
- Dataset size and characteristics
- Error messages and stack traces
- Steps to reproduce the issue

---

## Summary

SocialMapper v0.5.0 delivers significant performance improvements to the core processing engine, with 17.3x faster processing for large datasets. However, this is a pre-release version with breaking changes to the Streamlit interface and potential remaining bugs.

**Recommended for:**
- Performance testing and evaluation
- Core processing workflows (non-Streamlit)
- Development and experimentation

**Not recommended for:**
- Production deployments
- Streamlit-based workflows
- Critical applications requiring stability

This release establishes the foundation for future stable releases while providing immediate performance benefits for users willing to work with pre-release software.

---

**SocialMapper v0.5.0 - Performance-Focused Pre-release** 