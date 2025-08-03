"""Geocoding implementations for converting coordinates to census geographic units.

Provides geocoding services using Census Bureau APIs to convert
latitude/longitude coordinates to census geographic identifiers.
"""

import logging
from typing import Any

import requests

from ..domain.entities import GeocodeResult
from ..domain.interfaces import ConfigurationProvider


class GeocodingError(Exception):
    """Base exception for geocoding errors."""


class CensusGeocoder:
    """Census Bureau geocoding service implementation.

    Uses the Census Bureau's geocoding API to convert coordinates
    to census geographic units (block groups, tracts, etc.).
    """

    def __init__(self, config: ConfigurationProvider, logger: logging.Logger):
        """Initialize geocoder with configuration.

        Args:
            config: Configuration provider
            logger: Logger instance
        """
        self._config = config
        self._logger = logger

        # Census geocoding API endpoints
        self._geocode_base_url = "https://geocoding.geo.census.gov/geocoder"
        self._session = self._create_session()

        # Known city fallbacks for common problematic locations
        # Format: (lat_min, lat_max, lon_min, lon_max) -> (state_fips, county_fips)
        self._known_regions = {
            # Salem, Oregon - Marion County
            (44.8, 45.1, -123.2, -122.8): ("41", "047"),
            # Portland, Oregon - Multnomah County
            (45.4, 45.6, -122.8, -122.5): ("41", "051"),
            # Eugene, Oregon - Lane County
            (43.9, 44.2, -123.3, -122.8): ("41", "039"),
            # Santa Fe, New Mexico - Santa Fe County
            (35.6, 35.8, -106.1, -105.8): ("35", "049"),
            # Durham, North Carolina - Durham County
            (35.9, 36.1, -79.0, -78.8): ("37", "063"),
            # Chapel Hill, North Carolina - Orange County
            (35.8, 36.0, -79.1, -78.9): ("37", "135"),
        }

    def geocode_point(self, latitude: float, longitude: float) -> GeocodeResult:
        """Geocode a lat/lon point to geographic units.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            GeocodeResult with geographic unit information

        Raises:
            GeocodingError: If geocoding fails
        """
        self._logger.debug(f"Geocoding point: {latitude}, {longitude}")

        # Build request parameters
        params = {
            "x": longitude,
            "y": latitude,
            "benchmark": "Public_AR_Current",  # Current address ranges
            "vintage": "Current_Current",  # Current vintage
            "format": "json",
        }

        # Make request to Census geocoding API
        url = f"{self._geocode_base_url}/geographies/coordinates"

        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            # Parse response
            result = self._parse_geocode_response(data, latitude, longitude)

            self._logger.debug(f"Geocoding successful: {result.tract_geoid}")
            return result

        except requests.RequestException as e:
            # Try fallback for known regions before failing
            self._logger.warning(f"Census API failed, trying fallback for {latitude}, {longitude}")
            fallback_result = self._try_known_region_fallback(latitude, longitude)
            if fallback_result:
                return fallback_result
            raise GeocodingError(f"Geocoding request failed: {e}") from e
        except (ValueError, KeyError) as e:
            raise GeocodingError(f"Failed to parse geocoding response: {e}") from e

    def geocode_address(self, address: str) -> GeocodeResult:
        """Geocode an address to geographic units.

        Args:
            address: Street address to geocode

        Returns:
            GeocodeResult with geographic unit information

        Raises:
            GeocodingError: If geocoding fails
        """
        self._logger.debug(f"Geocoding address: {address}")

        # Build request parameters
        params = {
            "street": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        }

        # Make request to Census geocoding API
        url = f"{self._geocode_base_url}/geographies/address"

        try:
            response = self._session.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()

            data = response.json()

            # Extract coordinates from address match
            address_matches = data.get("result", {}).get("addressMatches", [])
            if not address_matches:
                raise GeocodingError(f"No address matches found for: {address}")

            # Use the first (best) match
            match = address_matches[0]
            coordinates = match.get("coordinates", {})

            latitude = float(coordinates.get("y"))
            longitude = float(coordinates.get("x"))

            # Parse geographic information
            result = self._parse_geocode_response(data, latitude, longitude)

            # Add confidence score from address matching
            result = GeocodeResult(
                latitude=result.latitude,
                longitude=result.longitude,
                state_fips=result.state_fips,
                county_fips=result.county_fips,
                tract_geoid=result.tract_geoid,
                block_group_geoid=result.block_group_geoid,
                zcta_geoid=result.zcta_geoid,
                confidence=match.get("matchedAddress", {}).get("tigerLine", {}).get("side"),
                source="census_geocoder",
            )

            self._logger.debug(f"Address geocoding successful: {result.tract_geoid}")
            return result

        except requests.RequestException as e:
            raise GeocodingError(f"Address geocoding request failed: {e}") from e
        except (ValueError, KeyError) as e:
            raise GeocodingError(f"Failed to parse address geocoding response: {e}") from e

    def batch_geocode_points(self, coordinates: list) -> list:
        """Geocode multiple points in a single request.

        Args:
            coordinates: List of (latitude, longitude) tuples

        Returns:
            List of GeocodeResult objects

        Note:
            This is a placeholder for batch geocoding functionality.
            The Census API supports batch geocoding but requires file uploads.
        """
        results = []

        for lat, lon in coordinates:
            try:
                result = self.geocode_point(lat, lon)
                results.append(result)
            except GeocodingError as e:
                self._logger.warning(f"Failed to geocode {lat}, {lon}: {e}")
                # Add a failed result
                results.append(
                    GeocodeResult(
                        latitude=lat, longitude=lon, confidence=0.0, source="census_geocoder_failed"
                    )
                )

        return results

    def _parse_geocode_response(
        self, data: dict[str, Any], latitude: float, longitude: float
    ) -> GeocodeResult:
        """Parse Census geocoding API response.

        Args:
            data: Raw API response data
            latitude: Original latitude
            longitude: Original longitude

        Returns:
            Parsed GeocodeResult
        """
        # Navigate the nested response structure
        result = data.get("result", {})

        # For coordinate geocoding, geographies are directly under result
        # For address geocoding, they're under addressMatches[0].geographies
        geographies = result.get("geographies", {})

        if not geographies:
            # Try address match format as fallback
            address_matches = result.get("addressMatches", [])
            if address_matches:
                geographies = address_matches[0].get("geographies", {})

        if not geographies:
            # Return basic result with just coordinates
            return GeocodeResult(latitude=latitude, longitude=longitude, source="census_geocoder")

        # Extract state information
        states = geographies.get("States", [])
        state_fips = states[0].get("STATE") if states else None

        # Extract county information
        counties = geographies.get("Counties", [])
        county_fips = counties[0].get("COUNTY") if counties else None

        # If we didn't get state/county from API, try fallback
        if not state_fips or not county_fips:
            fallback = self._try_known_region_fallback(latitude, longitude)
            if fallback:
                state_fips = state_fips or fallback.state_fips
                county_fips = county_fips or fallback.county_fips

        # Extract tract information
        tracts = geographies.get("Census Tracts", [])
        tract_geoid = None
        if tracts:
            tract = tracts[0]
            tract_geoid = (
                f"{tract.get('STATE', '')}{tract.get('COUNTY', '')}{tract.get('TRACT', '')}"
            )

        # Extract block group information from census blocks
        blocks = geographies.get("2020 Census Blocks", [])
        block_group_geoid = None
        if blocks:
            block = blocks[0]
            state = block.get("STATE", "")
            county = block.get("COUNTY", "")
            tract = block.get("TRACT", "")
            blkgrp = block.get("BLKGRP", "")
            if all([state, county, tract, blkgrp]):
                block_group_geoid = f"{state}{county}{tract}{blkgrp}"

        # Extract ZCTA (ZIP Code Tabulation Area) information
        zctas = geographies.get("Zip Code Tabulation Areas", [])
        zcta_geoid = zctas[0].get("ZCTA5") if zctas else None

        return GeocodeResult(
            latitude=latitude,
            longitude=longitude,
            state_fips=state_fips,
            county_fips=county_fips,
            tract_geoid=tract_geoid,
            block_group_geoid=block_group_geoid,
            zcta_geoid=zcta_geoid,
            confidence=1.0,  # Census geocoder is authoritative
            source="census_geocoder",
        )

    def _try_known_region_fallback(self, latitude: float, longitude: float) -> GeocodeResult | None:
        """Try to use known region fallback for geocoding.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            GeocodeResult if region is known, None otherwise
        """
        for bounds, (state_fips, county_fips) in self._known_regions.items():
            lat_min, lat_max, lon_min, lon_max = bounds
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                self._logger.info(f"Using fallback for known region: state={state_fips}, county={county_fips}")

                # Create a basic result with state and county info
                # We don't have tract/block group info but at least we have county
                return GeocodeResult(
                    latitude=latitude,
                    longitude=longitude,
                    state_fips=state_fips,
                    county_fips=county_fips,
                    tract_geoid=None,  # We don't know the exact tract
                    block_group_geoid=None,  # We don't know the exact block group
                    zcta_geoid=None,  # We don't know the ZCTA
                    confidence=0.8,  # Lower confidence for fallback
                    source="census_geocoder_fallback",
                )

        return None

    def _create_session(self) -> requests.Session:
        """Create configured requests session."""
        session = requests.Session()

        # Store timeout for use in requests
        # Note: timeout is passed to individual requests, not set on session
        self._timeout = self._config.get_setting("api_timeout_seconds", 30)

        # Set user agent
        session.headers.update({"User-Agent": "SocialMapper/1.0 (Census Geocoder)"})

        return session

    def health_check(self) -> bool:
        """Check if the geocoding service is available.

        Returns:
            True if service is available, False otherwise
        """
        try:
            # Test with a known coordinate (Washington, DC)
            result = self.geocode_point(38.9072, -77.0369)
            return result.state_fips == "11"  # DC FIPS code
        except GeocodingError:
            return False


