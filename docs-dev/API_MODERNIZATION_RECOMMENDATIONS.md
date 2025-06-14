# SocialMapper API Modernization Recommendations

## 1. Current API Design Analysis

### Current State Overview
The SocialMapper API currently has several design challenges:

#### Function Signature Complexity
The main entry point `run_socialmapper()` has **22 parameters**, making it difficult to use and maintain:
```python
def run_socialmapper(
    run_config: Optional[RunConfig] = None,
    *,
    geocode_area: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    poi_type: Optional[str] = None,
    poi_name: Optional[str] = None,
    additional_tags: Optional[Dict] = None,
    travel_time: int = 15,
    geographic_level: str = "block-group",
    census_variables: List[str] | None = None,
    api_key: Optional[str] = None,
    output_dir: str = "output",
    custom_coords_path: Optional[str] = None,
    export_csv: bool = True,
    export_maps: bool = False,
    export_isochrones: bool = False,
    use_interactive_maps: bool = True,
    map_backend: str = "plotly",
    name_field: Optional[str] = None,
    type_field: Optional[str] = None,
    max_poi_count: Optional[int] = None
) -> Dict[str, Any]:
```

#### Configuration Models
- Two separate config models: `RunConfig` (minimal) and `PipelineConfig` (comprehensive)
- No clear separation between required and optional parameters
- Missing validation for mutually exclusive options

#### Return Types
- Returns untyped `Dict[str, Any]`
- No structured error responses
- No way to distinguish between success and partial success

#### Error Handling
- Basic exception propagation without structured error types
- No result types (Ok/Error pattern)
- Limited recovery mechanisms

#### Async Support
- Some async patterns exist (AsyncRateLimitedClient) but not exposed in main API
- Network operations are synchronous at the API level
- No streaming support for large datasets

## 2. Modern API Design Patterns Recommendations

### 2.1 Builder Pattern for Configuration

```python
from typing import Self, Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum

class GeographicLevel(Enum):
    BLOCK_GROUP = "block-group"
    ZCTA = "zcta"
    TRACT = "tract"
    COUNTY = "county"

class MapBackend(Enum):
    PLOTLY = "plotly"
    MATPLOTLIB = "matplotlib"
    FOLIUM = "folium"

@dataclass
class SocialMapperBuilder:
    """Fluent builder for SocialMapper configuration."""
    
    # POI Configuration
    _poi_source: Optional['POISource'] = None
    _travel_time: int = 15
    _max_poi_count: Optional[int] = None
    
    # Geographic Configuration
    _geographic_level: GeographicLevel = GeographicLevel.BLOCK_GROUP
    _census_variables: List[str] = field(default_factory=lambda: ["total_population"])
    _api_key: Optional[str] = None
    
    # Output Configuration
    _output_dir: str = "output"
    _exports: Dict[str, bool] = field(default_factory=lambda: {
        "csv": True,
        "maps": False,
        "isochrones": False,
        "interactive": True
    })
    _map_backend: MapBackend = MapBackend.PLOTLY
    
    def with_osm_pois(self, 
                      area: str,
                      state: str,
                      poi_type: str,
                      poi_name: str,
                      additional_tags: Optional[Dict] = None) -> Self:
        """Configure OpenStreetMap POI source."""
        self._poi_source = OSMPOISource(
            area=area,
            state=state,
            poi_type=poi_type,
            poi_name=poi_name,
            additional_tags=additional_tags or {}
        )
        return self
    
    def with_custom_pois(self,
                        file_path: str,
                        name_field: Optional[str] = None,
                        type_field: Optional[str] = None) -> Self:
        """Configure custom POI source from file."""
        self._poi_source = CustomPOISource(
            file_path=file_path,
            name_field=name_field,
            type_field=type_field
        )
        return self
    
    def with_travel_time(self, minutes: int) -> Self:
        """Set travel time for isochrones."""
        if not 1 <= minutes <= 120:
            raise ValueError("Travel time must be between 1 and 120 minutes")
        self._travel_time = minutes
        return self
    
    def with_census_variables(self, *variables: str) -> Self:
        """Add census variables to retrieve."""
        self._census_variables.extend(variables)
        return self
    
    def with_api_key(self, key: str) -> Self:
        """Set Census API key."""
        self._api_key = key
        return self
    
    def with_output_dir(self, path: str) -> Self:
        """Set output directory."""
        self._output_dir = path
        return self
    
    def enable_csv_export(self, enabled: bool = True) -> Self:
        """Enable/disable CSV export."""
        self._exports["csv"] = enabled
        return self
    
    def enable_map_export(self, enabled: bool = True) -> Self:
        """Enable/disable map generation."""
        self._exports["maps"] = enabled
        return self
    
    def enable_isochrone_export(self, enabled: bool = True) -> Self:
        """Enable/disable isochrone export."""
        self._exports["isochrones"] = enabled
        return self
    
    def with_map_backend(self, backend: MapBackend) -> Self:
        """Set map rendering backend."""
        self._map_backend = backend
        return self
    
    def limit_poi_count(self, max_count: int) -> Self:
        """Limit number of POIs to process."""
        self._max_poi_count = max_count
        return self
    
    def build(self) -> 'SocialMapperConfig':
        """Build and validate the configuration."""
        if self._poi_source is None:
            raise ValueError("POI source must be configured")
        
        return SocialMapperConfig(
            poi_source=self._poi_source,
            travel_time=self._travel_time,
            max_poi_count=self._max_poi_count,
            geographic_level=self._geographic_level,
            census_variables=self._census_variables,
            api_key=self._api_key,
            output_dir=self._output_dir,
            exports=self._exports,
            map_backend=self._map_backend
        )

# Usage example:
config = (SocialMapperBuilder()
    .with_osm_pois(
        area="San Francisco",
        state="CA",
        poi_type="amenity",
        poi_name="library"
    )
    .with_travel_time(20)
    .with_census_variables("median_income", "education_bachelors_plus")
    .enable_map_export()
    .enable_isochrone_export()
    .build()
)
```

### 2.2 Async/Await Support

