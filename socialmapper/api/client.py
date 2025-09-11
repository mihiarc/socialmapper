"""Simple, Pythonic SocialMapper client.

Clean API that eliminates over-engineering and follows Python conventions.
"""

import os
from pathlib import Path
from typing import Any

from ..console import get_logger
from ..pipeline import PipelineConfig, PipelineOrchestrator
from ..pipeline.poi_discovery import NearbyPOIDiscoveryConfig, execute_poi_discovery_pipeline
from ..util import CENSUS_VARIABLE_MAPPING, normalize_census_variable
from .exceptions import (
    AnalysisError,
    APIError,
    ValidationError,
    validate_location,
    validate_poi_types,
    validate_travel_time,
)
from .results import AnalysisResult, POIResult, create_analysis_result_from_pipeline_data

logger = get_logger(__name__)


class SocialMapper:
    """Simple, Pythonic client for SocialMapper analysis.
    
    This class provides a clean interface for spatial analysis without the 
    complexity of builders, result types, or forced context managers.
    
    Example:
        ```python
        # Simple initialization
        mapper = SocialMapper()
        
        # Direct analysis
        result = mapper.analyze_location(
            "San Francisco, CA",
            poi_types=["library", "school"],
            travel_time=15
        )
        
        print(f"Found {result.poi_count} POIs")
        result.print_summary()
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_enabled: bool = True,
        **config
    ):
        """Initialize SocialMapper client.
        
        Args:
            api_key: Census API key (optional, can also use CENSUS_API_KEY env var)
            cache_enabled: Enable caching for better performance
            **config: Additional configuration options
        """
        # Set up API key
        self.api_key = api_key or os.getenv('CENSUS_API_KEY')

        # Configuration
        self.config = {
            'cache_enabled': cache_enabled,
            'default_travel_time': 15,
            'default_travel_mode': 'drive',
            'default_output_dir': 'output',
            **config
        }

        logger.info("SocialMapper client initialized")

    def analyze_location(
        self,
        location: str | tuple[float, float],
        poi_types: list[str] | None = None,
        travel_time: int | None = None,
        travel_mode: str | None = None,
        census_variables: list[str] | None = None,
        output_dir: str | None = None,
        create_maps: bool = True,
        **options
    ) -> AnalysisResult:
        """Analyze accessibility and demographics for a location.
        
        Can perform POI discovery, demographic analysis, or both. If poi_types is None
        or empty, performs demographic-only analysis within the travel time area.
        
        Args:
            location: Location as "City, State" or (latitude, longitude)
            poi_types: Optional list of POI types (e.g., ["library", "school"]). 
                      None or empty list for demographic-only analysis
            travel_time: Travel time limit in minutes (1-120)
            travel_mode: Travel mode ("drive", "walk", "bike") 
            census_variables: Census variables to analyze
            output_dir: Output directory for files
            create_maps: Whether to create map visualizations
            **options: Additional analysis options
            
        Returns:
            AnalysisResult with analysis data and file paths
            
        Raises:
            ValidationError: If inputs are invalid
            AnalysisError: If analysis fails
            APIError: If external API calls fail
            
        Example:
            ```python
            result = mapper.analyze_location(
                "Portland, OR",
                poi_types=["library"],
                travel_time=20,
                census_variables=["total_population", "median_household_income"]
            )
            ```
        """
        try:
            # Apply defaults if None
            if travel_time is None:
                travel_time = self.config['default_travel_time']
            if travel_mode is None:
                travel_mode = self.config['default_travel_mode']
            if output_dir is None:
                output_dir = self.config['default_output_dir']
                
            # Validate inputs
            if isinstance(location, str):
                validate_location(location)
                city, state = [part.strip() for part in location.split(",")]
                lat, lon = None, None
            elif isinstance(location, (tuple, list)) and len(location) == 2:
                lat, lon = location
                # Validate coordinates
                if not (-90 <= lat <= 90):
                    raise ValidationError(
                        "Invalid coordinates",
                        field="location",
                        value=location
                    )
                if not (-180 <= lon <= 180):
                    raise ValidationError(
                        "Invalid coordinates", 
                        field="location",
                        value=location
                    )
                city, state = None, None
            else:
                raise ValidationError(
                    "Location must be 'City, State' string or (lat, lon) tuple",
                    field="location",
                    value=location
                )

            validate_travel_time(travel_time)

            if travel_mode not in ["drive", "walk", "bike"]:
                raise ValidationError(
                    "Travel mode must be 'drive', 'walk', or 'bike'",
                    field="travel_mode",
                    value=travel_mode,
                    valid_options=["drive", "walk", "bike"]
                )

            # POI types are optional - allow None or empty list for demographic-only analysis
            if poi_types is not None:
                validate_poi_types(poi_types)
                # Empty list is allowed (user explicitly wants no POI search)

            # Validate census variables
            if census_variables:
                normalized_vars = []
                for var in census_variables:
                    try:
                        normalized = normalize_census_variable(var)
                        normalized_vars.append(normalized)
                    except Exception as e:
                        available_vars = list(CENSUS_VARIABLE_MAPPING.keys())
                        raise ValidationError(
                            f"Invalid census variable: {var}",
                            field="census_variables",
                            value=var,
                            valid_options=available_vars[:10],  # Show first 10
                            cause=e
                        )
                census_variables = normalized_vars

            # Build pipeline configuration
            config = self._build_pipeline_config(
                city=city,
                state=state,
                lat=lat,
                lon=lon,
                poi_types=poi_types,
                travel_time=travel_time,
                travel_mode=travel_mode,
                census_variables=census_variables,
                output_dir=output_dir,
                create_maps=create_maps,
                **options
            )

            # Execute analysis
            logger.info(f"Starting analysis for {location}")
            pipeline_config = PipelineConfig(**config)
            orchestrator = PipelineOrchestrator(pipeline_config)
            result_data = orchestrator.run()

            # Convert to clean result object
            result = create_analysis_result_from_pipeline_data(result_data, config)

            logger.info(f"Analysis complete: {result.poi_count} POIs found")
            return result

        except ValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            # Convert other exceptions to appropriate types
            if "census" in str(e).lower() or "api key" in str(e).lower():
                raise APIError(
                    f"Census API error: {e}",
                    api_name="census",
                    cause=e
                )
            elif "osm" in str(e).lower() or "overpass" in str(e).lower():
                raise APIError(
                    f"OpenStreetMap API error: {e}",
                    api_name="osm",
                    cause=e
                )
            else:
                raise AnalysisError(
                    f"Analysis failed: {e}",
                    cause=e
                )

    def discover_nearby_pois(
        self,
        location: str | tuple[float, float],
        travel_time: int = 15,
        travel_mode: str = "drive",
        poi_categories: list[str] | None = None,
        exclude_categories: list[str] | None = None,
        max_pois_per_category: int | None = None,
        output_dir: str = "output",
        create_maps: bool = True,
        **options
    ) -> POIResult:
        """Discover all POIs near a location within travel time.
        
        Args:
            location: Location as "City, State" or (latitude, longitude) 
            travel_time: Travel time limit in minutes (1-120)
            travel_mode: Travel mode ("drive", "walk", "bike")
            poi_categories: POI categories to include (e.g., ["food_and_drink", "healthcare"])
            exclude_categories: POI categories to exclude
            max_pois_per_category: Maximum POIs per category
            output_dir: Output directory for files
            create_maps: Whether to create map visualizations
            **options: Additional discovery options
            
        Returns:
            POIResult with discovered POIs and statistics
            
        Example:
            ```python
            result = mapper.discover_nearby_pois(
                "Chapel Hill, NC", 
                travel_time=20,
                travel_mode="walk",
                poi_categories=["food_and_drink", "healthcare"]
            )
            ```
        """
        try:
            # Validate inputs (reuse validation from analyze_location)
            if isinstance(location, str):
                validate_location(location)
            elif not (isinstance(location, (tuple, list)) and len(location) == 2):
                raise ValidationError(
                    "Location must be 'City, State' string or (lat, lon) tuple",
                    field="location",
                    value=location
                )

            validate_travel_time(travel_time)

            if travel_mode not in ["drive", "walk", "bike"]:
                raise ValidationError(
                    "Travel mode must be 'drive', 'walk', or 'bike'",
                    field="travel_mode",
                    value=travel_mode,
                    valid_options=["drive", "walk", "bike"]
                )

            # Import travel mode enum
            from ..isochrone import TravelMode
            travel_mode_enum = {
                "drive": TravelMode.DRIVE,
                "walk": TravelMode.WALK,
                "bike": TravelMode.BIKE
            }[travel_mode]

            # Build POI discovery configuration
            poi_config = NearbyPOIDiscoveryConfig(
                location=location,
                travel_time=travel_time,
                travel_mode=travel_mode_enum,
                poi_categories=poi_categories,
                exclude_categories=exclude_categories,
                max_pois_per_category=max_pois_per_category,
                output_dir=Path(output_dir),
                **options
            )

            # Execute POI discovery
            logger.info(f"Starting POI discovery for {location}")
            result = execute_poi_discovery_pipeline(poi_config)

            if result.is_err():
                error = result.unwrap_err()
                raise AnalysisError(
                    f"POI discovery failed: {error.message}",
                    stage="poi_discovery",
                    context=error.context
                )

            poi_result = result.unwrap()
            logger.info(f"POI discovery complete: {poi_result.total_poi_count} POIs found")
            return poi_result

        except ValidationError:
            raise  # Re-raise validation errors as-is
        except Exception as e:
            if "poi discovery" in str(e).lower():
                raise AnalysisError(
                    f"POI discovery failed: {e}",
                    stage="poi_discovery",
                    cause=e
                )
            else:
                raise AnalysisError(
                    f"Analysis failed: {e}",
                    cause=e
                )

    def analyze_custom_pois(
        self,
        poi_file: str | Path,
        travel_time: int = 15,
        travel_mode: str = "drive",
        census_variables: list[str] | None = None,
        output_dir: str = "output",
        **options
    ) -> AnalysisResult:
        """Analyze accessibility using custom POI coordinates from a file.
        
        Args:
            poi_file: Path to CSV file with POI coordinates
            travel_time: Travel time limit in minutes
            travel_mode: Travel mode ("drive", "walk", "bike")
            census_variables: Census variables to analyze
            output_dir: Output directory for files
            **options: Additional analysis options
            
        Returns:
            AnalysisResult with analysis data
            
        Example:
            ```python
            result = mapper.analyze_custom_pois(
                "my_hospitals.csv",
                travel_time=30,
                census_variables=["total_population", "median_age"]
            )
            ```
        """
        poi_file = Path(poi_file)
        if not poi_file.exists():
            raise ValidationError(
                f"POI file not found: {poi_file}",
                field="poi_file",
                value=str(poi_file)
            )

        try:
            # Build configuration for custom POI analysis
            config = self._build_pipeline_config(
                custom_poi_file=str(poi_file),
                travel_time=travel_time,
                travel_mode=travel_mode,
                census_variables=census_variables,
                output_dir=output_dir,
                **options
            )

            # Execute analysis
            logger.info(f"Starting custom POI analysis from {poi_file}")
            pipeline_config = PipelineConfig(**config)
            orchestrator = PipelineOrchestrator(pipeline_config)
            result_data = orchestrator.run()

            # Convert to result object
            result = create_analysis_result_from_pipeline_data(result_data, config)

            logger.info(f"Custom POI analysis complete: {result.poi_count} POIs found")
            return result

        except Exception as e:
            raise AnalysisError(
                f"Custom POI analysis failed: {e}",
                stage="custom_poi_analysis",
                cause=e
            )

    def _build_pipeline_config(self, **kwargs) -> dict[str, Any]:
        """Build pipeline configuration from method parameters."""
        config = {
            'output_dir': kwargs.get('output_dir', self.config['default_output_dir']),
            'travel_time': kwargs.get('travel_time', self.config['default_travel_time']),
            'travel_mode': kwargs.get('travel_mode', self.config['default_travel_mode']),
        }

        # Add API key if available (use correct parameter name)
        if self.api_key:
            config['api_key'] = self.api_key

        # Location configuration
        if kwargs.get('city') and kwargs.get('state'):
            config.update({
                'geocode_area': f"{kwargs['city']}, {kwargs['state']}",
                'state': kwargs['state'],
            })
        elif kwargs.get('lat') is not None and kwargs.get('lon') is not None:
            # For coordinates, we need to convert to a format the pipeline understands
            # For now, we'll need to use custom coordinates approach
            from tempfile import NamedTemporaryFile
            import csv
            import os
            
            # Create a temporary file with the coordinates
            temp_file = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            writer = csv.writer(temp_file)
            writer.writerow(['name', 'lat', 'lon'])
            writer.writerow(['Analysis Point', kwargs['lat'], kwargs['lon']])
            temp_file.close()
            
            config['custom_coords_path'] = temp_file.name

        # POI configuration - optional for demographic-only analysis
        poi_types = kwargs.get('poi_types')
        if poi_types and len(poi_types) > 0:
            # Convert simple poi_types list to OSM format
            # Use first POI type as primary
            config['poi_type'] = 'amenity'  # Default category
            config['poi_name'] = poi_types[0]
            # For multiple POI types, we'd need to run multiple analyses
            # For now, just use the first one
        elif poi_types == []:
            # Explicitly empty list - no POI search
            config['skip_poi_discovery'] = True
        else:
            # poi_types is None - demographic-only analysis
            config['skip_poi_discovery'] = True

        # Custom POI file
        if kwargs.get('custom_poi_file'):
            config['custom_coords_path'] = kwargs['custom_poi_file']

        # Census variables
        if kwargs.get('census_variables'):
            config['census_variables'] = kwargs['census_variables']

        # Output options
        if kwargs.get('create_maps', True):
            config['create_maps'] = True

        # Geographic level
        config['geographic_level'] = kwargs.get('geographic_level', 'block-group')

        return config
