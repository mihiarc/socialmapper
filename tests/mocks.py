"""Mock services for external API dependencies."""

import time
import random
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock

from .factories import TestDataFactory


class MockCensusAPI:
    """Mock Census API for testing."""

    def __init__(self, delay: float = 0, fail_rate: float = 0):
        """
        Initialize mock Census API.

        Parameters
        ----------
        delay : float
            Simulated network delay in seconds.
        fail_rate : float
            Probability of failure (0-1).
        """
        self.delay = delay
        self.fail_rate = fail_rate
        self.call_count = 0

    def get_data(
        self,
        variables: List[str],
        geoids: List[str]
    ) -> Dict[str, Any]:
        """
        Mock get census data.

        Parameters
        ----------
        variables : list of str
            Variables to fetch.
        geoids : list of str
            GEOIDs to fetch data for.

        Returns
        -------
        dict
            Mock census data.

        Raises
        ------
        Exception
            If simulated failure occurs.
        """
        self.call_count += 1

        if self.delay:
            time.sleep(self.delay)

        if random.random() < self.fail_rate:
            raise Exception("Simulated Census API failure")

        return TestDataFactory.create_census_response(variables, geoids)


class MockRoutingAPI:
    """Mock routing API for isochrone generation."""

    def __init__(self, delay: float = 0, fail_rate: float = 0):
        """
        Initialize mock routing API.

        Parameters
        ----------
        delay : float
            Simulated network delay.
        fail_rate : float
            Probability of failure.
        """
        self.delay = delay
        self.fail_rate = fail_rate
        self.call_count = 0

    def create_isochrone(
        self,
        lat: float,
        lon: float,
        travel_time: int,
        mode: str = "drive"
    ) -> Dict[str, Any]:
        """
        Mock isochrone creation.

        Parameters
        ----------
        lat : float
            Latitude.
        lon : float
            Longitude.
        travel_time : int
            Travel time in minutes.
        mode : str
            Travel mode.

        Returns
        -------
        dict
            Mock isochrone geometry.

        Raises
        ------
        Exception
            If simulated failure occurs.
        """
        self.call_count += 1

        if self.delay:
            time.sleep(self.delay)

        if random.random() < self.fail_rate:
            raise Exception("Simulated Routing API failure")

        # Adjust radius based on travel time and mode
        speed_kmh = {"drive": 60, "walk": 5, "bike": 15}.get(mode, 60)
        radius_km = (travel_time / 60) * speed_kmh

        return TestDataFactory.create_isochrone_geometry(lat, lon, radius_km)


class MockGeocoder:
    """Mock geocoding service."""

    def __init__(self, delay: float = 0, fail_rate: float = 0):
        """
        Initialize mock geocoder.

        Parameters
        ----------
        delay : float
            Simulated network delay.
        fail_rate : float
            Probability of failure.
        """
        self.delay = delay
        self.fail_rate = fail_rate
        self.locations = {
            "Seattle, WA": (47.6062, -122.3321),
            "Portland, OR": (45.5152, -122.6784),
            "San Francisco, CA": (37.7749, -122.4194),
            "Los Angeles, CA": (34.0522, -118.2437),
            "New York, NY": (40.7128, -74.0060),
        }

    def geocode(self, location: str) -> Optional[tuple]:
        """
        Mock geocoding.

        Parameters
        ----------
        location : str
            Location string to geocode.

        Returns
        -------
        tuple or None
            (latitude, longitude) or None if not found.

        Raises
        ------
        Exception
            If simulated failure occurs.
        """
        if self.delay:
            time.sleep(self.delay)

        if random.random() < self.fail_rate:
            raise Exception("Simulated Geocoding failure")

        # Check known locations
        if location in self.locations:
            return self.locations[location]

        # Generate random coordinates for unknown locations
        if "," in location:  # Assume it's a city, state format
            return (
                random.uniform(25, 49),  # US latitude range
                random.uniform(-125, -65)  # US longitude range
            )

        return None


class MockPOIService:
    """Mock POI discovery service."""

    def __init__(self, delay: float = 0, fail_rate: float = 0):
        """
        Initialize mock POI service.

        Parameters
        ----------
        delay : float
            Simulated network delay.
        fail_rate : float
            Probability of failure.
        """
        self.delay = delay
        self.fail_rate = fail_rate
        self.poi_types = {
            "restaurant": ["Pizza Place", "Burger Joint", "Sushi Bar", "Cafe", "Diner"],
            "grocery": ["Supermarket", "Grocery Store", "Market", "Food Co-op"],
            "healthcare": ["Hospital", "Clinic", "Medical Center", "Urgent Care"],
            "education": ["School", "University", "College", "Library"],
            "recreation": ["Park", "Gym", "Sports Center", "Pool"],
        }

    def search_pois(
        self,
        lat: float,
        lon: float,
        categories: Optional[List[str]] = None,
        radius: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Mock POI search.

        Parameters
        ----------
        lat : float
            Latitude.
        lon : float
            Longitude.
        categories : list of str, optional
            POI categories to search.
        radius : int
            Search radius in meters.

        Returns
        -------
        list of dict
            Mock POIs.

        Raises
        ------
        Exception
            If simulated failure occurs.
        """
        if self.delay:
            time.sleep(self.delay)

        if random.random() < self.fail_rate:
            raise Exception("Simulated POI service failure")

        if not categories:
            categories = list(self.poi_types.keys())

        pois = []
        for category in categories:
            if category in self.poi_types:
                # Generate 2-5 POIs per category
                for i in range(random.randint(2, 5)):
                    name = random.choice(self.poi_types[category])
                    # Generate POI within radius
                    angle = random.uniform(0, 360)
                    distance = random.uniform(0, radius)
                    # Approximate offset
                    lat_offset = (distance / 111000) * random.uniform(-1, 1)
                    lon_offset = (distance / 111000) * random.uniform(-1, 1)

                    poi = TestDataFactory.create_poi(
                        name=f"{name} {i+1}",
                        lat=lat + lat_offset,
                        lon=lon + lon_offset,
                        category=category
                    )
                    pois.append(poi)

        return pois


def create_mock_fixtures():
    """
    Create commonly used mock fixtures.

    Returns
    -------
    dict
        Dictionary of mock services.
    """
    return {
        "census_api": MockCensusAPI(),
        "routing_api": MockRoutingAPI(),
        "geocoder": MockGeocoder(),
        "poi_service": MockPOIService(),
    }