```python
import asyncio
from typing import AsyncIterator, Optional
from dataclasses import dataclass

@dataclass
class AsyncSocialMapper:
    """Async version of SocialMapper for better I/O performance."""
    
    def __init__(self, config: SocialMapperConfig):
        self.config = config
        self._session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self._session = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session:
            await self._session.aclose()
    
    async def extract_pois(self) -> AsyncIterator[POI]:
        """Extract POIs asynchronously."""
        if isinstance(self.config.poi_source, OSMPOISource):
            async for poi in self._extract_osm_pois():
                yield poi
        else:
            # File-based extraction can be synchronous
            for poi in self._extract_custom_pois():
                yield poi
    
    async def _extract_osm_pois(self) -> AsyncIterator[POI]:
        """Extract POIs from OpenStreetMap."""
        # Use async HTTP client for Overpass API
        query = self._build_overpass_query()
        
        async with self._session.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            for element in data.get("elements", []):
                yield POI.from_osm_element(element)
    
    async def generate_isochrones(self, pois: List[POI]) -> AsyncIterator[Isochrone]:
        """Generate isochrones concurrently."""
        # Create tasks for concurrent processing
        tasks = [
            self._generate_single_isochrone(poi) 
            for poi in pois
        ]
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        # Yield results as they complete
        for coro in asyncio.as_completed([bounded_task(t) for t in tasks]):
            try:
                isochrone = await coro
                yield isochrone
            except Exception as e:
                # Log error but continue processing
                logger.error(f"Failed to generate isochrone: {e}")
    
    async def fetch_census_data(self, 
                               geographic_units: List[GeographicUnit]) -> AsyncIterator[CensusData]:
        """Fetch census data with streaming support."""
        # Batch requests for efficiency
        batch_size = 50
        
        for i in range(0, len(geographic_units), batch_size):
            batch = geographic_units[i:i + batch_size]
            
            # Create census API request
            params = self._build_census_params(batch)
            
            async with self._session.get(
                "https://api.census.gov/data/2021/acs/acs5",
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                # Parse and yield census data
                for row in self._parse_census_response(data):
                    yield row

# Usage example:
async def main():
    config = (SocialMapperBuilder()
        .with_osm_pois("San Francisco", "CA", "amenity", "library")
        .with_census_variables("median_income", "population")
        .build()
    )
    
    async with AsyncSocialMapper(config) as mapper:
        # Extract POIs
        pois = []
        async for poi in mapper.extract_pois():
            pois.append(poi)
            print(f"Found POI: {poi.name}")
        
        # Generate isochrones concurrently
        isochrones = []
        async for isochrone in mapper.generate_isochrones(pois):
            isochrones.append(isochrone)
            print(f"Generated isochrone for: {isochrone.poi.name}")
        
        # Stream census data
        async for census_data in mapper.fetch_census_data(geographic_units):
            print(f"Census data: {census_data}")

# Run async
asyncio.run(main())
```

### 2.3 Result Types (Ok/Error Pattern)

```python
from typing import Generic, TypeVar, Union, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

T = TypeVar('T')
E = TypeVar('E')

class Result(ABC, Generic[T, E]):
    """Base class for Result type."""
    
    @abstractmethod
    def is_ok(self) -> bool:
        """Check if result is Ok."""
        pass
    
    @abstractmethod
    def is_err(self) -> bool:
        """Check if result is Error."""
        pass
    
    @abstractmethod
    def unwrap(self) -> T:
        """Get the value or raise if error."""
        pass
    
    @abstractmethod
    def unwrap_err(self) -> E:
        """Get the error or raise if ok."""
        pass
    
    @abstractmethod
    def map(self, func) -> 'Result':
        """Map function over Ok value."""
        pass
    
    @abstractmethod
    def map_err(self, func) -> 'Result':
        """Map function over Error value."""
        pass

@dataclass
class Ok(Result[T, E]):
    """Success result."""
    value: T
    
    def is_ok(self) -> bool:
        return True
    
    def is_err(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_err(self) -> E:
        raise ValueError("Called unwrap_err on Ok value")
    
    def map(self, func):
        return Ok(func(self.value))
    
    def map_err(self, func):
        return self
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def and_then(self, func):
        """Flatmap for Result."""
        return func(self.value)

@dataclass
class Err(Result[T, E]):
    """Error result."""
    error: E
    
    def is_ok(self) -> bool:
        return False
    
    def is_err(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on Err value: {self.error}")
    
    def unwrap_err(self) -> E:
        return self.error
    
    def map(self, func):
        return self
    
    def map_err(self, func):
        return Err(func(self.error))
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def and_then(self, func):
        return self

# Error types
@dataclass
class SocialMapperError:
    """Base error type for SocialMapper."""
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError(SocialMapperError):
    """Input validation error."""
    field: str
    constraint: str

@dataclass
class APIError(SocialMapperError):
    """External API error."""
    service: str
    status_code: Optional[int] = None
    retry_after: Optional[int] = None

@dataclass
class ProcessingError(SocialMapperError):
    """Processing pipeline error."""
    stage: str
    cause: Optional[Exception] = None

# Updated API with Result types
class SocialMapperAPI:
    """Modern API with Result types."""
    
    def validate_config(self, config: SocialMapperConfig) -> Result[None, ValidationError]:
        """Validate configuration."""
        # Check POI source
        if config.poi_source is None:
            return Err(ValidationError(
                message="POI source is required",
                code="MISSING_POI_SOURCE",
                field="poi_source",
                constraint="required"
            ))
        
        # Check travel time
        if not 1 <= config.travel_time <= 120:
            return Err(ValidationError(
                message="Travel time must be between 1 and 120 minutes",
                code="INVALID_TRAVEL_TIME",
                field="travel_time",
                constraint="range[1,120]"
            ))
        
        # Check API key if census variables specified
        if config.census_variables and not config.api_key:
            return Err(ValidationError(
                message="Census API key required when census variables specified",
                code="MISSING_API_KEY",
                field="api_key",
                constraint="required_with:census_variables"
            ))
        
        return Ok(None)
    
    def extract_pois(self, config: SocialMapperConfig) -> Result[List[POI], ProcessingError]:
        """Extract POIs with error handling."""
        try:
            if isinstance(config.poi_source, OSMPOISource):
                pois = self._extract_osm_pois(config.poi_source)
            else:
                pois = self._extract_custom_pois(config.poi_source)
            
            if not pois:
                return Err(ProcessingError(
                    message="No POIs found",
                    code="NO_POIS_FOUND",
                    stage="extraction"
                ))
            
            return Ok(pois)
            
        except Exception as e:
            return Err(ProcessingError(
                message=f"Failed to extract POIs: {str(e)}",
                code="POI_EXTRACTION_FAILED",
                stage="extraction",
                cause=e
            ))
    
    def run_pipeline(self, config: SocialMapperConfig) -> Result[PipelineResult, SocialMapperError]:
        """Run complete pipeline with Result type."""
        # Validate configuration
        validation = self.validate_config(config)
        if validation.is_err():
            return validation
        
        # Extract POIs
        poi_result = self.extract_pois(config)
        if poi_result.is_err():
            return poi_result
        
        pois = poi_result.unwrap()
        
        # Continue with pipeline...
        return Ok(PipelineResult(
            pois=pois,
            isochrones=[],
            census_data={},
            outputs={}
        ))

# Usage with error handling
api = SocialMapperAPI()
result = api.run_pipeline(config)

match result:
    case Ok(pipeline_result):
        print(f"Success! Found {len(pipeline_result.pois)} POIs")
    case Err(ValidationError() as e):
        print(f"Validation error: {e.message} (field: {e.field})")
    case Err(APIError() as e):
        print(f"API error from {e.service}: {e.message}")
        if e.retry_after:
            print(f"Retry after {e.retry_after} seconds")
    case Err(ProcessingError() as e):
        print(f"Processing error in {e.stage}: {e.message}")
```

