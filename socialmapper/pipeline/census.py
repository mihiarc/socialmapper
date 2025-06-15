"""
Census data integration module for the SocialMapper pipeline.

This module handles integration of census data with isochrones and POIs.
"""

from typing import Any, Dict, List, Optional, Tuple

import geopandas as gpd

from ..progress import get_progress_bar
from ..util import census_code_to_name, get_readable_census_variables, normalize_census_variable


def integrate_census_data(
    isochrone_gdf: gpd.GeoDataFrame,
    census_variables: List[str],
    api_key: Optional[str],
    poi_data: Dict[str, Any],
    geographic_level: str = "block-group",
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, List[str]]:
    """
    Integrate census data with isochrones.

    Args:
        isochrone_gdf: Isochrone GeoDataFrame
        census_variables: List of census variables
        api_key: Census API key
        poi_data: POI data for distance calculations
        geographic_level: Geographic unit ('block-group' or 'zcta')

    Returns:
        Tuple of (geographic_units_gdf, census_data_gdf, census_codes)
    """
    from ..census import get_census_system
    from ..distance import add_travel_distances

    print("\n=== Integrating Census Data ===")

    # Get census system
    census_system = get_census_system()
    
    # Process variables - normalize them to census codes
    census_codes = []
    
    for var in census_variables:
        # Normalize the variable to its census code(s)
        normalized = census_system._variable_service.normalize_variable(var)
        if isinstance(normalized, list):
            # Calculated variable - add all component codes
            census_codes.extend(normalized)
        else:
            # Simple variable - add the single code
            census_codes.append(normalized)
    
    # Remove duplicates while preserving order
    census_codes = list(dict.fromkeys(census_codes))
    
    # Display human-readable names for requested census variables
    readable_names = []
    for var in census_variables:
        normalized = census_system._variable_service.normalize_variable(var)
        if isinstance(normalized, list):
            # It's a calculated variable
            readable_names.append(census_system._variable_service.get_readable_variable(var))
        else:
            readable_names.append(census_system._variable_service.get_readable_variable(normalized))
    
    print(f"Requesting census data for: {', '.join(readable_names)}")
    print(f"Geographic level: {geographic_level}")

    # Determine states to search from POI data
    counties = census_system.get_counties_from_pois(poi_data["pois"], include_neighbors=False)
    print(f"Found {len(counties)} counties from POIs")
    state_fips = list(set([county[0] for county in counties]))

    # Get geographic units based on level
    if geographic_level == "zcta":
        # Use modern census system for ZCTA functionality
        with get_progress_bar(
            total=len(state_fips), desc="🏛️ Finding ZIP Code Tabulation Areas", unit="state"
        ) as pbar:
            geographic_units_gdf = census_system.get_zctas(state_fips)
            pbar.update(len(state_fips))

            # Filter to intersecting ZCTAs
            isochrone_union = isochrone_gdf.geometry.union_all()
            intersecting_mask = geographic_units_gdf.geometry.intersects(isochrone_union)
            geographic_units_gdf = geographic_units_gdf[intersecting_mask]

        if geographic_units_gdf is None or geographic_units_gdf.empty:
            raise ValueError("No ZIP Code Tabulation Areas found intersecting with isochrones.")

        print(f"Found {len(geographic_units_gdf)} intersecting ZIP Code Tabulation Areas")
    else:
        # Get block groups using modern census system
        with get_progress_bar(
            total=len(counties), desc="🏛️ Finding Census Block Groups", unit="county"
        ) as pbar:
            geographic_units_gdf = census_system.get_block_groups_for_counties(counties)
            pbar.update(len(counties))

            # Filter to intersecting block groups
            isochrone_union = isochrone_gdf.geometry.union_all()
            intersecting_mask = geographic_units_gdf.geometry.intersects(isochrone_union)
            geographic_units_gdf = geographic_units_gdf[intersecting_mask]

        if geographic_units_gdf is None or geographic_units_gdf.empty:
            raise ValueError("No census block groups found intersecting with isochrones.")

        print(f"Found {len(geographic_units_gdf)} intersecting census block groups")

    # Calculate travel distances in memory
    units_with_distances = add_travel_distances(
        block_groups_gdf=geographic_units_gdf, poi_data=poi_data
    )

    units_label = "ZIP Code Tabulation Areas" if geographic_level == "zcta" else "block groups"
    print(f"Calculated travel distances for {len(units_with_distances)} {units_label}")

    # Fetch census data
    geoids = units_with_distances["GEOID"].tolist()

    unit_desc = "ZCTA" if geographic_level == "zcta" else "block"
    with get_progress_bar(
        total=len(geoids), desc="📊 Integrating Census Data", unit=unit_desc
    ) as pbar:
        if geographic_level == "zcta":
            # Use modern census system for ZCTA data
            census_data = census_system._zcta_service.get_census_data(
                geoids=geoids,
                variables=census_codes,
                api_key=api_key,
                geographic_level=geographic_level,
            )
            pbar.update(len(geoids) // 2)

            # Merge census data with geographic units
            census_data_gdf = units_with_distances.copy()

            # Add census variables to the GeoDataFrame
            for _, row in census_data.iterrows():
                geoid = row["GEOID"]
                var_code = row["variable_code"]
                value = row["value"]

                # Find matching geographic unit and add the variable
                mask = census_data_gdf["GEOID"] == geoid
                if mask.any():
                    census_data_gdf.loc[mask, var_code] = value

            pbar.update(len(geoids) // 2)
        else:
            # Use modern census system for block group data
            census_data_points = census_system.get_census_data(
                census_codes,
                geoids,
                2023
            )
            pbar.update(len(geoids) // 2)

            # Merge census data with geographic units
            census_data_gdf = units_with_distances.copy()

            # Add census variables to the GeoDataFrame
            for data_point in census_data_points:
                geoid = data_point.geoid
                var_code = data_point.variable.code
                value = data_point.value

                # Find matching geographic unit and add the variable
                mask = census_data_gdf["GEOID"] == geoid
                if mask.any():
                    census_data_gdf.loc[mask, var_code] = value

            pbar.update(len(geoids) // 2)
    
    # Note: Removed human-readable name conversion to simplify the pipeline
    # Census data will use census codes (e.g., B01003_001E) directly

    # Set visualization attributes
    variables_for_viz = [var for var in census_codes if var != "NAME"]
    census_data_gdf.attrs["variables_for_visualization"] = variables_for_viz

    print(f"Retrieved census data for {len(census_data_gdf)} {units_label}")

    return geographic_units_gdf, census_data_gdf, census_codes
