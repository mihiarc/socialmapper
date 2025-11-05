# API Audit - Consistent Return Types & Pydantic Validation

**Issue:** #62
**Date:** 2025-11-05
**Status:** Analysis Complete

## Executive Summary

This audit examines all 5 core API functions and 3 utility functions to identify inconsistencies in return types and opportunities for Pydantic validation. The current API has mixed patterns with some validation in place but inconsistent return types that vary based on parameters.

## Core API Functions Analysis

### 1. `create_isochrone()`

**Current Signature:**
```python
def create_isochrone(
    location: str | tuple[float, float],
    travel_time: int = 15,
    travel_mode: str = "drive"
) -> dict[str, Any]:
```

**Return Type:**
- Always returns `dict` (GeoJSON Feature)
- ✅ **CONSISTENT** - Same type regardless of parameters

**Input Validation:**
- ✅ Manual validation for `travel_time` (1-120 range)
- ✅ Manual validation for `travel_mode` (drive/walk/bike)
- ✅ Coordinate resolution via helper
- ❌ No Pydantic model for input validation

**Recommendation:**
- **Priority:** MEDIUM
- Create `IsochroneRequest` Pydantic model
- Create `IsochroneResult` Pydantic model to wrap GeoJSON
- Return type is already consistent, just needs formalization

---

### 2. `get_census_blocks()`

**Current Signature:**
```python
def get_census_blocks(
    polygon: dict | None = None,
    location: tuple[float, float] | None = None,
    radius_km: float = 5
) -> list[dict[str, Any]]:
```

**Return Type:**
- Always returns `list[dict]` (census block groups)
- ✅ **CONSISTENT** - Same type regardless of parameters

**Input Validation:**
- ✅ Mutually exclusive validation for polygon/location
- ❌ No validation for radius_km bounds
- ❌ No Pydantic model for input validation

**Recommendation:**
- **Priority:** MEDIUM
- Create `CensusBlocksRequest` Pydantic model
- Create `CensusBlock` Pydantic model for individual blocks
- Return `list[CensusBlock]` for type safety

---

### 3. `get_census_data()`

**Current Signature:**
```python
def get_census_data(
    location: dict | list[str] | tuple[float, float],
    variables: list[str],
    year: int = 2023
) -> dict[str, Any]:
```

**Return Type:**
- ⚠️ **INCONSISTENT** - Return varies by location type:
  - For polygon/GEOIDs: `{geoid: {variable: value, ...}, ...}`
  - For point tuple: `{variable: value, ...}` (single block)

**Input Validation:**
- ❌ No validation for year range
- ❌ No validation for variables list
- ❌ Accepts 3 different location types (overloaded parameter)
- ❌ No Pydantic model

**Issues Identified:**
1. **High priority** - Return type changes based on input
2. Difficult for users to know what structure they'll get
3. Location parameter is heavily overloaded

**Recommendation:**
- **Priority:** HIGH
- Create separate functions or use Union type for result
- Create `CensusDataRequest` Pydantic model
- Create `CensusDataResult` Pydantic model with clear structure
- Consider splitting into `get_census_data_for_polygon()` and
  `get_census_data_for_point()` for clarity

---

### 4. `create_map()`

**Current Signature:**
```python
def create_map(
    data: list[dict] | pd.DataFrame | gpd.GeoDataFrame,
    column: str,
    title: str | None = None,
    save_path: str | None = None,
    export_format: str = "png"
) -> bytes | dict | None:
```

**Return Type:**
- ❌ **HIGHLY INCONSISTENT** - Three different return types:
  - Image formats (png/pdf/svg): `bytes` (if save_path is None)
  - GeoJSON format: `dict` (if save_path is None)
  - All formats: `None` (if save_path is provided)

**Input Validation:**
- ✅ Validation for export_format
- ✅ Validation that column exists in data
- ❌ No Pydantic model

**Issues Identified:**
1. **Critical priority** - This is the worst offender
2. Same function returns `bytes | dict | None`
3. Return type depends on both `save_path` and `export_format`
4. Very difficult for users to handle

**Recommendation:**
- **Priority:** CRITICAL
- Create `MapRequest` Pydantic model
- Create `MapResult` with discriminated union:
  ```python
  class MapResult(BaseModel):
      format: str
      data: Optional[bytes] = None  # for images
      geojson: Optional[dict] = None  # for geojson
      file_path: Optional[Path] = None  # when saved
  ```
- Always return MapResult for consistency

---

### 5. `get_poi()`

**Current Signature:**
```python
def get_poi(
    location: str | tuple[float, float],
    categories: list[str] | None = None,
    travel_time: int | None = None,
    limit: int = 100,
    validate_coords: bool = True
) -> list[dict[str, Any]]:
```

**Return Type:**
- Always returns `list[dict]` (POIs)
- ✅ **CONSISTENT** - Same type regardless of parameters