### 2.4 Context Managers for Resource Management

```python
from contextlib import contextmanager, asynccontextmanager
from typing import Iterator, AsyncIterator
import tempfile
import shutil

class SocialMapperSession:
    """Context manager for SocialMapper session with resource management."""
    
    def __init__(self, config: SocialMapperConfig):
        self.config = config
        self._temp_dir: Optional[str] = None
        self._cache_manager: Optional[CacheManager] = None
        self._http_client: Optional[httpx.Client] = None
        self._db_connection: Optional[Any] = None
    
    def __enter__(self) -> 'SocialMapperSession':
        """Initialize resources."""
        # Create temporary directory for intermediate files
        self._temp_dir = tempfile.mkdtemp(prefix="socialmapper_")
        
        # Initialize cache manager
        self._cache_manager = CacheManager(
            cache_dir=os.path.join(self._temp_dir, "cache"),
            max_size_mb=500
        )
        
        # Create HTTP client with connection pooling
        self._http_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20
            )
        )
        
        # Initialize database connection if needed
        if self.config.use_database:
            self._db_connection = self._init_database()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources."""
        # Close HTTP client
        if self._http_client:
            self._http_client.close()
        
        # Close database connection
        if self._db_connection:
            self._db_connection.close()
        
        # Save cache statistics
        if self._cache_manager:
            self._cache_manager.save_statistics()
        
        # Clean up temporary directory
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)
    
    @contextmanager
    def transaction(self) -> Iterator['Transaction']:
        """Create a transaction context."""
        transaction = Transaction(self)
        try:
            yield transaction
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
    
    def run_with_progress(self, pipeline: Pipeline) -> PipelineResult:
        """Run pipeline with progress tracking."""
        with self.transaction() as tx:
            # Setup progress tracking
            progress = ProgressTracker(total_stages=len(pipeline.stages))
            
            for stage in pipeline.stages:
                with progress.stage(stage.name):
                    result = stage.run(self, tx)
                    tx.save_checkpoint(stage.name, result)
            
            return tx.get_result()

# Async context manager
@asynccontextmanager
async def async_socialmapper_session(config: SocialMapperConfig) -> AsyncIterator[AsyncSocialMapperSession]:
    """Async context manager for SocialMapper."""
    session = AsyncSocialMapperSession(config)
    
    # Initialize async resources
    session._http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=10)
    )
    
    try:
        yield session
    finally:
        # Cleanup async resources
        await session._http_client.aclose()
        if session._cache_manager:
            await session._cache_manager.flush()

# Usage examples
# Synchronous
with SocialMapperSession(config) as session:
    result = session.run_with_progress(pipeline)
    print(f"Processed {len(result.pois)} POIs")

# Asynchronous
async with async_socialmapper_session(config) as session:
    async for poi in session.stream_pois():
        print(f"Processing POI: {poi.name}")
```

### 2.5 Type Safety with Generics and Protocols

```python
from typing import Protocol, TypeVar, Generic, List, Dict, Any
from abc import abstractmethod

T = TypeVar('T')
P = TypeVar('P', bound='POIProtocol')
I = TypeVar('I', bound='IsochroneProtocol')
C = TypeVar('C', bound='CensusDataProtocol')

class POIProtocol(Protocol):
    """Protocol for POI objects."""
    name: str
    latitude: float
    longitude: float
    type: str
    
    def to_dict(self) -> Dict[str, Any]: ...
    def distance_to(self, other: 'POIProtocol') -> float: ...

class IsochroneProtocol(Protocol):
    """Protocol for isochrone objects."""
    poi: POIProtocol
    travel_time: int
    geometry: Any  # shapely geometry
    
    def contains_point(self, lat: float, lon: float) -> bool: ...
    def area_sq_km(self) -> float: ...

class CensusDataProtocol(Protocol):
    """Protocol for census data objects."""
    geographic_id: str
    variables: Dict[str, Any]
    
    def get_variable(self, code: str) -> Any: ...
    def get_population(self) -> int: ...

class DataProcessor(Generic[T]):
    """Generic data processor."""
    
    def __init__(self, transformer: Callable[[T], T]):
        self.transformer = transformer
    
    def process(self, items: List[T]) -> List[T]:
        """Process a list of items."""
        return [self.transformer(item) for item in items]
    
    def process_parallel(self, items: List[T], max_workers: int = 4) -> List[T]:
        """Process items in parallel."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.transformer, item) for item in items]
            return [future.result() for future in as_completed(futures)]

class Pipeline(Generic[P, I, C]):
    """Type-safe pipeline with generics."""
    
    def __init__(self,
                 poi_extractor: 'POIExtractor[P]',
                 isochrone_generator: 'IsochroneGenerator[P, I]',
                 census_integrator: 'CensusIntegrator[I, C]'):
        self.poi_extractor = poi_extractor
        self.isochrone_generator = isochrone_generator
        self.census_integrator = census_integrator
    
    def run(self) -> 'PipelineResult[P, I, C]':
        """Run the pipeline with type safety."""
        # Extract POIs
        pois: List[P] = self.poi_extractor.extract()
        
        # Generate isochrones
        isochrones: List[I] = self.isochrone_generator.generate(pois)
        
        # Integrate census data
        census_data: List[C] = self.census_integrator.integrate(isochrones)
        
        return PipelineResult(
            pois=pois,
            isochrones=isochrones,
            census_data=census_data
        )

@dataclass
class PipelineResult(Generic[P, I, C]):
    """Type-safe pipeline result."""
    pois: List[P]
    isochrones: List[I]
    census_data: List[C]
    
    def filter_pois(self, predicate: Callable[[P], bool]) -> List[P]:
        """Filter POIs with type safety."""
        return [poi for poi in self.pois if predicate(poi)]
    
    def get_census_by_geography(self, geography_id: str) -> Optional[C]:
        """Get census data by geography ID."""
        for data in self.census_data:
            if data.geographic_id == geography_id:
                return data
        return None

# Concrete implementations
class OSMPOIExtractor(Generic[P]):
    """OpenStreetMap POI extractor."""
    
    def __init__(self, config: OSMConfig, poi_factory: Callable[..., P]):
        self.config = config
        self.poi_factory = poi_factory
    
    def extract(self) -> List[P]:
        """Extract POIs from OSM."""
        # Implementation...
        return []

# Type-safe usage
def create_pipeline() -> Pipeline[CustomPOI, CustomIsochrone, CustomCensusData]:
    """Create a type-safe pipeline."""
    return Pipeline(
        poi_extractor=OSMPOIExtractor(osm_config, CustomPOI.from_osm),
        isochrone_generator=CustomIsochroneGenerator(),
        census_integrator=CustomCensusIntegrator()
    )

# Usage with type checking
pipeline = create_pipeline()
result = pipeline.run()

# Type checker knows these types
for poi in result.pois:  # poi: CustomPOI
    print(poi.custom_attribute)  # Type-safe access

for isochrone in result.isochrones:  # isochrone: CustomIsochrone
    area = isochrone.calculate_custom_area()  # Type-safe method
```

