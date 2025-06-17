"""TIGER REST API client for fetching geometries."""

import logging

# Avoid circular import - implement simple caching inline
import pickle
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import requests
from requests.adapters import HTTPAdapter

try:
    from requests.packages.urllib3.util.retry import Retry
except ImportError:
    # For newer versions of urllib3
    from urllib3.util.retry import Retry
from shapely.geometry import shape

from .models import (
    TIGER_ENDPOINTS,
    GeographyLevel,
    GeometryQuery,
    GeometryResult,
    TigerEndpoint,
)

logger = logging.getLogger(__name__)


class TigerGeometryClient:
    """Client for fetching geometries from TIGER REST API."""

    def __init__(
        self,
        cache_dir: str | None = None,
        rate_limit_delay: float = 0.1,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize the TIGER geometry client.

        Args:
            cache_dir: Directory for caching responses (None = no caching)
            rate_limit_delay: Delay between API requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self._last_request_time = 0.0

    def fetch_geometries(self, query: GeometryQuery) -> GeometryResult:
        """Fetch geometries based on query parameters.

        Args:
            query: Query parameters specifying what geometries to fetch

        Returns:
            GeometryResult containing the fetched geometries

        Raises:
            ValueError: If query parameters are invalid
            requests.RequestException: If API request fails
        """
        # Validate query parameters
        self._validate_query(query)

        # Get endpoint configuration
        endpoint = TIGER_ENDPOINTS.get(query.geography_level)
        if not endpoint:
            raise ValueError(f"Unsupported geography level: {query.geography_level}")

        # Check cache if available
        cache_key = self._get_cache_key(query)
        if self.cache_dir and (cached_result := self._get_cached_result(cache_key)):
            logger.info(f"Using cached result for {cache_key}")
            return cached_result

        # Build and execute query
        logger.info(f"Fetching {query.geography_level.value} geometries")
        params = self._build_query_params(query, endpoint)
        features = self._fetch_all_features(endpoint, params)

        # Convert to GeoDataFrame
        gdf = self._features_to_geodataframe(features, endpoint, query)

        # Create result
        result = GeometryResult(
            geodataframe=gdf,
            geography_level=query.geography_level,
            query=query,
            metadata={
                "endpoint": endpoint.base_url,
                "feature_count": len(features),
                "timestamp": pd.Timestamp.now().isoformat(),
            },
        )

        # Cache result if available
        if self.cache_dir:
            self._cache_result(cache_key, result)

        return result

    def fetch_counties(
        self,
        state_fips: str | None = None,
        county_names: list[str] | None = None,
        simplify_tolerance: float = 0.0001,
    ) -> GeometryResult:
        """Convenience method for fetching county geometries.

        Args:
            state_fips: State FIPS code to filter by
            county_names: List of county names to filter by
            simplify_tolerance: Tolerance for geometry simplification

        Returns:
            GeometryResult with county geometries
        """
        query = GeometryQuery(
            geography_level=GeographyLevel.COUNTY,
            state_fips=state_fips,
            simplify_tolerance=simplify_tolerance,
        )

        result = self.fetch_geometries(query)

        # Filter by county names if provided
        if county_names:
            mask = result.geodataframe["NAME"].isin(county_names)
            result.geodataframe = result.geodataframe[mask].copy()

        return result

    def fetch_block_groups(
        self,
        state_fips: str,
        county_fips: str | None = None,
        tract_ids: list[str] | None = None,
        simplify_tolerance: float = 0.0001,
        use_generalized: bool = True,
    ) -> GeometryResult:
        """Convenience method for fetching block group geometries.

        Args:
            state_fips: State FIPS code (required)
            county_fips: County FIPS code to filter by
            tract_ids: List of tract IDs to filter by
            simplify_tolerance: Tolerance for geometry simplification
            use_generalized: If True, use generalized (500k) boundaries for better performance

        Returns:
            GeometryResult with block group geometries
        """
        geography_level = (
            GeographyLevel.BLOCK_GROUP if use_generalized else GeographyLevel.BLOCK_GROUP_DETAILED
        )

        query = GeometryQuery(
            geography_level=geography_level,
            state_fips=state_fips,
            county_fips=county_fips,
            simplify_tolerance=simplify_tolerance,
        )

        result = self.fetch_geometries(query)

        # Filter by tract IDs if provided
        if tract_ids:
            # Extract tract from block group GEOID (first 11 digits)
            result.geodataframe["tract_id"] = result.geodataframe["GEOID"].str[:11]
            mask = result.geodataframe["tract_id"].isin(tract_ids)
            result.geodataframe = result.geodataframe[mask].drop(columns=["tract_id"])

        return result

    def fetch_zctas(
        self,
        zcta_codes: list[str] | None = None,
        zcta_prefix: str | None = None,
        simplify_tolerance: float = 0.0001,
    ) -> GeometryResult:
        """Convenience method for fetching ZCTA geometries.

        Args:
            zcta_codes: List of specific ZCTA codes to fetch
            zcta_prefix: Prefix to filter ZCTAs (e.g., '945')
            simplify_tolerance: Tolerance for geometry simplification

        Returns:
            GeometryResult with ZCTA geometries
        """
        query = GeometryQuery(
            geography_level=GeographyLevel.ZCTA,
            zcta_prefix=zcta_prefix,
            geometry_ids=zcta_codes,
            simplify_tolerance=simplify_tolerance,
        )

        return self.fetch_geometries(query)

    def _validate_query(self, query: GeometryQuery) -> None:
        """Validate query parameters."""
        # Check required parameters for certain geography levels
        if query.geography_level in [
            GeographyLevel.BLOCK_GROUP,
            GeographyLevel.BLOCK_GROUP_DETAILED,
        ] and not query.state_fips:
            raise ValueError("state_fips is required for block group queries")

        if query.geography_level == GeographyLevel.TRACT and not query.state_fips:
            raise ValueError("state_fips is required for tract queries")

    def _build_query_params(self, query: GeometryQuery, endpoint: TigerEndpoint) -> dict[str, Any]:
        """Build query parameters for the API request."""
        params = {
            "where": "1=1",  # Default to all records
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson",
            "geometryPrecision": "6",
            "outSR": "4326",  # WGS84
        }

        # Build WHERE clause
        where_clauses = []

        # State filter
        if query.state_fips and endpoint.state_field:
            where_clauses.append(f"{endpoint.state_field} = '{query.state_fips}'")

        # County filter
        if query.county_fips and endpoint.county_field:
            where_clauses.append(f"{endpoint.county_field} = '{query.county_fips}'")

        # ZCTA prefix filter
        if query.zcta_prefix and query.geography_level == GeographyLevel.ZCTA:
            where_clauses.append(f"{endpoint.id_field} LIKE '{query.zcta_prefix}%'")

        # Specific geometry IDs
        if query.geometry_ids and len(query.geometry_ids) > 0:
            id_list = ", ".join(f"'{gid}'" for gid in query.geometry_ids)
            where_clauses.append(f"{endpoint.id_field} IN ({id_list})")

        if where_clauses:
            params["where"] = " AND ".join(where_clauses)

        return params

    def _fetch_all_features(
        self, endpoint: TigerEndpoint, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Fetch all features, handling pagination if necessary."""
        all_features = []
        offset = 0
        batch_size = 1000  # API typically limits to 1000 records per request

        while True:
            # Apply rate limiting
            self._apply_rate_limit()

            # Add pagination parameters
            query_params = params.copy()
            query_params["resultOffset"] = offset
            query_params["resultRecordCount"] = batch_size

            # Make request
            url = endpoint.build_query_url()
            logger.debug(f"Fetching from {url} with offset {offset}")

            try:
                response = self.session.get(url, params=query_params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch data: {e}")
                raise

            # Extract features
            features = data.get("features", [])
            if not features:
                break

            all_features.extend(features)
            logger.debug(f"Fetched {len(features)} features")

            # Check if we got all features
            if len(features) < batch_size:
                break

            offset += batch_size

        logger.info(f"Fetched total of {len(all_features)} features")
        return all_features

    def _features_to_geodataframe(
        self,
        features: list[dict[str, Any]],
        endpoint: TigerEndpoint,
        query: GeometryQuery,
    ) -> gpd.GeoDataFrame:
        """Convert features to GeoDataFrame."""
        if not features:
            # Return empty GeoDataFrame with proper schema
            return gpd.GeoDataFrame(
                columns=["GEOID", "NAME", "geometry"],
                crs="EPSG:4326",
            )

        # Extract geometries and attributes
        geometries = []
        attributes = []

        for feature in features:
            # Parse geometry
            geom = shape(feature["geometry"])

            # Simplify if requested
            if query.simplify_tolerance is not None and query.simplify_tolerance > 0:
                geom = geom.simplify(query.simplify_tolerance, preserve_topology=True)

            geometries.append(geom)

            # Extract attributes
            attrs = feature.get("properties", {})

            # Ensure consistent GEOID field
            if query.geography_level == GeographyLevel.COUNTY:
                attrs["GEOID"] = attrs.get("STATE", "") + attrs.get("COUNTY", "")
            elif query.geography_level == GeographyLevel.BLOCK_GROUP:
                attrs["GEOID"] = (
                    attrs.get("STATE", "")
                    + attrs.get("COUNTY", "")
                    + attrs.get("TRACT", "")
                    + attrs.get("BLKGRP", "")
                )
            elif query.geography_level == GeographyLevel.TRACT:
                attrs["GEOID"] = (
                    attrs.get("STATE", "") + attrs.get("COUNTY", "") + attrs.get("TRACT", "")
                )
            else:
                attrs["GEOID"] = attrs.get(endpoint.id_field, "")

            # Ensure NAME field
            if "NAME" not in attrs:
                attrs["NAME"] = attrs.get(endpoint.name_field, "")

            attributes.append(attrs)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            attributes,
            geometry=geometries,
            crs="EPSG:4326",
        )

        # Select columns based on include_attributes
        if not query.include_attributes:
            # Keep only essential columns
            essential_cols = ["GEOID", "NAME", "geometry"]
            available_cols = [col for col in essential_cols if col in gdf.columns]
            gdf = gdf[available_cols]

        return gdf

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _get_cache_key(self, query: GeometryQuery) -> str:
        """Generate cache key for a query."""
        # Create a deterministic key from query parameters
        key_parts = [
            f"tiger_{query.geography_level.value}",
            f"state_{query.state_fips or 'all'}",
            f"county_{query.county_fips or 'all'}",
            f"zcta_{query.zcta_prefix or 'all'}",
        ]

        if query.geometry_ids and len(query.geometry_ids) > 0:
            # Sort IDs for consistent key
            ids_hash = hash(tuple(sorted(query.geometry_ids)))
            key_parts.append(f"ids_{ids_hash}")

        return "_".join(key_parts)

    def _get_cached_result(self, cache_key: str) -> GeometryResult | None:
        """Get cached result if available."""
        if not self.cache_dir:
            return None

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            return None

        try:
            with cache_file.open("rb") as f:
                cached_data = pickle.load(f)

            # Reconstruct GeoDataFrame from cached data
            gdf = gpd.read_file(cached_data["geodataframe"], driver="GeoJSON")

            return GeometryResult(
                geodataframe=gdf,
                geography_level=GeographyLevel(cached_data["geography_level"]),
                query=GeometryQuery.model_validate(cached_data["query"]),
                metadata=cached_data["metadata"],
            )
        except Exception as e:
            logger.warning(f"Failed to load cached result: {e}")

        return None

    def _cache_result(self, cache_key: str, result: GeometryResult) -> None:
        """Cache a result."""
        if not self.cache_dir:
            return

        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            # Convert to cacheable format
            cache_data = {
                "geodataframe": result.geodataframe.to_json(),
                "geography_level": result.geography_level.value,
                "query": result.query.model_dump(),
                "metadata": result.metadata,
            }

            with cache_file.open("wb") as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
