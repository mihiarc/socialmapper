# 🏗️ SocialMapper Architecture Guide

## Current Structure Analysis

### ✅ **Well-Organized Components**
```
socialmapper/
├── data/              # Data management (streaming, memory)
├── visualization/     # Plotting and mapping
├── ui/               # User interfaces (CLI, Rich terminal)
├── config/           # Configuration management
└── progress/         # Progress tracking
```

### ⚠️ **Areas for Improvement**

#### 1. **Core Module Size**
- `core.py` (769 lines) - Monolithic function that handles entire pipeline
- **Recommendation**: Break into smaller, composable functions

#### 2. **Mixed Abstraction Levels**
```
# Current: Mixed levels in root
socialmapper/
├── distance/         # Low-level processing
├── isochrone/        # Low-level processing  
├── export/           # High-level output
├── query/            # Low-level data acquisition
└── core.py           # High-level orchestration
```

#### 3. **Inconsistent Naming**
- Some modules use singular (`distance/`) others plural (`counties/`)
- Mixed naming conventions across similar components

## 🎯 **Recommended Modern Structure**

### **Option A: ETL-Based Organization**
```
socialmapper/
├── pipeline/         # Core ETL pipeline
│   ├── extract/      # Data acquisition (POI, Census)
│   ├── transform/    # Processing (distance, isochrone)
│   └── load/         # Output (export, visualization)
├── sources/          # External data adapters
│   ├── census/       # Census Bureau APIs
│   ├── osm/          # OpenStreetMap integration
│   └── geography/    # Geographic boundaries
├── interfaces/       # User-facing components
│   ├── api/          # Python API (core.py)
│   ├── cli/          # Command-line interface
│   └── terminal/     # Rich terminal interface
└── common/           # Shared utilities
    ├── config/       # Configuration
    ├── types/        # Type definitions
    └── utils/        # Helper functions
```

### **Option B: Domain-Based Organization**
```
socialmapper/
├── geospatial/       # All geographic operations
│   ├── distance/
│   ├── isochrone/
│   └── boundaries/
├── data/             # Data management
│   ├── census/
│   ├── osm/
│   └── streaming/
├── interfaces/       # User interfaces
└── core/             # Business logic
```

## 🚀 **Implementation Strategy**

### **Phase 1: Documentation & Planning**
- [x] Document current architecture
- [x] Identify improvement areas
- [ ] Create migration plan
- [ ] Set up backward compatibility

### **Phase 2: Internal Refactoring (No Breaking Changes)**
- [ ] Break down `core.py` into smaller functions
- [ ] Improve internal module organization
- [ ] Add type hints and documentation
- [ ] Standardize naming conventions

### **Phase 3: Structural Improvements**
- [ ] Implement new directory structure
- [ ] Update import paths
- [ ] Maintain backward compatibility aliases
- [ ] Update documentation

### **Phase 4: Cleanup**
- [ ] Remove deprecated aliases
- [ ] Final testing and validation
- [ ] Update examples and documentation

## 📊 **Benefits of Refactoring**

### **Developer Experience**
- **Clearer Mental Model**: ETL stages are intuitive
- **Easier Navigation**: Related code is co-located
- **Better Testing**: Smaller, focused modules
- **Reduced Complexity**: Single responsibility principle

### **Maintainability**
- **Easier Debugging**: Clear separation of concerns
- **Simpler Onboarding**: Logical structure for new contributors
- **Better Documentation**: Structure reflects functionality
- **Future Extensions**: Clear places for new features

### **Performance**
- **Lazy Loading**: Import only what's needed
- **Better Caching**: Clear data flow patterns
- **Optimized Imports**: Reduced circular dependencies

## 🎯 **Next Steps**

1. **Immediate (No Breaking Changes)**:
   - Refactor `core.py` into smaller functions
   - Add comprehensive type hints
   - Improve documentation

2. **Short-term (Backward Compatible)**:
   - Create new structure alongside existing
   - Add compatibility aliases
   - Gradual migration of internal imports

3. **Long-term (Major Version)**:
   - Complete structural reorganization
   - Remove compatibility aliases
   - Update all documentation and examples

## 🔧 **Implementation Guidelines**

### **Naming Conventions**
- Use **singular** for modules (`distance/`, not `distances/`)
- Use **verbs** for functions (`calculate_distance`, not `distance_calc`)
- Use **nouns** for classes (`DistanceCalculator`, not `CalculateDistance`)

### **Import Patterns**
```python
# Preferred: Explicit imports
from socialmapper.pipeline.extract import query_pois
from socialmapper.pipeline.transform import calculate_distances

# Avoid: Star imports
from socialmapper.pipeline.extract import *
```

### **Backward Compatibility**
```python
# In __init__.py - maintain old imports
from .pipeline.extract.query import query_pois as query_overpass  # Old name
from .pipeline.transform.distance import calculate_distances
```

This architecture guide provides a roadmap for improving SocialMapper's structure while maintaining stability and usability. 