### 2.6 Dependency Injection

```python
from typing import Protocol, Optional
from dataclasses import dataclass
import inject

# Define service protocols
class HTTPClientProtocol(Protocol):
    """Protocol for HTTP clients."""
    def get(self, url: str, **kwargs) -> Any: ...
    def post(self, url: str, **kwargs) -> Any: ...

class CacheProtocol(Protocol):
    """Protocol for caching."""
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...

class LoggerProtocol(Protocol):
    """Protocol for logging."""
    def info(self, message: str) -> None: ...
    def error(self, message: str, exc_info: bool = False) -> None: ...

# Service implementations
@dataclass
class ServiceContainer:
    """Dependency injection container."""
    http_client: HTTPClientProtocol
    cache: CacheProtocol
    logger: LoggerProtocol
    config: SocialMapperConfig

# Configure injection
def configure_injection(config: SocialMapperConfig):
    """Configure dependency injection."""
    def config_func(binder: inject.Binder):
        # Bind interfaces to implementations
        binder.bind(HTTPClientProtocol, RateLimitedClient(service="socialmapper"))
        binder.bind(CacheProtocol, RedisCache() if config.use_redis else InMemoryCache())
        binder.bind(LoggerProtocol, StructuredLogger())
        binder.bind(SocialMapperConfig, config)
        
        # Bind service container
        binder.bind_to_constructor(ServiceContainer, lambda: ServiceContainer(
            http_client=inject.instance(HTTPClientProtocol),
            cache=inject.instance(CacheProtocol),
            logger=inject.instance(LoggerProtocol),
            config=inject.instance(SocialMapperConfig)
        ))
    
    inject.configure(config_func)

# Services using dependency injection
class POIExtractorService:
    """POI extraction service with injected dependencies."""
    
    @inject.params(container=ServiceContainer)
    def __init__(self, container: ServiceContainer):
        self.http_client = container.http_client
        self.cache = container.cache
        self.logger = container.logger
        self.config = container.config
    
    def extract_pois(self) -> Result[List[POI], ProcessingError]:
        """Extract POIs using injected services."""
        # Check cache first
        cache_key = self._generate_cache_key()
        cached_pois = self.cache.get(cache_key)
        
        if cached_pois:
            self.logger.info("Using cached POIs")
            return Ok(cached_pois)
        
        try:
            # Extract from source
            self.logger.info("Extracting POIs from source")
            response = self.http_client.get(self._build_query_url())
            pois = self._parse_response(response)
            
            # Cache results
            self.cache.set(cache_key, pois, ttl=3600)
            
            return Ok(pois)
            
        except Exception as e:
            self.logger.error(f"POI extraction failed: {e}", exc_info=True)
            return Err(ProcessingError(
                message=str(e),
                code="POI_EXTRACTION_FAILED",
                stage="extraction"
            ))

class IsochroneGeneratorService:
    """Isochrone generation with dependency injection."""
    
    @inject.params(
        http_client=HTTPClientProtocol,
        cache=CacheProtocol,
        logger=LoggerProtocol
    )
    def __init__(self, 
                 http_client: HTTPClientProtocol,
                 cache: CacheProtocol,
                 logger: LoggerProtocol):
        self.http_client = http_client
        self.cache = cache
        self.logger = logger
    
    async def generate_isochrone(self, poi: POI) -> Result[Isochrone, ProcessingError]:
        """Generate isochrone for a POI."""
        # Implementation with injected dependencies
        pass

# Factory pattern with DI
class ServiceFactory:
    """Factory for creating services with dependency injection."""
    
    @staticmethod
    @inject.params(container=ServiceContainer)
    def create_poi_extractor(container: ServiceContainer) -> POIExtractorService:
        """Create POI extractor with dependencies."""
        return POIExtractorService()
    
    @staticmethod
    @inject.params(container=ServiceContainer)
    def create_pipeline(container: ServiceContainer) -> Pipeline:
        """Create complete pipeline with dependencies."""
        return Pipeline(
            poi_extractor=ServiceFactory.create_poi_extractor(),
            isochrone_generator=IsochroneGeneratorService(),
            census_integrator=CensusIntegratorService()
        )

# Usage
config = SocialMapperConfig(...)
configure_injection(config)

# Services are automatically injected
poi_service = POIExtractorService()  # Dependencies injected
result = poi_service.extract_pois()
```

