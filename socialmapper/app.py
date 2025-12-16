"""SocialMapper Streamlit Application.

A user-friendly interface for spatial accessibility analysis.
No Python coding required - just enter a location and analyze.
"""

import json

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import shape
from streamlit_folium import st_folium

from socialmapper import (
    create_isochrone,
    get_census_blocks,
    get_census_data,
    get_poi,
)
from socialmapper.exceptions import SocialMapperError
from socialmapper.poi_categorization import POI_CATEGORY_MAPPING

# Page configuration
st.set_page_config(
    page_title="SocialMapper",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for cleaner look
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    if "results" not in st.session_state:
        st.session_state.results = None
    if "analysis_type" not in st.session_state:
        st.session_state.analysis_type = None
    if "location" not in st.session_state:
        st.session_state.location = None


def get_poi_categories():
    """Get available POI categories."""
    return sorted(POI_CATEGORY_MAPPING.keys())


def create_folium_map(center_lat, center_lon, zoom=12):
    """Create a base Folium map."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron",
    )
    return m


def add_isochrone_to_map(m, isochrone_geojson):
    """Add isochrone polygon to map.

    Parameters
    ----------
    m : folium.Map
        The map to add the isochrone to.
    isochrone_geojson : dict
        GeoJSON Feature dict from create_isochrone().
    """
    if isochrone_geojson:
        props = isochrone_geojson.get("properties", {})
        folium.GeoJson(
            isochrone_geojson,
            style_function=lambda x: {
                "fillColor": "#3388ff",
                "color": "#3388ff",
                "weight": 2,
                "fillOpacity": 0.3,
            },
            tooltip=f"{props.get('travel_time', '?')} min {props.get('travel_mode', '?')}",
        ).add_to(m)

        # Get centroid for marker
        geom = shape(isochrone_geojson["geometry"])
        centroid = geom.centroid
        folium.Marker(
            [centroid.y, centroid.x],
            popup=f"Center: {props.get('location', 'Unknown')}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)
    return m


def add_pois_to_map(m, pois):
    """Add POI markers to map.

    Parameters
    ----------
    m : folium.Map
        The map to add POIs to.
    pois : list of dict
        List of POI dicts from get_poi().
    """
    if pois:
        for poi in pois:
            folium.CircleMarker(
                [poi["lat"], poi["lon"]],
                radius=6,
                color="#28a745",
                fill=True,
                fillColor="#28a745",
                fillOpacity=0.7,
                popup=f"<b>{poi.get('name', 'Unknown')}</b><br>{poi.get('category', '')}",
                tooltip=poi.get("name", "POI"),
            ).add_to(m)
    return m


def add_census_data_to_map(m, gdf, column=None):
    """Add census data visualization to map as choropleth.

    Parameters
    ----------
    m : folium.Map
        The map to add census data to.
    gdf : gpd.GeoDataFrame
        GeoDataFrame with census blocks and data.
    column : str, optional
        Column to use for choropleth coloring.
    """
    if gdf is not None and len(gdf) > 0:
        # Convert to GeoJSON for Folium
        geojson_data = gdf.__geo_interface__

        if column and column in gdf.columns:
            # Create choropleth
            folium.Choropleth(
                geo_data=geojson_data,
                data=gdf,
                columns=["geoid", column],
                key_on="feature.properties.geoid",
                fill_color="YlOrRd",
                fill_opacity=0.6,
                line_opacity=0.3,
                legend_name=column,
                nan_fill_color="gray",
            ).add_to(m)
        else:
            # Simple boundary display
            folium.GeoJson(
                geojson_data,
                style_function=lambda x: {
                    "fillColor": "#3388ff",
                    "color": "#333",
                    "weight": 1,
                    "fillOpacity": 0.3,
                },
            ).add_to(m)
    return m


def run_isochrone_analysis(location, travel_mode, travel_time):
    """Run isochrone analysis."""
    with st.spinner(f"Generating {travel_time}-minute {travel_mode} isochrone..."):
        result = create_isochrone(
            location=location,
            travel_mode=travel_mode,
            travel_time=travel_time,
        )
        return result


def run_poi_analysis(location, categories):
    """Run POI discovery analysis."""
    with st.spinner(f"Finding {', '.join(categories)}..."):
        result = get_poi(
            location=location,
            categories=categories,
        )
        return result


def run_census_analysis(location, variables):
    """Run census data analysis and return GeoDataFrame with geometries."""
    with st.spinner("Fetching census demographics..."):
        # First create an isochrone to define the area
        isochrone = create_isochrone(location=location, travel_time=15, travel_mode="drive")

        # Get census block geometries
        blocks = get_census_blocks(polygon=isochrone)

        # Get census data for that area
        census_result = get_census_data(
            location=isochrone,
            variables=variables,
        )

        # Create GeoDataFrame from blocks
        if blocks:
            # Build geometry list
            geometries = []
            block_data = []
            for block in blocks:
                geom = shape(block["geometry"])
                geometries.append(geom)
                block_data.append({
                    "geoid": block["geoid"],
                    "state_fips": block.get("state_fips", ""),
                    "county_fips": block.get("county_fips", ""),
                })

            gdf = gpd.GeoDataFrame(block_data, geometry=geometries, crs="EPSG:4326")

            # Join census data to geometries
            if census_result and census_result.data:
                for geoid, data in census_result.data.items():
                    for var_name, value in data.items():
                        # Add each variable as a column
                        gdf.loc[gdf["geoid"] == geoid, var_name] = value

            return {"gdf": gdf, "variables": variables, "isochrone": isochrone}

        return None


def display_results_summary(results, analysis_type):
    """Display summary of analysis results."""
    st.subheader("Results Summary")

    if analysis_type == "Isochrone":
        if results:
            props = results.get("properties", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("Travel Mode", props.get("travel_mode", "N/A").title())
            col2.metric("Travel Time", f"{props.get('travel_time', 'N/A')} min")
            area = props.get("area_sq_km")
            if area:
                col3.metric("Coverage Area", f"{area:.2f} km²")

    elif analysis_type == "POI Discovery":
        if results:
            st.metric("POIs Found", len(results))

            # Category breakdown
            categories = {}
            for poi in results:
                cat = poi.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            if categories:
                st.write("**By Category:**")
                for cat, count in sorted(
                    categories.items(), key=lambda x: x[1], reverse=True
                ):
                    st.write(f"  - {cat}: {count}")
        else:
            st.info("No POIs found in this area.")

    elif analysis_type == "Census Data" and results and results.get("gdf") is not None:
        gdf = results["gdf"]
        st.metric("Census Blocks", len(gdf))

        # Show data preview
        st.write("**Data Preview:**")
        # Display non-geometry columns
        display_cols = [c for c in gdf.columns if c != "geometry"]
        st.dataframe(gdf[display_cols].head(10), use_container_width=True)


def export_results(results, analysis_type):
    """Create export options for results."""
    st.subheader("Export Data")

    if analysis_type == "Isochrone" and results:
        # Export as GeoJSON
        geojson = json.dumps(results, indent=2)
        st.download_button(
            label="Download Isochrone (GeoJSON)",
            data=geojson,
            file_name="isochrone.geojson",
            mime="application/json",
        )

    elif analysis_type == "POI Discovery" and results:
        # Export as CSV
        poi_data = [
            {
                "name": p.get("name", ""),
                "category": p.get("category", ""),
                "latitude": p.get("lat", ""),
                "longitude": p.get("lon", ""),
                "distance_km": p.get("distance_km", ""),
            }
            for p in results
        ]
        df = pd.DataFrame(poi_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download POIs (CSV)",
            data=csv,
            file_name="pois.csv",
            mime="text/csv",
        )

    elif analysis_type == "Census Data" and results and results.get("gdf") is not None:
        # Export as CSV
        gdf = results["gdf"]
        display_cols = [c for c in gdf.columns if c != "geometry"]
        csv = gdf[display_cols].to_csv(index=False)
        st.download_button(
            label="Download Census Data (CSV)",
            data=csv,
            file_name="census_data.csv",
            mime="text/csv",
        )


def main():
    """Run the main Streamlit application."""
    init_session_state()

    # Header
    st.markdown('<p class="main-header">🗺️ SocialMapper</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Community accessibility analysis made simple</p>',
        unsafe_allow_html=True,
    )

    # Sidebar - Analysis Configuration
    with st.sidebar:
        st.header("Analysis Settings")

        # Location input
        location = st.text_input(
            "Location",
            placeholder="Enter address, city, or lat,lon",
            help="Examples: 'Portland, OR', '123 Main St, Seattle', '45.5,-122.6'",
        )

        # Analysis type
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Isochrone", "POI Discovery", "Census Data"],
            help="Choose what type of analysis to run",
        )

        st.divider()

        # Analysis-specific options
        if analysis_type == "Isochrone":
            st.subheader("Isochrone Settings")
            travel_mode = st.selectbox(
                "Travel Mode",
                ["walk", "bike", "drive"],
                format_func=lambda x: x.title(),
            )
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=60,
                value=15,
                step=5,
            )

        elif analysis_type == "POI Discovery":
            st.subheader("POI Settings")
            available_categories = get_poi_categories()
            categories = st.multiselect(
                "POI Categories",
                available_categories,
                default=["grocery"] if "grocery" in available_categories else available_categories[:1],
                help="Select types of places to find",
            )

        elif analysis_type == "Census Data":
            st.subheader("Census Settings")
            variable_options = {
                "Total Population": "total_population",
                "Median Household Income": "median_household_income",
                "Poverty Rate": "poverty_rate",
                "Median Age": "median_age",
            }
            selected_vars = st.multiselect(
                "Demographics",
                list(variable_options.keys()),
                default=["Total Population"],
            )
            variables = [variable_options[v] for v in selected_vars]

        st.divider()

        # Run button
        run_disabled = not location
        if st.button("Run Analysis", type="primary", disabled=run_disabled):
            try:
                results = None
                if analysis_type == "Isochrone":
                    results = run_isochrone_analysis(location, travel_mode, travel_time)
                elif analysis_type == "POI Discovery":
                    if not categories:
                        st.error("Please select at least one POI category.")
                    else:
                        results = run_poi_analysis(location, categories)
                elif analysis_type == "Census Data":
                    if not variables:
                        st.error("Please select at least one demographic variable.")
                    else:
                        results = run_census_analysis(location, variables)

                st.session_state.results = results
                st.session_state.analysis_type = analysis_type
                st.session_state.location = location

            except SocialMapperError as e:
                st.error(f"Analysis error: {e}")
            except Exception as e:
                import traceback
                st.error(f"Unexpected error: {e}")
                st.code(traceback.format_exc(), language="text")

        if not location:
            st.info("Enter a location to begin")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Map")

        # Display map with results
        results = st.session_state.results
        analysis_type = st.session_state.analysis_type

        if results:
            # Determine map center based on analysis type
            if analysis_type == "Isochrone":
                # Get centroid of isochrone geometry
                geom = shape(results["geometry"])
                centroid = geom.centroid
                center_lat, center_lon = centroid.y, centroid.x
            elif analysis_type == "POI Discovery" and results:
                # Center on first POI
                center_lat = results[0]["lat"]
                center_lon = results[0]["lon"]
            elif analysis_type == "Census Data" and results.get("gdf") is not None:
                # Center on GeoDataFrame centroid
                gdf = results["gdf"]
                centroid = gdf.geometry.unary_union.centroid
                center_lat, center_lon = centroid.y, centroid.x
            else:
                # Default US center
                center_lat, center_lon = 39.8283, -98.5795

            # Create map
            m = create_folium_map(center_lat, center_lon)

            # Add results to map
            if analysis_type == "Isochrone":
                m = add_isochrone_to_map(m, results)
                # Fit to isochrone bounds
                geom = shape(results["geometry"])
                bounds = geom.bounds  # (minx, miny, maxx, maxy)
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            elif analysis_type == "POI Discovery":
                m = add_pois_to_map(m, results)
                if results:
                    # Fit to POI bounds
                    lats = [p["lat"] for p in results]
                    lons = [p["lon"] for p in results]
                    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
            elif analysis_type == "Census Data" and results.get("gdf") is not None:
                gdf = results["gdf"]
                variables = results.get("variables", [])
                # Use first variable for choropleth if available
                column = variables[0] if variables else None
                m = add_census_data_to_map(m, gdf, column=column)
                # Fit to bounds
                bounds = gdf.total_bounds  # (minx, miny, maxx, maxy)
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            st_folium(m, width=None, height=500, use_container_width=True)
        else:
            # Show default map
            m = create_folium_map(39.8283, -98.5795, zoom=4)
            st_folium(m, width=None, height=500, use_container_width=True)
            st.info("Configure your analysis in the sidebar and click 'Run Analysis'")

    with col2:
        if results:
            display_results_summary(results, analysis_type)
            st.divider()
            export_results(results, analysis_type)


if __name__ == "__main__":
    main()