**Input Validation:**
- ✅ Validation for travel_time (if provided)
- ❌ No validation for limit bounds
- ❌ No validation for categories
- ❌ No Pydantic model

**Recommendation:**
- **Priority:** LOW
- Create `POIRequest` Pydantic model
- Use existing `DiscoveredPOI` model from api_result_types.py
- Return `list[DiscoveredPOI]` for type safety

---

## Utility Functions Analysis

### 6. `analyze_multiple_pois()`

**Current Signature:**
```python
def analyze_multiple_pois(
    locations: list[str | tuple[float, float]],
    travel_time: int = 15,
    travel_mode: str = "drive",
    variables: list[str] = None,
    compare: bool = True
) -> dict[str, Any]:
```

**Return Type:**
- Always returns `dict` with structured data
- ✅ **CONSISTENT** but complex nested structure

**Recommendation:**
- **Priority:** MEDIUM
- Create `MultiPOIAnalysisRequest` Pydantic model
- Create `MultiPOIAnalysisResult` Pydantic model with nested structures

---

### 7. `import_poi_csv()`

**Current Signature:**
```python
def import_poi_csv(
    csv_path: str,
    name_field: str = "name",
    lat_field: str = "latitude",
    lon_field: str = "longitude",
    type_field: str = "type"
) -> list[dict[str, Any]]:
```

**Return Type:**
- Always returns `list[dict]`
- ✅ **CONSISTENT**

**Recommendation:**
- **Priority:** LOW
- Create `CSVImportConfig` Pydantic model
- Return list of `DiscoveredPOI` models

---

### 8. `generate_report()`

**Current Signature:**
```python
def generate_report(
    analysis_data: dict[str, Any],
    format: str = "html",
    template: str = "default",
    include_maps: bool = True
) -> str | bytes:
```

**Return Type:**
- ⚠️ **INCONSISTENT** - Return type varies by format:
  - HTML: returns `str`
  - PDF: returns `bytes`

**Input Validation:**
- ✅ Validation for format

**Recommendation:**
- **Priority:** MEDIUM
- Create `ReportRequest` Pydantic model
- Create `ReportResult` model:
  ```python
  class ReportResult(BaseModel):
      format: str
      content: str | bytes
      file_path: Optional[Path] = None
  ```

---

## Existing Pydantic Infrastructure

✅ Good news: Some Pydantic models already exist in `api_result_types.py`:

```python
- DiscoveredPOI (BaseModel)
- NearbyPOIResult (BaseModel)
- NearbyPOIDiscoveryConfig (BaseModel)
- Result, Ok, Err (Generic error handling types)
- ErrorType (Enum)
```

These can be used as templates for new models.

---

## Summary of Issues

### Critical Priority (Breaking Changes)
1. **`create_map()`** - Returns `bytes | dict | None` depending on parameters

### High Priority
2. **`get_census_data()`** - Returns different dict structures based on location type

### Medium Priority
3. **`create_isochrone()`** - Needs Pydantic request/response models
4. **`get_census_blocks()`** - Needs Pydantic models and radius validation
5. **`analyze_multiple_pois()`** - Needs structured response models
6. **`generate_report()`** - Returns `str | bytes` depending on format

### Low Priority
7. **`get_poi()`** - Can use existing DiscoveredPOI model
8. **`import_poi_csv()`** - Can use existing DiscoveredPOI model

---

## Current Return Type Patterns

| Function | Current Return | Consistency | Issues |
|----------|---------------|-------------|---------|
| `create_isochrone()` | `dict` | ✅ Consistent | None - just needs formalization |
| `get_census_blocks()` | `list[dict]` | ✅ Consistent | None - just needs formalization |
| `get_census_data()` | `dict` | ⚠️ Structure varies | Different structure for point vs polygon |
| `create_map()` | `bytes \| dict \| None` | ❌ Highly inconsistent | Three different types! |
| `get_poi()` | `list[dict]` | ✅ Consistent | None - just needs formalization |
| `analyze_multiple_pois()` | `dict` | ✅ Consistent | Complex nested structure |
| `import_poi_csv()` | `list[dict]` | ✅ Consistent | None - just needs formalization |
| `generate_report()` | `str \| bytes` | ⚠️ Type varies | Different type per format |

---

## Parameter Overloading Issues

### `get_census_data()` location parameter
Accepts three different types:
- `dict` - GeoJSON Feature/geometry
- `list[str]` - GEOID strings
- `tuple[float, float]` - Coordinate pair

**Problem:** This is confusing for users and makes type hints unclear.

**Solution:** Either:
1. Use Pydantic discriminated unions
2. Split into separate functions
3. Create a `Location` union type with clear semantics

---

## Proposed Pydantic Models

### Request Models (Input Validation)