### 2.7 API Versioning Strategy

```python
from typing import Union
from fastapi import FastAPI, APIRouter, Header, HTTPException
from pydantic import BaseModel
import semver

# Version-specific request/response models
class POIRequestV1(BaseModel):
    """V1 POI request model."""
    area: str
    poi_type: str
    poi_name: str

class POIRequestV2(BaseModel):
    """V2 POI request model with additional fields."""
    area: str
    poi_type: str
    poi_name: str
    tags: Dict[str, str] = {}
    max_results: int = 100

# API versioning with headers
app = FastAPI(title="SocialMapper API")

# Version routers
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

@v1_router.post("/extract-pois")
async def extract_pois_v1(request: POIRequestV1):
    """V1 API endpoint."""
    # V1 implementation
    return {"version": "1.0", "pois": []}

@v2_router.post("/extract-pois")
async def extract_pois_v2(request: POIRequestV2):
    """V2 API endpoint with enhanced features."""
    # V2 implementation with tags and max_results
    return {"version": "2.0", "pois": [], "total": 0}

# Header-based versioning
@app.post("/api/extract-pois")
async def extract_pois(
    request: Union[POIRequestV1, POIRequestV2],
    api_version: str = Header(default="1.0", alias="X-API-Version")
):
    """Version-aware endpoint."""
    version = semver.VersionInfo.parse(api_version)
    
    if version.major == 1:
        return await extract_pois_v1(POIRequestV1(**request.dict()))
    elif version.major == 2:
        return await extract_pois_v2(POIRequestV2(**request.dict()))
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported API version: {api_version}"
        )

# SDK versioning
class SocialMapperSDK:
    """Versioned SDK for SocialMapper."""
    
    VERSION = "2.0.0"
    SUPPORTED_API_VERSIONS = ["1.0", "1.1", "2.0"]
    
    def __init__(self, api_version: Optional[str] = None):
        self.api_version = api_version or self.VERSION
        self._validate_version()
    
    def _validate_version(self):
        """Validate API version compatibility."""
        if self.api_version not in self.SUPPORTED_API_VERSIONS:
            raise ValueError(
                f"API version {self.api_version} not supported. "
                f"Supported versions: {self.SUPPORTED_API_VERSIONS}"
            )
    
    @property
    def poi_extractor(self) -> 'POIExtractor':
        """Get version-appropriate POI extractor."""
        version = semver.VersionInfo.parse(self.api_version)
        
        if version.major == 1:
            return POIExtractorV1()
        else:
            return POIExtractorV2()

# Deprecation warnings
import warnings
from functools import wraps

def deprecated(version: str, alternative: str):
    """Decorator for marking deprecated functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated as of version {version}. "
                f"Use {alternative} instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

@deprecated(version="2.0.0", alternative="SocialMapperBuilder")
def create_socialmapper_config(**kwargs):
    """Legacy configuration function."""
    return SocialMapperConfig(**kwargs)
```

## 3. Best Practices Evaluation

### 3.1 REST/GraphQL-style API Design

```python
# REST API with FastAPI
from fastapi import FastAPI, Query, Path, Body
from typing import List, Optional

app = FastAPI(
    title="SocialMapper API",
    version="2.0.0",
    description="Community mapping and analysis API"
)

# RESTful endpoints
@app.post("/api/v2/analyses", response_model=AnalysisResponse)
async def create_analysis(request: CreateAnalysisRequest):
    """Create a new analysis job."""
    job_id = await analysis_service.create_job(request)
    return AnalysisResponse(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow()
    )

@app.get("/api/v2/analyses/{job_id}", response_model=AnalysisResponse)
async def get_analysis(job_id: str = Path(..., description="Analysis job ID")):
    """Get analysis status and results."""
    return await analysis_service.get_job(job_id)

@app.get("/api/v2/pois", response_model=List[POIResponse])
async def list_pois(
    area: str = Query(..., description="Geographic area"),
    poi_type: str = Query(..., description="POI type"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Result offset")
):
    """List POIs with pagination."""
    return await poi_service.list_pois(area, poi_type, limit, offset)

# GraphQL with Strawberry
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class POI:
    id: str
    name: str
    latitude: float
    longitude: float
    type: str
    tags: Dict[str, str]

@strawberry.type
class Isochrone:
    id: str
    poi: POI
    travel_time: int
    area_sq_km: float
    population_covered: int

@strawberry.type
class Query:
    @strawberry.field
    async def pois(
        self,
        area: str,
        poi_type: str,
        limit: int = 100
    ) -> List[POI]:
        """Query POIs."""
        return await poi_service.query_pois(area, poi_type, limit)
    
    @strawberry.field
    async def isochrone(self, poi_id: str, travel_time: int) -> Isochrone:
        """Get isochrone for a POI."""
        return await isochrone_service.get_isochrone(poi_id, travel_time)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_analysis(
        self,
        area: str,
        poi_types: List[str],
        travel_time: int,
        census_variables: List[str]
    ) -> AnalysisJob:
        """Create a new analysis."""
        return await analysis_service.create_analysis(
            area, poi_types, travel_time, census_variables
        )

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

### 3.2 Input Validation and Sanitization

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Optional, Literal
import re

class CoordinateValidator:
    """Reusable coordinate validation."""
    
    @staticmethod
    def validate_latitude(lat: float) -> float:
        if not -90 <= lat <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return lat
    
    @staticmethod
    def validate_longitude(lon: float) -> float:
        if not -180 <= lon <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return lon

class POICreateRequest(BaseModel):
    """Validated POI creation request."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="POI name"
    )
    
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude in decimal degrees"
    )
    
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude in decimal degrees"
    )
    
    poi_type: Literal["amenity", "leisure", "shop", "tourism"] = Field(
        ...,
        description="POI type category"
    )
    
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional tags"
    )
    
    @validator('name')
    def sanitize_name(cls, v: str) -> str:
        """Sanitize POI name."""
        # Remove dangerous characters
        v = re.sub(r'[<>\"\';&]', '', v)
        # Normalize whitespace
        v = ' '.join(v.split())
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate and sanitize tags."""
        # Limit number of tags
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        
        # Sanitize tag keys and values
        sanitized = {}
        for key, value in v.items():
            # Validate key format
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{0,49}$', key):
                raise ValueError(f"Invalid tag key: {key}")
            
            # Sanitize value
            sanitized[key] = re.sub(r'[<>\"\';&]', '', str(value))[:255]
        
        return sanitized

class AnalysisConfigRequest(BaseModel):
    """Validated analysis configuration."""
    
    area: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Geographic area name"
    )
    
    state: str = Field(
        ...,
        regex=r'^[A-Z]{2}$',
        description="Two-letter state code"
    )
    
    poi_types: List[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="POI types to analyze"
    )
    
    travel_time: int = Field(
        15,
        ge=1,
        le=120,
        description="Travel time in minutes"
    )
    
    census_variables: List[str] = Field(
        default_factory=lambda: ["total_population"],
        max_items=50,
        description="Census variables to retrieve"
    )
    
    output_formats: List[Literal["csv", "json", "parquet"]] = Field(
        ["csv"],
        description="Output formats"
    )
    
    @validator('area')
    def sanitize_area(cls, v: str) -> str:
        """Sanitize area name."""
        # Remove special characters except spaces, hyphens, and apostrophes
        v = re.sub(r'[^a-zA-Z0-9\s\-\']', '', v)
        return v.strip()
    
    @validator('census_variables', each_item=True)
    def validate_census_variable(cls, v: str) -> str:
        """Validate census variable format."""
        # Check if it's a known friendly name or valid code
        if v in CENSUS_VARIABLE_MAPPING:
            return CENSUS_VARIABLE_MAPPING[v]
        
        # Validate census code format (e.g., B01003_001E)
        if not re.match(r'^[A-Z]\d{5}_\d{3}[A-Z]$', v):
            raise ValueError(f"Invalid census variable: {v}")
        
        return v
    
    @root_validator
    def validate_configuration(cls, values):
        """Cross-field validation."""
        # Ensure travel time is reasonable for the area
        area = values.get('area', '')
        travel_time = values.get('travel_time', 15)
        
        # Large areas might need longer travel times
        if 'county' in area.lower() and travel_time < 30:
            values['travel_time'] = 30
        
        return values

# File upload validation
class FileUploadValidator:
    """Validate uploaded files."""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.csv', '.json', '.geojson', '.xlsx'}
    
    @classmethod
    def validate_file(cls, file: UploadFile) -> Result[None, ValidationError]:
        """Validate uploaded file."""
        # Check file extension
        ext = Path(file.filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            return Err(ValidationError(
                message=f"File type {ext} not allowed",
                code="INVALID_FILE_TYPE",
                field="file",
                constraint=f"allowed_types:{cls.ALLOWED_EXTENSIONS}"
            ))
        
        # Check file size
        if file.size > cls.MAX_FILE_SIZE:
            return Err(ValidationError(
                message=f"File too large: {file.size} bytes",
                code="FILE_TOO_LARGE",
                field="file",
                constraint=f"max_size:{cls.MAX_FILE_SIZE}"
            ))
        
        # Validate content based on type
        if ext == '.csv':
            return cls._validate_csv_content(file)
        elif ext in {'.json', '.geojson'}:
            return cls._validate_json_content(file)
        
        return Ok(None)
```

