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
