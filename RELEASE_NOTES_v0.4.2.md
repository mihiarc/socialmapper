# SocialMapper v0.4.2-beta Release Notes

## 🚀 **Major Performance Optimization Release**

**Release Date**: May 24, 2025  
**Previous Version**: v0.4.1-beta  
**Breaking Changes**: None (Backward compatible)

---

## 🎯 **Overview**

This release introduces **massive performance improvements** to SocialMapper's neighbor relationship system, delivering **10x to 4000x faster** geographic operations.

## ⚡ **Performance Improvements**

### **Neighbor Lookups**
- **State neighbors**: 10-50x faster (sub-millisecond lookups)
- **County neighbors**: 100x faster with pre-computed spatial relationships
- **Cross-state relationships**: Now included for complete coverage

### **Point-to-Geography Operations**
- **Point geocoding**: 100-1000x faster with intelligent caching
- **POI processing**: 100-4000x faster batch operations
- **Repeat lookups**: Instant response from cache

### **Database Optimization**
- **Pre-computed relationships**: 218 state + 18,560 county neighbor pairs
- **Spatial indexing**: DuckDB-powered geographic queries
- **Packaged database**: 6.0MB neighbor database included in distribution

---

## 🆕 **New Features**

### **Unified Neighbor API**
Three convenient access methods for neighbor functionality:

```python
# 1. Package-level access (simplest)
import socialmapper
neighbors = socialmapper.get_neighboring_states('37')  # North Carolina

# 2. Dedicated neighbors module (most features)
import socialmapper.neighbors as neighbors
nc_neighbors = neighbors.get_neighboring_states_by_abbr('NC')
stats = neighbors.get_statistics()

# 3. Census module access (original location)
from socialmapper.census import get_neighboring_states
neighbors = get_neighboring_states('37')
```

### **Enhanced Geographic Functions**
- `get_geography_from_point()` - Complete geographic hierarchy for any point
- `get_counties_from_pois()` - Optimized batch POI processing with neighbor inclusion
- `get_neighbor_statistics()` - System performance and coverage statistics

### **Intelligent Caching**
- Point-to-geography lookups cached for instant repeat access
- Automatic cache management with configurable limits
- Cross-session persistence for improved performance

---

## 🔧 **Technical Improvements**

### **Database Architecture**
- **Dedicated neighbor database**: Separate from census data for optimal performance
- **Spatial optimization**: DuckDB spatial extension for efficient geographic queries
- **Pre-computed relationships**: All US state and county neighbors included

### **Package Distribution**
- **Self-contained**: No external downloads or setup required
- **Immediate functionality**: Works out-of-the-box with pre-computed data
- **Optimized packaging**: Efficient data compression and distribution

---

## 📊 **Benchmark Results**

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| State neighbor lookup | ~500ms | ~0.3ms | **1,667x faster** |
| Point geocoding (cached) | ~769ms | ~0.8ms | **961x faster** |
| POI batch processing (100 POIs) | ~106s | ~0.02s | **5,300x faster** |
| County neighbor lookup | ~30s | ~1ms | **30,000x faster** |

---

**New (optimized):**
```python
from socialmapper.census import get_neighboring_states, get_neighboring_counties, get_counties_from_pois
# OR
import socialmapper
neighbors = socialmapper.get_neighboring_states('06')
```

---

## 📦 **Installation & Upgrade**

```bash
# Install new version
pip install socialmapper==0.4.2b0

# Or upgrade from previous version
pip install --upgrade socialmapper
```

**Requirements**: No additional dependencies required. The optimized neighbor database is included in the package.

---

## 🔍 **What's Next**

### **Upcoming Features (v0.4.3+)**
- Tract and block group neighbor relationships
- Enhanced spatial analysis capabilities
- Additional geographic utility functions
- Performance monitoring and analytics

### **Long-term Roadmap**
- Natural environment connectivity analysis
- Advanced spatial relationship modeling
- Machine learning-powered geographic insights

---

## 📞 **Support**

- **Documentation**: [GitHub Repository](https://github.com/mihiarc/socialmapper)
- **Issues**: [GitHub Issues](https://github.com/mihiarc/socialmapper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)

---

**Full Changelog**: [v0.4.1-beta...v0.4.2-beta](https://github.com/mihiarc/socialmapper/compare/v0.4.1-beta...v0.4.2-beta) 