### 3.3 Rate Limiting and Throttling

```python
from fastapi import FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from datetime import datetime, timedelta

# Configure rate limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Different rate limits for different endpoints
@app.get("/api/v2/pois")
@limiter.limit("100/hour")
async def list_pois(request: Request):
    """List POIs with rate limiting."""
    return {"pois": []}

@app.post("/api/v2/analyses")
@limiter.limit("10/hour")
async def create_analysis(request: Request):
    """Create analysis with stricter rate limit."""
    return {"job_id": "..."}

# Custom rate limiting with user tiers
class TieredRateLimiter:
    """Rate limiter with user tiers."""
    
    TIERS = {
        "free": {"requests_per_hour": 100, "burst": 10},
        "basic": {"requests_per_hour": 1000, "burst": 50},
        "premium": {"requests_per_hour": 10000, "burst": 200},
        "enterprise": {"requests_per_hour": 100000, "burst": 1000}
    }
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_rate_limit(self, user_id: str, tier: str) -> bool:
        """Check if user is within rate limits."""
        limits = self.TIERS.get(tier, self.TIERS["free"])
        
        # Use sliding window algorithm
        now = datetime.utcnow()
        window_start = now - timedelta(hours=1)
        
        # Count requests in the last hour
        key = f"rate_limit:{user_id}"
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        
        # Count current entries
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
        
        # Set expiry
        pipe.expire(key, 3600)
        
        results = pipe.execute()
        request_count = results[1]
        
        # Check burst limit
        burst_key = f"burst:{user_id}"
        burst_count = self.redis.incr(burst_key)
        if burst_count == 1:
            self.redis.expire(burst_key, 60)  # 1 minute window
        
        if burst_count > limits["burst"]:
            raise HTTPException(
                status_code=429,
                detail="Burst limit exceeded",
                headers={"Retry-After": "60"}
            )
        
        if request_count >= limits["requests_per_hour"]:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "3600"}
            )
        
        return True

# Middleware for API key validation and rate limiting
@app.middleware("http")
async def api_key_and_rate_limit_middleware(request: Request, call_next):
    """Validate API key and apply rate limits."""
    # Skip for health checks
    if request.url.path == "/health":
        return await call_next(request)
    
    # Extract API key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": "API key required"}
        )
    
    # Validate API key and get user info
    user_info = await validate_api_key(api_key)
    if not user_info:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid API key"}
        )
    
    # Apply rate limiting based on tier
    rate_limiter = TieredRateLimiter(redis_client)
    await rate_limiter.check_rate_limit(
        user_info["user_id"],
        user_info["tier"]
    )
    
    # Add user info to request state
    request.state.user_info = user_info
    
    # Continue processing
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(
        rate_limiter.TIERS[user_info["tier"]]["requests_per_hour"]
    )
    response.headers["X-RateLimit-Remaining"] = "..."  # Calculate remaining
    response.headers["X-RateLimit-Reset"] = "..."  # Next reset time
    
    return response
```

### 3.4 Caching Strategies

