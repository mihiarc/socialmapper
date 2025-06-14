# Census Module Refactoring Implementation Guide

## Overview

This guide will help you implement the modernized census module architecture, moving from the current technical debt to a clean, maintainable structure following modern best practices.

## Current vs. Target Architecture

### Current Problems
- Two overlapping census modules (`/census/` and `/data/census/`)
- Backward compatibility shims creating maintenance burden
- Global state and hard-to-test code
- Unclear separation of concerns

### Target Benefits
- Single, well-organized census module
- Dependency injection for easy testing
- Clean separation of concerns (Domain/Service/Infrastructure)
- Type-safe protocols for all interfaces
- No global state
- Backward compatibility during transition

## Implementation Steps

### Phase 1: Build New Architecture (1-2 weeks)

#### Step 1.1: Set up the domain layer
```bash
# Create the new module structure
mkdir -p socialmapper/census_modern/{domain,services,infrastructure,adapters}
mkdir -p socialmapper/census_modern/domain
mkdir -p socialmapper/census_modern/services
mkdir -p socialmapper/census_modern/infrastructure
mkdir -p socialmapper/census_modern/adapters
```

The domain layer files have been created above. Next, implement the missing infrastructure components:

#### Step 1.2: Implement missing infrastructure
You'll need to create these infrastructure implementations:

1. **API Client** (`infrastructure/api_client.py`)
   - Implement the `CensusAPIClient` protocol
   - Handle Census Bureau API calls with proper error handling
   - Include rate limiting and retry logic

2. **Cache Provider** (`infrastructure/cache.py`)
   - Implement `InMemoryCacheProvider` class
   - Add optional Redis/file-based cache implementations

3. **Repository** (`infrastructure/repository.py`)
   - Implement `SQLiteRepository` and `NoOpRepository`
   - Handle data persistence with proper schema

4. **Rate Limiter** (`infrastructure/rate_limiter.py`)
   - Implement `TokenBucketRateLimiter`
   - Respect Census API rate limits

5. **Geocoder** (`infrastructure/geocoder.py`)
   - Implement `CensusGeocoder`
   - Handle lat/lon to geographic unit conversion

#### Step 1.3: Complete the service layer
Add missing services:

1. **Geography Service** (`services/geography_service.py`)
2. **Neighbor Service** (`services/neighbor_service.py`)

#### Step 1.4: Add comprehensive tests
```bash
# Run the tests we created
python -m pytest tests/test_census_modern.py -v
```

### Phase 2: Migration and Compatibility (1 week)

#### Step 2.1: Create migration scripts
```python
# scripts/migrate_census_usage.py
"""
Script to help users migrate from old to new census API.
"""

def analyze_current_usage():
    """Scan codebase for old census imports and usage."""
    # Implementation to find all census imports
    pass

def generate_migration_suggestions():
    """Generate specific migration suggestions for each usage."""
    # Implementation to suggest specific changes
    pass
```

#### Step 2.2: Update internal usage
Update all internal SocialMapper usage to use the new API:

```python
# Example migration
# OLD:
from socialmapper.census import get_block_groups_streaming
data = get_block_groups_streaming(['06'])

# NEW:
from socialmapper.census_modern import CensusManager
census = CensusManager()
data = census.get_block_groups(['06'])
```

#### Step 2.3: Add integration tests
Create tests that verify the new system works with real Census API calls:

```python
# tests/integration/test_census_real_api.py
def test_real_api_integration():
    """Test against real Census API to ensure compatibility."""
    # Use real API key from environment
    # Test actual data retrieval
    pass
```

### Phase 3: Deprecation and Documentation (1 week)

#### Step 3.1: Add deprecation warnings
Update the old modules to emit warnings:

```python
# socialmapper/census/__init__.py
import warnings
from ..census_modern.adapters.legacy_adapter import *

warnings.warn(
    "socialmapper.census is deprecated. Use socialmapper.census_modern instead.",
    DeprecationWarning,
    stacklevel=2
)
```

#### Step 3.2: Update documentation
1. Update README.md with new usage examples
2. Create migration guide for users
3. Update API documentation
4. Add examples showing both old and new usage

#### Step 3.3: Update CI/CD
```yaml
# .github/workflows/test.yml
- name: Run new census tests
  run: |
    python -m pytest tests/test_census_modern.py
    python -m pytest tests/integration/test_census_real_api.py
```

