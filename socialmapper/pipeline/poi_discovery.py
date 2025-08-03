"""POI discovery pipeline stage for SocialMapper.

This module implements the nearby POI discovery pipeline stage that:
1. Geocodes origin locations (addresses or coordinates)
2. Generates isochrones for the specified travel time/mode
3. Queries POIs within the isochrone using the polygon query system
4. Organizes and exports results

The pipeline follows the established patterns from other pipeline modules.
"""

import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import Point

from ..api.result_types import (
    DiscoveredPOI,
    Err,
    Error,
    ErrorType,
    NearbyPOIDiscoveryConfig,
    NearbyPOIResult,
    Ok,
    Result,
)
from ..console import get_logger, print_info, print_success
from ..exceptions import (
    InvalidConfigurationError,
)
from ..geocoding import geocode_address
from ..geocoding.models import AddressInput, AddressProvider, GeocodingConfig
from ..isochrone import TravelMode, create_isochrone_from_poi
from ..poi_categorization import POI_CATEGORY_MAPPING, categorize_poi
from ..query.polygon_queries import query_pois_in_polygon
from ..util.error_handling import error_context

logger = get_logger(__name__)


class NearbyPOIDiscoveryStage:
    """Pipeline stage for discovering POIs near a location within travel time constraints."""

    def __init__(self, config: NearbyPOIDiscoveryConfig):
        """Initialize the POI discovery stage with configuration.

        Args:
            config: Configuration for POI discovery
        """
        self.config = config
        self.results = NearbyPOIResult(
            origin_location={},
            travel_time=config.travel_time,
            travel_mode=config.travel_mode,
            isochrone_area_km2=0.0,
        )

    def execute(self) -> Result[NearbyPOIResult, Error]:
        """Execute the POI discovery pipeline stage.

        Returns:
            Result containing the discovery results or an error
        """
        try:
            # Step 1: Geocode the origin location
            print_info("\n=== Step 1: Geocoding Origin Location ===")
            geocoding_result = self._geocode_origin()
            if geocoding_result.is_err():
                return geocoding_result

            origin_coords = geocoding_result.unwrap()
            self.results.origin_location = {
                "lat": origin_coords[0],
                "lon": origin_coords[1],
            }
            print_success(
                f"Origin geocoded: {origin_coords[0]:.6f}, {origin_coords[1]:.6f}"
            )

            # Step 2: Generate isochrone for the origin
            print_info("\n=== Step 2: Generating Isochrone ===")
            isochrone_result = self._generate_isochrone(origin_coords)
            if isochrone_result.is_err():
                return isochrone_result

            isochrone_gdf = isochrone_result.unwrap()
            self.results.isochrone_geometry = isochrone_gdf

            # Calculate isochrone area
            if not isochrone_gdf.empty:
                # Project to a suitable CRS for area calculation (e.g., Web Mercator)
                projected_gdf = isochrone_gdf.to_crs("EPSG:3857")
                area_m2 = projected_gdf.geometry.area.sum()
                self.results.isochrone_area_km2 = area_m2 / 1_000_000
                print_success(f"Isochrone area: {self.results.isochrone_area_km2:.2f} km²")

            # Step 3: Query POIs within the isochrone
            print_info("\n=== Step 3: Querying POIs Within Isochrone ===")
            poi_query_result = self._query_pois_in_isochrone(isochrone_gdf)
            if poi_query_result.is_err():
                return poi_query_result

            raw_pois = poi_query_result.unwrap()
            print_info(f"Found {len(raw_pois)} POIs within the isochrone")

            # Step 4: Process and organize POIs
            print_info("\n=== Step 4: Processing and Organizing POIs ===")
            processing_result = self._process_pois(raw_pois, origin_coords)
            if processing_result.is_err():
                return processing_result

            # Step 5: Export results
            if any([self.config.export_csv, self.config.export_geojson, self.config.create_map]):
                print_info("\n=== Step 5: Exporting Results ===")
                export_result = self._export_results()
                if export_result.is_err():
                    self.results.warnings.append(
                        f"Export warning: {export_result.unwrap_err().message}"
                    )

            # Add metadata
            self.results.metadata.update({
                "query_categories": self.config.poi_categories or list(POI_CATEGORY_MAPPING.keys()),
                "excluded_categories": self.config.exclude_categories or [],
                "max_pois_per_category": self.config.max_pois_per_category,
                "include_poi_details": self.config.include_poi_details,
            })

            print_success(
                f"\n✓ POI Discovery Complete: {self.results.total_poi_count} POIs found "
                f"across {len(self.results.pois_by_category)} categories"
            )

            return Ok(self.results)

        except Exception as e:
            logger.error(f"Unexpected error in POI discovery: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.POI_DISCOVERY,
                    message=f"Unexpected error during POI discovery: {e!s}",
                    cause=e,
                )
            )

    def _geocode_origin(self) -> Result[tuple[float, float], Error]:
        """Geocode the origin location to coordinates.

        Returns:
            Result containing (lat, lon) tuple or an error
        """
        try:
            if isinstance(self.config.location, tuple):
                # Already have coordinates
                lat, lon = self.config.location
                return Ok((lat, lon))

            # Geocode address string
            with error_context("geocoding origin address", address=self.config.location):
                # Create geocoding config
                geocoding_config = GeocodingConfig(
                    primary_provider=AddressProvider.NOMINATIM,
                    fallback_providers=[AddressProvider.CENSUS],
                )

                # Create address input
                address_input = AddressInput(address=self.config.location)

                # Geocode the address
                geocoding_result = geocode_address(address_input, geocoding_config)

                if geocoding_result.quality.value == "failed":
                    return Err(
                        Error(
                            type=ErrorType.LOCATION_GEOCODING,
                            message=f"Failed to geocode address: {self.config.location}",
                            context={"address": self.config.location},
                        )
                    )

                return Ok((geocoding_result.latitude, geocoding_result.longitude))

        except Exception as e:
            logger.error(f"Error geocoding origin: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.LOCATION_GEOCODING,
                    message=f"Error geocoding origin location: {e!s}",
                    cause=e,
                )
            )

    def _generate_isochrone(
        self, origin_coords: tuple[float, float]
    ) -> Result[gpd.GeoDataFrame, Error]:
        """Generate isochrone for the origin location.

        Args:
            origin_coords: (lat, lon) tuple

        Returns:
            Result containing the isochrone GeoDataFrame or an error
        """
        try:
            # Create a POI dict for the isochrone generator
            origin_poi = {
                "id": "origin",
                "name": "Origin Location",
                "lat": origin_coords[0],
                "lon": origin_coords[1],
                "tags": {"name": "Origin"},
            }

            # Generate isochrone
            with error_context(
                "generating isochrone",
                travel_time=self.config.travel_time,
                travel_mode=self.config.travel_mode.value,
            ):
                isochrone_gdf = create_isochrone_from_poi(
                    poi=origin_poi,
                    travel_time_limit=self.config.travel_time,
                    save_file=False,
                    travel_mode=self.config.travel_mode,
                )

                if isochrone_gdf is None or isochrone_gdf.empty:
                    return Err(
                        Error(
                            type=ErrorType.ISOCHRONE_GENERATION,
                            message="Failed to generate isochrone for origin location",
                            context={
                                "origin": origin_coords,
                                "travel_time": self.config.travel_time,
                                "travel_mode": self.config.travel_mode.value,
                            },
                        )
                    )

                return Ok(isochrone_gdf)

        except Exception as e:
            logger.error(f"Error generating isochrone: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.ISOCHRONE_GENERATION,
                    message=f"Error generating isochrone: {e!s}",
                    cause=e,
                )
            )

    def _query_pois_in_isochrone(
        self, isochrone_gdf: gpd.GeoDataFrame
    ) -> Result[list[dict[str, Any]], Error]:
        """Query POIs within the isochrone polygon.

        Args:
            isochrone_gdf: GeoDataFrame containing the isochrone polygon

        Returns:
            Result containing list of POI dictionaries or an error
        """
        try:
            # Get the isochrone polygon
            if isochrone_gdf.empty:
                return Err(
                    Error(
                        type=ErrorType.POI_QUERY,
                        message="Isochrone is empty, cannot query POIs",
                    )
                )

            isochrone_polygon = isochrone_gdf.geometry.iloc[0]

            # Query POIs using the polygon query system
            with error_context(
                "querying POIs in isochrone",
                categories=self.config.poi_categories,
                exclude=self.config.exclude_categories,
            ):
                pois = query_pois_in_polygon(
                    polygon=isochrone_polygon,
                    categories=self.config.poi_categories,
                    exclude_categories=self.config.exclude_categories,
                    timeout=180,  # 3 minutes timeout for large queries
                )

                if not pois:
                    return Err(
                        Error(
                            type=ErrorType.POI_QUERY,
                            message="No POIs found within the travel time isochrone",
                            context={
                                "isochrone_area_km2": self.results.isochrone_area_km2,
                                "categories_searched": self.config.poi_categories or "all",
                            },
                        )
                    )

                return Ok(pois)

        except Exception as e:
            logger.error(f"Error querying POIs: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.POI_QUERY,
                    message=f"Error querying POIs in isochrone: {e!s}",
                    cause=e,
                )
            )

    def _process_pois(
        self, raw_pois: list[dict[str, Any]], origin_coords: tuple[float, float]
    ) -> Result[None, Error]:
        """Process raw POI data into organized results.

        Args:
            raw_pois: List of raw POI dictionaries from the query
            origin_coords: (lat, lon) tuple of origin

        Returns:
            Result indicating success or an error
        """
        try:
            processed_pois = []
            pois_by_category = {}

            for poi in raw_pois:
                # Extract basic info
                poi_id = f"{poi.get('type', 'unknown')}_{poi.get('id', 'unknown')}"
                name = poi.get("tags", {}).get("name", f"Unnamed {poi.get('type', 'POI')}")

                # Get coordinates
                lat = poi.get("lat")
                lon = poi.get("lon")

                if lat is None or lon is None:
                    logger.warning(f"Skipping POI without coordinates: {poi_id}")
                    continue

                # Calculate straight-line distance
                distance_m = geodesic(origin_coords, (lat, lon)).meters

                # Categorize the POI
                category = categorize_poi(poi.get("tags", {}))

                # Create subcategory from most specific tag
                tags = poi.get("tags", {})
                subcategory = None
                for key in ["amenity", "shop", "leisure", "office", "tourism", "craft"]:
                    if key in tags:
                        subcategory = tags[key]
                        break

                if not subcategory:
                    subcategory = "general"

                # Skip if in excluded categories
                if self.config.exclude_categories and category in self.config.exclude_categories:
                    continue

                # Create DiscoveredPOI object
                discovered_poi = DiscoveredPOI(
                    id=poi_id,
                    name=name,
                    category=category,
                    subcategory=subcategory,
                    latitude=lat,
                    longitude=lon,
                    straight_line_distance_m=distance_m,
                    osm_type=poi.get("type", "unknown"),
                    osm_id=poi.get("id", 0),
                    tags=poi.get("tags", {}),
                )

                # Add additional details if requested
                if self.config.include_poi_details:
                    tags = poi.get("tags", {})
                    discovered_poi = DiscoveredPOI(
                        **{
                            **discovered_poi.__dict__,
                            "address": self._format_address(tags),
                            "phone": tags.get("phone"),
                            "website": tags.get("website") or tags.get("contact:website"),
                            "opening_hours": tags.get("opening_hours"),
                        }
                    )

                processed_pois.append(discovered_poi)

                # Organize by category
                if category not in pois_by_category:
                    pois_by_category[category] = []
                pois_by_category[category].append(discovered_poi)

            # Apply max POIs per category limit if specified
            if self.config.max_pois_per_category:
                for category, pois in pois_by_category.items():
                    if len(pois) > self.config.max_pois_per_category:
                        # Sort by distance and keep closest ones
                        sorted_pois = sorted(pois, key=lambda p: p.straight_line_distance_m)
                        pois_by_category[category] = sorted_pois[: self.config.max_pois_per_category]

                        logger.info(
                            f"Limited {category} POIs from {len(pois)} to "
                            f"{self.config.max_pois_per_category}"
                        )

            # Update results
            self.results.pois_by_category = pois_by_category
            self.results.total_poi_count = sum(len(pois) for pois in pois_by_category.values())
            self.results.category_counts = {
                category: len(pois) for category, pois in pois_by_category.items()
            }

            # Create POI points GeoDataFrame
            if processed_pois:
                poi_data = []
                for poi in self.results.get_all_pois():
                    poi_data.append({
                        "id": poi.id,
                        "name": poi.name,
                        "category": poi.category,
                        "subcategory": poi.subcategory,
                        "distance_m": poi.straight_line_distance_m,
                        "geometry": Point(poi.longitude, poi.latitude),
                    })

                self.results.poi_points = gpd.GeoDataFrame(
                    poi_data, crs="EPSG:4326"
                )

            return Ok(None)

        except Exception as e:
            logger.error(f"Error processing POIs: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.PROCESSING,
                    message=f"Error processing POI data: {e!s}",
                    cause=e,
                )
            )

    def _format_address(self, tags: dict[str, str]) -> str | None:
        """Format address from OSM tags.

        Args:
            tags: OSM tags dictionary

        Returns:
            Formatted address string or None
        """
        address_parts = []

        # Common address components in order
        for key in ["addr:housenumber", "addr:street", "addr:city", "addr:state", "addr:postcode"]:
            if key in tags:
                address_parts.append(tags[key])

        return ", ".join(address_parts) if address_parts else None

    def _export_results(self) -> Result[None, Error]:
        """Export results to files based on configuration.

        Returns:
            Result indicating success or an error
        """
        try:
            # Create output directory
            self.config.output_dir.mkdir(parents=True, exist_ok=True)

            base_name = f"poi_discovery_{self.config.travel_time}min_{self.config.travel_mode.value}"

            # Export CSV if requested
            if self.config.export_csv and self.results.total_poi_count > 0:
                csv_path = self.config.output_dir / f"{base_name}.csv"
                self._export_csv(csv_path)
                self.results.files_generated["csv"] = csv_path
                print_success(f"Exported CSV: {csv_path}")

            # Export GeoJSON if requested
            if self.config.export_geojson:
                if self.results.poi_points is not None and not self.results.poi_points.empty:
                    geojson_path = self.config.output_dir / f"{base_name}_pois.geojson"
                    self.results.poi_points.to_file(geojson_path, driver="GeoJSON")
                    self.results.files_generated["poi_geojson"] = geojson_path
                    print_success(f"Exported POI GeoJSON: {geojson_path}")

                if self.results.isochrone_geometry is not None and not self.results.isochrone_geometry.empty:
                    isochrone_path = self.config.output_dir / f"{base_name}_isochrone.geojson"
                    self.results.isochrone_geometry.to_file(isochrone_path, driver="GeoJSON")
                    self.results.files_generated["isochrone_geojson"] = isochrone_path
                    print_success(f"Exported Isochrone GeoJSON: {isochrone_path}")

            # Create map if requested
            if self.config.create_map and self.results.total_poi_count > 0:
                map_result = self._create_map()
                if map_result.is_ok():
                    map_path = map_result.unwrap()
                    self.results.files_generated["map"] = map_path
                    print_success(f"Created map: {map_path}")
                else:
                    self.results.warnings.append(f"Map creation failed: {map_result.unwrap_err().message}")

            return Ok(None)

        except Exception as e:
            logger.error(f"Error exporting results: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.PROCESSING,
                    message=f"Error exporting results: {e!s}",
                    cause=e,
                )
            )

    def _export_csv(self, csv_path: Path) -> None:
        """Export POI data to CSV file.

        Args:
            csv_path: Path to save the CSV file
        """
        rows = []
        for poi in self.results.get_all_pois():
            row = {
                "id": poi.id,
                "name": poi.name,
                "category": poi.category,
                "subcategory": poi.subcategory,
                "latitude": poi.latitude,
                "longitude": poi.longitude,
                "distance_m": round(poi.straight_line_distance_m, 1),
                "distance_km": round(poi.straight_line_distance_m / 1000, 2),
            }

            if self.config.include_poi_details:
                row.update({
                    "address": poi.address or "",
                    "phone": poi.phone or "",
                    "website": poi.website or "",
                    "opening_hours": poi.opening_hours or "",
                })

            rows.append(row)

        # Sort by distance
        rows.sort(key=lambda x: x["distance_m"])

        # Create DataFrame and save
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)

    def _create_map(self) -> Result[Path, Error]:
        """Create an interactive map of the results.

        Returns:
            Result containing the map file path or an error
        """
        try:
            import folium
            from folium.plugins import MarkerCluster

            # Create base map centered on origin
            origin_lat = self.results.origin_location["lat"]
            origin_lon = self.results.origin_location["lon"]

            m = folium.Map(
                location=[origin_lat, origin_lon],
                zoom_start=13,
                tiles="OpenStreetMap",
            )

            # Add origin marker
            folium.Marker(
                [origin_lat, origin_lon],
                popup="Origin Location",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(m)

            # Add isochrone polygon
            if self.results.isochrone_geometry is not None and not self.results.isochrone_geometry.empty:
                isochrone_geojson = json.loads(self.results.isochrone_geometry.to_json())
                folium.GeoJson(
                    isochrone_geojson,
                    name=f"{self.config.travel_time} min {self.config.travel_mode.value}",
                    style_function=lambda x: {
                        "fillColor": "#ff7800",
                        "color": "#ff7800",
                        "weight": 2,
                        "fillOpacity": 0.1,
                    },
                ).add_to(m)

            # Add POI markers with clustering
            marker_cluster = MarkerCluster().add_to(m)

            # Color palette for categories
            colors = [
                "blue", "green", "purple", "orange", "darkred",
                "lightred", "beige", "darkblue", "darkgreen", "cadetblue",
                "darkpurple", "white", "pink", "lightblue", "lightgreen",
                "gray", "black", "lightgray"
            ]

            category_colors = {}
            for i, category in enumerate(self.results.pois_by_category.keys()):
                category_colors[category] = colors[i % len(colors)]

            # Add POI markers
            for category, pois in self.results.pois_by_category.items():
                for poi in pois:
                    popup_text = f"""
                    <b>{poi.name}</b><br>
                    Category: {poi.category}<br>
                    Subcategory: {poi.subcategory}<br>
                    Distance: {poi.straight_line_distance_m/1000:.1f} km
                    """

                    if poi.address:
                        popup_text += f"<br>Address: {poi.address}"
                    if poi.website:
                        popup_text += f'<br><a href="{poi.website}" target="_blank">Website</a>'

                    folium.Marker(
                        [poi.latitude, poi.longitude],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color=category_colors[category], icon="info-sign"),
                    ).add_to(marker_cluster)

            # Add legend
            legend_html = '''
            <div style="position: fixed; 
                        top: 10px; right: 10px; width: 200px; height: auto;
                        background-color: white; z-index: 1000; font-size: 14px;
                        border: 2px solid grey; border-radius: 5px; padding: 10px">
                <p style="margin: 0; font-weight: bold;">POI Categories</p>
            '''

            for category, color in category_colors.items():
                count = self.results.category_counts.get(category, 0)
                legend_html += f'<p style="margin: 2px;"><span style="color: {color};">⬤</span> {category} ({count})</p>'

            legend_html += '</div>'
            m.get_root().html.add_child(folium.Element(legend_html))

            # Save map
            map_path = self.config.output_dir / f"poi_discovery_map_{self.config.travel_time}min.html"
            m.save(str(map_path))

            return Ok(map_path)

        except ImportError:
            return Err(
                Error(
                    type=ErrorType.PROCESSING,
                    message="Folium not installed. Install with: pip install folium",
                )
            )
        except Exception as e:
            logger.error(f"Error creating map: {e}", exc_info=True)
            return Err(
                Error(
                    type=ErrorType.PROCESSING,
                    message=f"Error creating map: {e!s}",
                    cause=e,
                )
            )