```python
from functools import lru_cache, wraps
from typing import Optional, Any, Callable
import hashlib
import pickle
from datetime import datetime, timedelta

class CacheStrategy:
    """Base cache strategy."""
    
    def get_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key."""
        # Create unique key from function and arguments
        key_parts = [
            func.__module__,
            func.__name__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        key_string = ":".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def should_cache(self, result: Any) -> bool:
        """Determine if result should be cached."""
        return True
    
    def get_ttl(self, result: Any) -> Optional[int]:
        """Get TTL for cached result."""
        return 3600  # 1 hour default

class MultiLevelCache:
    """Multi-level caching system."""
    
    def __init__(self):
        self.memory_cache = {}  # L1: In-memory
        self.redis_client = redis.Redis()  # L2: Redis
        self.s3_client = boto3.client('s3')  # L3: S3 for large objects
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache, checking all levels."""
        # Check L1 (memory)
        if key in self.memory_cache:
            return self.memory_cache[key]["value"]
        
        # Check L2 (Redis)
        redis_value = self.redis_client.get(key)
        if redis_value:
            value = pickle.loads(redis_value)
            # Promote to L1
            self.memory_cache[key] = {
                "value": value,
                "expires": datetime.utcnow() + timedelta(minutes=5)
            }
            return value
        
        # Check L3 (S3)
        try:
            response = self.s3_client.get_object(
                Bucket="socialmapper-cache",
                Key=f"cache/{key}"
            )
            value = pickle.loads(response['Body'].read())
            # Promote to L2 and L1
            self.redis_client.setex(key, 3600, pickle.dumps(value))
            self.memory_cache[key] = {
                "value": value,
                "expires": datetime.utcnow() + timedelta(minutes=5)
            }
            return value
        except:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set in cache at appropriate level."""
        serialized = pickle.dumps(value)
        size = len(serialized)
        
        # Small objects go to all levels
        if size < 1024 * 1024:  # 1MB
            # L1: Memory
            self.memory_cache[key] = {
                "value": value,
                "expires": datetime.utcnow() + timedelta(seconds=ttl)
            }
            
            # L2: Redis
            self.redis_client.setex(key, ttl, serialized)
        
        # Large objects go to S3
        if size > 100 * 1024:  # 100KB
            self.s3_client.put_object(
                Bucket="socialmapper-cache",
                Key=f"cache/{key}",
                Body=serialized,
                Metadata={"ttl": str(ttl)}
            )

# Decorator for caching
def cached(
    strategy: CacheStrategy = CacheStrategy(),
    cache: Optional[MultiLevelCache] = None
):
    """Decorator for caching function results."""
    if cache is None:
        cache = MultiLevelCache()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = strategy.get_key(func, args, kwargs)
            
            # Check cache
            cached_result = await cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache if appropriate
            if strategy.should_cache(result):
                ttl = strategy.get_ttl(result)
                await cache.set(key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Synchronous version
            key = strategy.get_key(func, args, kwargs)
            
            # Simple in-memory cache for sync
            if not hasattr(func, '_cache'):
                func._cache = {}
            
            if key in func._cache:
                return func._cache[key]
            
            result = func(*args, **kwargs)
            
            if strategy.should_cache(result):
                func._cache[key] = result
            
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Specialized caching strategies
class GeocodingCacheStrategy(CacheStrategy):
    """Caching strategy for geocoding results."""
    
    def get_ttl(self, result: Any) -> Optional[int]:
        """Geocoding results can be cached for a long time."""
        return 30 * 24 * 3600  # 30 days
    
    def get_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Normalize address for consistent caching."""
        if args and isinstance(args[0], str):
            # Normalize address
            address = args[0].lower().strip()
            address = ' '.join(address.split())
            return hashlib.sha256(address.encode()).hexdigest()
        return super().get_key(func, args, kwargs)

class IsochroneCacheStrategy(CacheStrategy):
    """Caching strategy for isochrones."""
    
    def should_cache(self, result: Any) -> bool:
        """Only cache successful isochrones."""
        return result is not None and hasattr(result, 'geometry')
    
    def get_ttl(self, result: Any) -> Optional[int]:
        """Isochrones valid for 7 days."""
        return 7 * 24 * 3600

# Usage
@cached(strategy=GeocodingCacheStrategy())
async def geocode_address(address: str) -> Optional[Coordinates]:
    """Geocode address with caching."""
    # Expensive geocoding operation
    return await geocoding_service.geocode(address)

@cached(strategy=IsochroneCacheStrategy())
async def generate_isochrone(poi: POI, travel_time: int) -> Optional[Isochrone]:
    """Generate isochrone with caching."""
    # Expensive isochrone generation
    return await isochrone_service.generate(poi, travel_time)
```

## 4. Specific Improvements Implementation

### 4.1 Simplified Function Signature

```python
# Instead of 22 parameters, use a single configuration object
class SocialMapper:
    """Modern SocialMapper API."""
    
    def __init__(self, config: Optional[SocialMapperConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or SocialMapperConfig()
    
    def run(self, 
            analysis: AnalysisRequest,
            options: Optional[RunOptions] = None) -> Result[AnalysisResult, SocialMapperError]:
        """
        Run analysis with simplified interface.
        
        Args:
            analysis: Analysis request configuration
            options: Optional runtime options
            
        Returns:
            Result containing analysis results or error
        """
        options = options or RunOptions()
        
        # Validate inputs
        validation = self._validate_analysis(analysis)
        if validation.is_err():
            return validation
        
        # Run pipeline
        try:
            result = self._run_pipeline(analysis, options)
            return Ok(result)
        except Exception as e:
            return Err(ProcessingError(
                message=str(e),
                code="PIPELINE_ERROR",
                stage="execution"
            ))
    
    @classmethod
    def from_builder(cls, builder: SocialMapperBuilder) -> 'SocialMapper':
        """Create from builder."""
        config = builder.build()
        return cls(config)

# Clean usage
mapper = SocialMapper.from_builder(
    SocialMapperBuilder()
    .with_osm_pois("San Francisco", "CA", "amenity", "library")
    .with_census_variables("median_income", "population")
    .enable_map_export()
)

result = mapper.run(
    AnalysisRequest(
        travel_time=20,
        geographic_level="block-group"
    )
)
```

### 4.2 Async Support Implementation