## Key Design Principles

### 1. Dependency Injection
**Bad (Global State):**
```python
# Global configuration - hard to test
CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

def get_census_data():
    # Uses global state
    api_client = CensusAPI(CENSUS_API_KEY)
```

**Good (Dependency Injection):**
```python
# Configuration injected - easy to test
class CensusService:
    def __init__(self, dependencies: CensusDataDependencies):
        self._api_client = dependencies.api_client
        
    def get_census_data(self):
        # Uses injected dependency
        return self._api_client.fetch_data()
```

### 2. Protocol-Based Design
**Bad (Concrete Dependencies):**
```python
from .api_client import CensusAPIClient

class CensusService:
    def __init__(self):
        self.api_client = CensusAPIClient()  # Hard dependency
```

**Good (Protocol-Based):**
```python
from .interfaces import CensusAPIClient  # Protocol

class CensusService:
    def __init__(self, api_client: CensusAPIClient):
        self.api_client = api_client  # Any implementation
```

### 3. Immutable Configuration
**Bad (Mutable Config):**
```python
class Config:
    def __init__(self):
        self.cache_enabled = True
    
    def disable_cache(self):
        self.cache_enabled = False  # Mutation
```

**Good (Immutable Config):**
```python
@dataclass(frozen=True)
class CensusConfig:
    cache_enabled: bool = True
    
    def with_cache_disabled(self) -> 'CensusConfig':
        return CensusConfig(cache_enabled=False)  # New instance
```

## Testing Strategy

### Unit Tests
```python
def test_census_service_with_mocks():
    # Mock all dependencies
    mock_api = Mock()
    mock_cache = Mock() 
    
    # Inject mocks
    service = CensusService(dependencies)
    
    # Test business logic without external dependencies
    result = service.get_census_data()
```

### Integration Tests
```python
def test_real_census_api():
    # Use real configuration
    config = CensusConfig(census_api_key=os.getenv("CENSUS_API_KEY"))
    manager = create_census_manager(config)
    
    # Test with real API
    data = manager.get_census_data(["010010201001"], ["B01003_001E"])
    assert len(data) > 0
```

### Performance Tests
```python
def test_cache_performance():
    # Test that caching improves performance
    start = time.time()
    data1 = manager.get_census_data(geoids, variables, use_cache=True)
    first_call_time = time.time() - start
    
    start = time.time()
    data2 = manager.get_census_data(geoids, variables, use_cache=True)
    second_call_time = time.time() - start
    
    assert second_call_time < first_call_time * 0.1  # 10x faster with cache
```

## Migration Timeline

### Week 1-2: Development
- [ ] Implement domain entities and interfaces
- [ ] Build infrastructure layer
- [ ] Create service layer
- [ ] Add comprehensive unit tests
- [ ] Create public API with dependency injection

### Week 3: Integration
- [ ] Create backward compatibility adapters
- [ ] Add integration tests with real APIs
- [ ] Migrate internal usage to new API
- [ ] Update CLI tools integration

### Week 4: Documentation and Rollout
- [ ] Add deprecation warnings to old modules
- [ ] Update documentation and examples
- [ ] Create migration guide for users
- [ ] Release with both old and new APIs available

### Future (Next Major Version)
- [ ] Remove old census modules
- [ ] Remove backward compatibility adapters
- [ ] Make new module the default

## Success Metrics

1. **Test Coverage**: >90% coverage on new module
2. **Performance**: New API is at least as fast as old API
3. **Compatibility**: All existing code works with adapters
4. **Maintainability**: New code passes all linting and type checking
5. **Documentation**: Complete examples and migration guide

## Common Pitfalls to Avoid

1. **Don't break existing usage** - Always maintain backward compatibility during transition
2. **Don't over-engineer** - Start simple and add complexity only when needed
3. **Don't forget integration tests** - Unit tests alone aren't sufficient
4. **Don't ignore performance** - Profile both old and new implementations
5. **Don't skip documentation** - Good docs are critical for adoption

## Getting Help

If you run into issues during implementation:

1. Run the tests to verify your implementation
2. Check the example usage in the test files
3. Use the type checker (`mypy`) to catch interface mismatches
4. Profile performance to ensure the new implementation is efficient

The new architecture should make census operations more reliable, testable, and maintainable while providing a smooth migration path for existing users. 