class MockGeocoder:
    """Mock geocoder for testing and development.

    Returns predictable results for testing without making API calls.
    """

    def __init__(
        self, config: ConfigurationProvider | None = None, logger: logging.Logger | None = None
    ):
        """Initialize mock geocoder."""
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

    def geocode_point(self, latitude: float, longitude: float) -> GeocodeResult:
        """Mock geocode a point.

        Returns a predictable result based on coordinates.
        """
        # Generate mock GEOIDs based on coordinates
        # This is obviously not real geocoding, just for testing

        # Mock state FIPS (based on longitude roughly)
        state_fips = "06" if longitude > -100 else "36"  # California-ish vs New York-ish

        # Mock county and tract
        county_fips = "001"
        tract_code = "000100"
        block_group = "1"

        tract_geoid = f"{state_fips}{county_fips}{tract_code}"
        block_group_geoid = f"{tract_geoid}{block_group}"

        return GeocodeResult(
            latitude=latitude,
            longitude=longitude,
            state_fips=state_fips,
            county_fips=county_fips,
            tract_geoid=tract_geoid,
            block_group_geoid=block_group_geoid,
            zcta_geoid="90210",  # Mock ZIP
            confidence=1.0,
            source="mock_geocoder",
        )

    def geocode_address(self, address: str) -> GeocodeResult:
        """Mock geocode an address.

        Returns a predictable result.
        """
        # Mock coordinates for any address
        return self.geocode_point(37.7749, -122.4194)  # San Francisco

    def health_check(self) -> bool:
        """Mock health check always returns True."""
        return True


class NoOpGeocoder:
    """No-operation geocoder that always fails.

    Useful when geocoding is disabled or not available.
    """

    def geocode_point(self, latitude: float, longitude: float) -> GeocodeResult:
        """Always raises GeocodingError."""
        raise GeocodingError("Geocoding is disabled")

    def geocode_address(self, address: str) -> GeocodeResult:
        """Always raises GeocodingError."""
        raise GeocodingError("Geocoding is disabled")

    def health_check(self) -> bool:
        """Always returns False."""
        return False