```python
class AsyncSocialMapper:
    """Fully async SocialMapper implementation."""
    
    async def run(self, 
                  analysis: AnalysisRequest) -> AsyncIterator[AnalysisEvent]:
        """
        Run analysis with streaming results.
        
        Yields:
            AnalysisEvent objects as processing progresses
        """
        # Start analysis
        yield AnalysisEvent(
            type="started",
            timestamp=datetime.utcnow(),
            data={"request": analysis}
        )
        
        # Extract POIs
        async with self._progress_context("Extracting POIs") as progress:
            pois = []
            async for poi in self._extract_pois_async(analysis):
                pois.append(poi)
                progress.update(len(pois))
                
                # Yield progress events
                if len(pois) % 10 == 0:
                    yield AnalysisEvent(
                        type="progress",
                        timestamp=datetime.utcnow(),
                        data={"stage": "extraction", "count": len(pois)}
                    )
        
        yield AnalysisEvent(
            type="stage_complete",
            timestamp=datetime.utcnow(),
            data={"stage": "extraction", "poi_count": len(pois)}
        )
        
        # Generate isochrones concurrently
        async with self._progress_context("Generating isochrones") as progress:
            isochrones = []
            async for isochrone in self._generate_isochrones_async(pois):
                isochrones.append(isochrone)
                progress.update(len(isochrones))
                
                yield AnalysisEvent(
                    type="isochrone_generated",
                    timestamp=datetime.utcnow(),
                    data={"poi": isochrone.poi.name}
                )
        
        # Stream census data
        async for census_batch in self._stream_census_data(isochrones):
            yield AnalysisEvent(
                type="census_data",
                timestamp=datetime.utcnow(),
                data={"batch_size": len(census_batch)}
            )
        
        # Final result
        yield AnalysisEvent(
            type="completed",
            timestamp=datetime.utcnow(),
            data={
                "poi_count": len(pois),
                "isochrone_count": len(isochrones)
            }
        )

# Usage with async iteration
async def process_analysis():
    mapper = AsyncSocialMapper(config)
    
    async for event in mapper.run(analysis_request):
        match event.type:
            case "started":
                print("Analysis started")
            case "progress":
                print(f"Progress: {event.data}")
            case "completed":
                print(f"Analysis completed: {event.data}")
            case _:
                print(f"Event: {event}")
```

### 4.3 Proper SDK Structure

```python
# socialmapper/
# ├── __init__.py
# ├── client.py          # Main client interface
# ├── models/            # Data models
# │   ├── __init__.py
# │   ├── poi.py
# │   ├── isochrone.py
# │   └── census.py
# ├── services/          # Service layer
# │   ├── __init__.py
# │   ├── extraction.py
# │   ├── analysis.py
# │   └── visualization.py
# ├── utils/             # Utilities
# │   ├── __init__.py
# │   ├── validation.py
# │   └── caching.py
# └── exceptions.py      # Custom exceptions

# socialmapper/client.py
class SocialMapperClient:
    """Main SDK client."""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: str = "https://api.socialmapper.io",
                 timeout: float = 30.0,
                 max_retries: int = 3):
        """
        Initialize SocialMapper client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or os.getenv("SOCIALMAPPER_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-API-Key": self.api_key} if self.api_key else {}
        )
        
        # Initialize services
        self.pois = POIService(self._client)
        self.isochrones = IsochroneService(self._client)
        self.census = CensusService(self._client)
        self.analysis = AnalysisService(self._client)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()
    
    def create_analysis(self) -> AnalysisBuilder:
        """Create a new analysis using builder pattern."""
        return AnalysisBuilder(self)

# socialmapper/services/analysis.py
class AnalysisService:
    """Analysis service."""
    
    def __init__(self, client: httpx.Client):
        self._client = client
    
    def create(self, request: AnalysisRequest) -> Result[AnalysisJob, APIError]:
        """Create a new analysis job."""
        try:
            response = self._client.post("/analyses", json=request.dict())
            response.raise_for_status()
            return Ok(AnalysisJob(**response.json()))
        except httpx.HTTPStatusError as e:
            return Err(APIError(
                message=f"Failed to create analysis: {e.response.text}",
                code="ANALYSIS_CREATE_FAILED",
                service="analysis",
                status_code=e.response.status_code
            ))
    
    def get_status(self, job_id: str) -> Result[JobStatus, APIError]:
        """Get analysis job status."""
        try:
            response = self._client.get(f"/analyses/{job_id}")
            response.raise_for_status()
            return Ok(JobStatus(**response.json()))
        except httpx.HTTPStatusError as e:
            return Err(APIError(
                message=f"Failed to get job status: {e.response.text}",
                code="JOB_STATUS_FAILED",
                service="analysis",
                status_code=e.response.status_code
            ))
    
    async def stream_results(self, job_id: str) -> AsyncIterator[AnalysisResult]:
        """Stream analysis results as they become available."""
        async with self._client.stream("GET", f"/analyses/{job_id}/stream") as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    yield AnalysisResult(**data)

# Usage
from socialmapper import SocialMapperClient

# Simple usage
with SocialMapperClient(api_key="your-api-key") as client:
    # Create analysis
    analysis = (client.create_analysis()
        .for_area("San Francisco", "CA")
        .with_pois("amenity", "library")
        .with_travel_time(20)
        .with_census_variables("median_income", "population")
        .build()
    )
    
    # Submit analysis
    result = client.analysis.create(analysis)
    
    if result.is_ok():
        job = result.unwrap()
        print(f"Analysis started: {job.id}")
        
        # Poll for results
        while True:
            status = client.analysis.get_status(job.id)
            if status.is_ok() and status.unwrap().is_complete:
                break
            time.sleep(5)
    else:
        print(f"Error: {result.unwrap_err()}")

# Async usage
async def run_analysis():
    async with AsyncSocialMapperClient(api_key="your-api-key") as client:
        # Stream results
        async for result in client.analysis.stream_results(job_id):
            print(f"Received: {result}")
```

## Summary

The modernization recommendations focus on:

1. **Simplifying the API** through builder patterns and configuration objects
2. **Adding async support** for better performance with I/O operations
3. **Implementing Result types** for explicit error handling
4. **Using context managers** for resource management
5. **Ensuring type safety** with generics and protocols
6. **Supporting dependency injection** for testability
7. **Implementing API versioning** for backward compatibility
8. **Adding comprehensive validation** and sanitization
9. **Including rate limiting** and caching strategies
10. **Creating a proper SDK structure** for ease of use

These improvements would make SocialMapper's API more modern, maintainable, and user-friendly while following current best practices in API design.