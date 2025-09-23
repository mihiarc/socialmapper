"""Test data factories for creating mock objects."""

from typing import List, Dict, Any, Optional
import random
import json


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_census_response(
        variables: List[str],
        geoids: List[str],
        include_errors: bool = False
    ) -> Dict[str, Any]:
        """
        Create mock census API response.

        Parameters
        ----------
        variables : list of str
            Census variables to include.
        geoids : list of str
            GEOIDs to include.
        include_errors : bool
            Whether to include error values.

        Returns
        -------
        dict
            Mock census API response.
        """
        data = []

        # Header row
        header = ["NAME"] + variables
        data.append(header)

        # Data rows
        for geoid in geoids:
            row = [f"Block Group {geoid[-1]}, Census Tract {geoid[5:11]}"]
            for var in variables:
                if include_errors and random.random() < 0.1:
                    row.append(None)  # Simulate missing data
                else:
                    # Generate reasonable values based on variable type
                    if "income" in var.lower():
                        row.append(str(random.randint(30000, 150000)))
                    elif "population" in var.lower():
                        row.append(str(random.randint(500, 5000)))
                    elif "age" in var.lower():
                        row.append(str(random.randint(25, 65)))
                    else:
                        row.append(str(random.randint(100, 1000)))
            data.append(row)

        return {"data": data}

    @staticmethod
    def create_isochrone_geometry(
        center_lat: float = 47.6062,
        center_lon: float = -122.3321,
        radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """
        Create test isochrone geometry.

        Parameters
        ----------
        center_lat : float
            Center latitude.
        center_lon : float
            Center longitude.
        radius_km : float
            Approximate radius in kilometers.

        Returns
        -------
        dict
            GeoJSON polygon geometry.
        """
        # Create a rough circle with 8 points
        import math
        points = []
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            # Approximate conversion: 1 degree ≈ 111 km
            lat_offset = radius_km * math.cos(rad) / 111
            lon_offset = radius_km * math.sin(rad) / (111 * math.cos(math.radians(center_lat)))
            points.append([
                center_lon + lon_offset,
                center_lat + lat_offset
            ])
        # Close the polygon
        points.append(points[0])

        return {
            "type": "Polygon",
            "coordinates": [points]
        }

    @staticmethod
    def create_block_group(
        geoid: str,
        state_fips: str = "06",
        county_fips: str = "037"
    ) -> Dict[str, Any]:
        """
        Create a mock census block group.

        Parameters
        ----------
        geoid : str
            12-digit GEOID.
        state_fips : str
            State FIPS code.
        county_fips : str
            County FIPS code.

        Returns
        -------
        dict
            Mock block group data.
        """
        return {
            "geoid": geoid,
            "state_fips": state_fips,
            "county_fips": county_fips,
            "tract": geoid[5:11],
            "block_group": geoid[11:12],
            "geometry": TestDataFactory.create_isochrone_geometry()
        }

    @staticmethod
    def create_poi(
        name: str = "Test POI",
        lat: float = 47.6062,
        lon: float = -122.3321,
        category: str = "restaurant"
    ) -> Dict[str, Any]:
        """
        Create a mock POI.

        Parameters
        ----------
        name : str
            POI name.
        lat : float
            Latitude.
        lon : float
            Longitude.
        category : str
            POI category.

        Returns
        -------
        dict
            Mock POI data.
        """
        return {
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "category": category,
            "address": f"{random.randint(100, 9999)} Main St",
            "city": "Seattle",
            "state": "WA",
            "rating": round(random.uniform(3.0, 5.0), 1),
            "price_level": random.randint(1, 4),
            "place_id": f"poi_{random.randint(1000, 9999)}"
        }

    @staticmethod
    def create_analysis_result(
        location: str = "Seattle, WA",
        travel_time: int = 15
    ) -> Dict[str, Any]:
        """
        Create a complete mock analysis result.

        Parameters
        ----------
        location : str
            Location string.
        travel_time : int
            Travel time in minutes.

        Returns
        -------
        dict
            Complete analysis result.
        """
        # Create isochrone
        isochrone = {
            "geometry": TestDataFactory.create_isochrone_geometry(),
            "properties": {
                "travel_time": travel_time,
                "mode": "drive"
            }
        }

        # Create block groups
        blocks = [
            TestDataFactory.create_block_group(f"060370001001"),
            TestDataFactory.create_block_group(f"060370001002"),
            TestDataFactory.create_block_group(f"060370001003")
        ]

        # Create census data
        census_data = {}
        for block in blocks:
            census_data[block["geoid"]] = {
                "population": random.randint(1000, 5000),
                "median_income": random.randint(40000, 120000),
                "median_age": random.randint(25, 55)
            }

        # Create POIs
        pois = [
            TestDataFactory.create_poi(f"Restaurant {i}")
            for i in range(5)
        ]

        return {
            "location": location,
            "isochrone": isochrone,
            "blocks": blocks,
            "census_data": census_data,
            "pois": pois,
            "summary": {
                "block_count": len(blocks),
                "poi_count": len(pois),
                "travel_time": travel_time,
                "travel_mode": "drive"
            }
        }