def execute_poi_discovery_pipeline(
    config: NearbyPOIDiscoveryConfig,
) -> Result[NearbyPOIResult, Error]:
    """Execute the POI discovery pipeline with the given configuration.

    This is the main entry point for the POI discovery pipeline stage.

    Args:
        config: Configuration for POI discovery

    Returns:
        Result containing the discovery results or an error

    Example:
        ```python
        from pathlib import Path
        from socialmapper.pipeline import execute_poi_discovery_pipeline
        from socialmapper.api.result_types import NearbyPOIDiscoveryConfig
        from socialmapper.isochrone import TravelMode

        config = NearbyPOIDiscoveryConfig(
            location="Chapel Hill, NC",
            travel_time=15,
            travel_mode=TravelMode.DRIVE,
            poi_categories=["food_and_drink", "shopping"],
            export_csv=True,
            create_map=True,
            output_dir=Path("output/poi_discovery")
        )

        result = execute_poi_discovery_pipeline(config)
        
        match result:
            case Ok(poi_result):
                print(f"Found {poi_result.total_poi_count} POIs")
                for category, count in poi_result.category_counts.items():
                    print(f"  {category}: {count}")
            case Err(error):
                print(f"Error: {error}")
        ```
    """
    try:
        # Validate configuration
        config.validate()

        # Create and execute the pipeline stage
        stage = NearbyPOIDiscoveryStage(config)
        return stage.execute()

    except InvalidConfigurationError as e:
        return Err(
            Error(
                type=ErrorType.CONFIGURATION,
                message=str(e),
                cause=e,
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error in POI discovery pipeline: {e}", exc_info=True)
        return Err(
            Error(
                type=ErrorType.POI_DISCOVERY,
                message=f"Unexpected error: {e!s}",
                cause=e,
            )
        )


# Helper functions for common use cases

def discover_pois_near_address(
    address: str,
    travel_time: int = 15,
    travel_mode: TravelMode = TravelMode.DRIVE,
    categories: list[str] | None = None,
    output_dir: Path | None = None,
) -> Result[NearbyPOIResult, Error]:
    """Convenience function to discover POIs near an address.

    Args:
        address: Address string to search near
        travel_time: Travel time in minutes (default: 15)
        travel_mode: Mode of travel (default: DRIVE)
        categories: POI categories to include (default: all)
        output_dir: Output directory (default: output/poi_discovery)

    Returns:
        Result containing the discovery results or an error
    """
    config = NearbyPOIDiscoveryConfig(
        location=address,
        travel_time=travel_time,
        travel_mode=travel_mode,
        poi_categories=categories,
        export_csv=True,
        export_geojson=True,
        create_map=True,
        output_dir=output_dir or Path("output/poi_discovery"),
    )

    return execute_poi_discovery_pipeline(config)


def discover_pois_near_coordinates(
    latitude: float,
    longitude: float,
    travel_time: int = 15,
    travel_mode: TravelMode = TravelMode.DRIVE,
    categories: list[str] | None = None,
    output_dir: Path | None = None,
) -> Result[NearbyPOIResult, Error]:
    """Convenience function to discover POIs near coordinates.

    Args:
        latitude: Latitude of the origin
        longitude: Longitude of the origin
        travel_time: Travel time in minutes (default: 15)
        travel_mode: Mode of travel (default: DRIVE)
        categories: POI categories to include (default: all)
        output_dir: Output directory (default: output/poi_discovery)

    Returns:
        Result containing the discovery results or an error
    """
    config = NearbyPOIDiscoveryConfig(
        location=(latitude, longitude),
        travel_time=travel_time,
        travel_mode=travel_mode,
        poi_categories=categories,
        export_csv=True,
        export_geojson=True,
        create_map=True,
        output_dir=output_dir or Path("output/poi_discovery"),
    )

    return execute_poi_discovery_pipeline(config)