```python
class IsochroneRequest(BaseModel):
    location: str | tuple[float, float]
    travel_time: int = Field(ge=1, le=120, default=15)
    travel_mode: Literal["drive", "walk", "bike"] = "drive"

class CensusBlocksRequest(BaseModel):
    polygon: Optional[dict] = None
    location: Optional[tuple[float, float]] = None
    radius_km: float = Field(gt=0, le=100, default=5)

    @model_validator(mode='after')
    def validate_exclusive_location(self):
        if self.polygon is None and self.location is None:
            raise ValueError("Must provide either polygon or location")
        if self.polygon is not None and self.location is not None:
            raise ValueError("Provide either polygon or location, not both")
        return self

class CensusDataRequest(BaseModel):
    location: dict | list[str] | tuple[float, float]
    variables: list[str] = Field(min_length=1)
    year: int = Field(ge=2010, le=2023, default=2023)

class MapRequest(BaseModel):
    data: list[dict] | Any  # Accept various data types
    column: str
    title: Optional[str] = None
    save_path: Optional[Path] = None
    export_format: Literal["png", "pdf", "svg", "geojson", "shapefile"] = "png"

class POIRequest(BaseModel):
    location: str | tuple[float, float]
    categories: Optional[list[str]] = None
    travel_time: Optional[int] = Field(None, ge=1, le=120)
    limit: int = Field(default=100, ge=1, le=1000)
    validate_coords: bool = True
```

### Response Models (Output Structure)

```python
class IsochroneResult(BaseModel):
    geometry: dict  # GeoJSON geometry
    location: str
    travel_time: int
    travel_mode: str
    area_sq_km: float

class CensusBlock(BaseModel):
    geoid: str
    state_fips: str
    county_fips: str
    tract: str
    block_group: str
    geometry: dict
    area_sq_km: float

class CensusDataResult(BaseModel):
    data: dict[str, dict[str, Any]]  # {geoid: {variable: value}}
    query: CensusDataRequest

class MapResult(BaseModel):
    format: str
    image_data: Optional[bytes] = None
    geojson_data: Optional[dict] = None
    file_path: Optional[Path] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

# Can reuse existing DiscoveredPOI for get_poi()
```

---

## Implementation Strategy

### Phase 1: Critical Fixes (Breaking Changes)
1. Fix `create_map()` to return consistent `MapResult`
2. Fix `get_census_data()` to clarify return structure

### Phase 2: Add Pydantic Request Models
3. Add input validation models for all functions
4. Keep existing function signatures but validate internally
5. Add deprecation warnings for direct parameter usage

### Phase 3: Add Pydantic Response Models
6. Create response models that wrap existing dict returns
7. Add typed accessor methods

### Phase 4: New API (v3.0)
8. Create new functions that require Pydantic models
9. Deprecate old functions
10. Remove old functions in v3.0

---

## Migration Path

### Backward Compatibility Strategy

```python
# Old API (deprecated but still works)
iso = create_isochrone("Portland, OR", travel_time=20)

# New API with Pydantic (recommended)
request = IsochroneRequest(
    location="Portland, OR",
    travel_time=20
)
result = create_isochrone_v2(request)

# Or with convenience wrapper
result = create_isochrone_v2(
    location="Portland, OR",
    travel_time=20
)  # Automatically creates IsochroneRequest
```

### Deprecation Timeline

- **v2.0**: Add new Pydantic-based functions alongside old ones
- **v2.1-2.5**: Add deprecation warnings to old functions
- **v3.0**: Remove old functions, Pydantic-only API

---

## Testing Implications

All existing tests will need to be updated to handle new return types:

1. Tests expecting `bytes` from `create_map()` → expect `MapResult`
2. Tests expecting varying `dict` structures from `get_census_data()` → expect consistent structure
3. All tests should verify Pydantic validation errors are raised properly

---

## Documentation Needs

1. Update all docstrings to reflect new types
2. Create migration guide for users
3. Add examples for both old and new API
4. Update type stubs (`.pyi` files if they exist)
5. Add Pydantic schema documentation

---

## Benefits of This Refactor

1. **Predictability**: Users know exactly what they'll get back
2. **Type Safety**: Better IDE autocomplete and type checking
3. **Validation**: Automatic input validation with clear error messages
4. **Serialization**: Easy JSON serialization with Pydantic
5. **Documentation**: Auto-generated schema docs
6. **Testing**: Easier to mock and test with structured types

---

## Estimated Effort

- **Critical fixes** (create_map, get_census_data): 2-3 days
- **Pydantic request models**: 2-3 days
- **Pydantic response models**: 2-3 days
- **Tests updates**: 2-3 days
- **Documentation**: 1-2 days

**Total:** 9-14 days of focused development

---

## Next Steps

1. ✅ Complete this audit
2. Get feedback from maintainers on approach
3. Start with critical `create_map()` fix
4. Implement phase by phase
5. Maintain backward compatibility where possible
