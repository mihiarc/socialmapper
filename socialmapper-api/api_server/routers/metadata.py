"""Metadata endpoints for census variables and POI types.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..models import (
    CensusVariable,
    CensusVariablesResponse,
    LocationSearchResponse,
    LocationSearchResult,
    POIType,
    POITypesResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Mock data for census variables (in production, this would come from the Census API)
CENSUS_VARIABLES = [
    CensusVariable(
        code="B01003_001E",
        name="Total Population",
        concept="Total Population",
        group="Demographics",
        universe="Total population"
    ),
    CensusVariable(
        code="B19013_001E",
        name="Median Household Income",
        concept="Median Household Income in the Past 12 Months",
        group="Income",
        universe="Households"
    ),
    CensusVariable(
        code="B15003_022E",
        name="Bachelor's Degree",
        concept="Educational Attainment",
        group="Education",
        universe="Population 25 years and over"
    ),
    CensusVariable(
        code="B08303_001E",
        name="Total Commuters",
        concept="Means of Transportation to Work",
        group="Transportation",
        universe="Workers 16 years and over"
    ),
    CensusVariable(
        code="B25001_001E",
        name="Total Housing Units",
        concept="Housing Units",
        group="Housing",
        universe="Total housing units"
    ),
    CensusVariable(
        code="B02001_002E",
        name="White Alone",
        concept="Race",
        group="Demographics",
        universe="Total population"
    ),
    CensusVariable(
        code="B02001_003E",
        name="Black or African American Alone",
        concept="Race",
        group="Demographics",
        universe="Total population"
    ),
    CensusVariable(
        code="B03002_012E",
        name="Hispanic or Latino",
        concept="Hispanic or Latino Origin",
        group="Demographics",
        universe="Total population"
    )
]

# Mock data for POI types (based on OpenStreetMap taxonomy)
POI_TYPES = [
    POIType(
        type="amenity",
        name="library",
        description="Public libraries and book lending facilities",
        category="Education & Culture",
        common_names=["library", "public library", "community library"]
    ),
    POIType(
        type="amenity",
        name="school",
        description="Educational institutions for children",
        category="Education & Culture",
        common_names=["school", "elementary school", "high school"]
    ),
    POIType(
        type="amenity",
        name="hospital",
        description="Medical facilities providing emergency and inpatient care",
        category="Healthcare",
        common_names=["hospital", "medical center", "emergency room"]
    ),
    POIType(
        type="amenity",
        name="clinic",
        description="Medical facilities for outpatient care",
        category="Healthcare",
        common_names=["clinic", "health center", "medical clinic"]
    ),
    POIType(
        type="shop",
        name="supermarket",
        description="Large grocery stores with wide selection",
        category="Food & Shopping",
        common_names=["supermarket", "grocery store", "food market"]
    ),
    POIType(
        type="shop",
        name="convenience",
        description="Small stores with extended hours",
        category="Food & Shopping",
        common_names=["convenience store", "corner store", "mini mart"]
    ),
    POIType(
        type="leisure",
        name="park",
        description="Public green spaces for recreation",
        category="Recreation",
        common_names=["park", "public park", "city park"]
    ),
    POIType(
        type="amenity",
        name="restaurant",
        description="Sit-down dining establishments",
        category="Food & Shopping",
        common_names=["restaurant", "dining", "eatery"]
    ),
    POIType(
        type="amenity",
        name="bank",
        description="Financial institutions",
        category="Services",
        common_names=["bank", "credit union", "financial institution"]
    ),
    POIType(
        type="amenity",
        name="pharmacy",
        description="Stores selling medications",
        category="Healthcare",
        common_names=["pharmacy", "drugstore", "chemist"]
    )
]


@router.get("/census/variables", response_model=CensusVariablesResponse)
async def get_census_variables(
    group: str | None = Query(None, description="Filter by variable group"),
    search: str | None = Query(None, description="Search term for variable name or concept"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    settings: Settings = Depends(get_settings)
):
    """Get available census variables for analysis.
    
    This endpoint returns a list of census variables that can be used in
    analysis requests. Variables can be filtered by group or searched by name.
    
    Args:
        group: Optional filter by variable group (e.g., "Demographics", "Income")
        search: Optional search term for variable name or concept
        limit: Maximum number of results to return
        offset: Number of results to skip for pagination
        settings: Application settings
        
    Returns:
        CensusVariablesResponse: List of available census variables
    """
    try:
        logger.info(f"Getting census variables (group={group}, search={search})")

        # Filter variables
        filtered_vars = CENSUS_VARIABLES

        if group:
            filtered_vars = [v for v in filtered_vars if v.group.lower() == group.lower()]

        if search:
            search_lower = search.lower()
            filtered_vars = [
                v for v in filtered_vars
                if search_lower in v.name.lower() or
                   search_lower in v.concept.lower() or
                   search_lower in v.code.lower()
            ]

        # Get unique categories
        categories = list(set(v.group for v in CENSUS_VARIABLES if v.group))
        categories.sort()

        # Apply pagination
        total_count = len(filtered_vars)
        paginated_vars = filtered_vars[offset:offset + limit]

        return CensusVariablesResponse(
            variables=paginated_vars,
            total_count=total_count,
            categories=categories
        )

    except Exception as e:
        logger.error(f"Failed to get census variables: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve census variables",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.get("/poi/types", response_model=POITypesResponse)
async def get_poi_types(
    category: str | None = Query(None, description="Filter by POI category"),
    search: str | None = Query(None, description="Search term for POI type or name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    settings: Settings = Depends(get_settings)
):
    """Get available POI types for analysis.
    
    This endpoint returns a list of POI types that can be used in analysis
    requests. POI types follow the OpenStreetMap taxonomy.
    
    Args:
        category: Optional filter by POI category
        search: Optional search term for POI type or name
        limit: Maximum number of results to return
        offset: Number of results to skip for pagination
        settings: Application settings
        
    Returns:
        POITypesResponse: List of available POI types
    """
    try:
        logger.info(f"Getting POI types (category={category}, search={search})")

        # Filter POI types
        filtered_pois = POI_TYPES

        if category:
            filtered_pois = [p for p in filtered_pois if p.category.lower() == category.lower()]

        if search:
            search_lower = search.lower()
            filtered_pois = [
                p for p in filtered_pois
                if search_lower in p.type.lower() or
                   search_lower in p.name.lower() or
                   (p.description and search_lower in p.description.lower()) or
                   (p.common_names and any(search_lower in name.lower() for name in p.common_names))
            ]

        # Get unique categories
        categories = list(set(p.category for p in POI_TYPES if p.category))
        categories.sort()

        # Apply pagination
        total_count = len(filtered_pois)
        paginated_pois = filtered_pois[offset:offset + limit]

        return POITypesResponse(
            poi_types=paginated_pois,
            total_count=total_count,
            categories=categories
        )

    except Exception as e:
        logger.error(f"Failed to get POI types: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve POI types",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


@router.get("/geography/search", response_model=LocationSearchResponse)
async def search_locations(
    q: str = Query(..., description="Search query for location"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    country: str | None = Query("US", description="Country code to limit search"),
    settings: Settings = Depends(get_settings)
):
    """Search for geographic locations by name.
    
    This endpoint provides geocoding functionality to find locations by name.
    It returns coordinates and other location details for use in analysis requests.
    
    Args:
        q: Search query (e.g., "Portland" or "Chicago, IL")
        limit: Maximum number of results to return
        country: Optional country code to limit search (default: US)
        settings: Application settings
        
    Returns:
        LocationSearchResponse: List of matching locations
    """
    try:
        logger.info(f"Searching for location: {q}")

        # Mock location search results
        # In production, this would use a geocoding service
        mock_results = []

        if "portland" in q.lower():
            mock_results.append(
                LocationSearchResult(
                    display_name="Portland, Multnomah County, Oregon, USA",
                    city="Portland",
                    state="Oregon",
                    country="United States",
                    latitude=45.5152,
                    longitude=-122.6784,
                    importance=0.95,
                    place_type="city"
                )
            )
            mock_results.append(
                LocationSearchResult(
                    display_name="Portland, Cumberland County, Maine, USA",
                    city="Portland",
                    state="Maine",
                    country="United States",
                    latitude=43.6591,
                    longitude=-70.2568,
                    importance=0.85,
                    place_type="city"
                )
            )
        elif "chicago" in q.lower():
            mock_results.append(
                LocationSearchResult(
                    display_name="Chicago, Cook County, Illinois, USA",
                    city="Chicago",
                    state="Illinois",
                    country="United States",
                    latitude=41.8781,
                    longitude=-87.6298,
                    importance=0.98,
                    place_type="city"
                )
            )
        elif "durham" in q.lower():
            mock_results.append(
                LocationSearchResult(
                    display_name="Durham, Durham County, North Carolina, USA",
                    city="Durham",
                    state="North Carolina",
                    country="United States",
                    latitude=35.9940,
                    longitude=-78.8986,
                    importance=0.88,
                    place_type="city"
                )
            )
        else:
            # Generic result for any other query
            mock_results.append(
                LocationSearchResult(
                    display_name=f"{q}, USA",
                    city=q.split(",")[0].strip() if "," in q else q,
                    state="Unknown",
                    country="United States",
                    latitude=40.7128,  # Default to NYC coordinates
                    longitude=-74.0060,
                    importance=0.5,
                    place_type="city"
                )
            )

        # Limit results
        limited_results = mock_results[:limit]

        return LocationSearchResponse(
            query=q,
            results=limited_results,
            total_count=len(limited_results)
        )

    except Exception as e:
        logger.error(f"Failed to search locations: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to search locations",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
