"""Fragment-based components for improved performance."""

import logging
from typing import Any

import streamlit as st
from streamlit_folium import st_folium

from ..utils.cache import get_map_base_config
from .maps import create_poi_map

logger = logging.getLogger(__name__)


def extract_analysis_data(analysis_result: dict[str, Any]) -> tuple[list, Any]:
    """Extract POIs and isochrones from different result formats.
    
    Args:
        analysis_result: Analysis result in various formats
        
    Returns:
        Tuple of (pois_list, isochrones_data)
    """
    pois = []
    isochrones = None

    if isinstance(analysis_result, dict):
        pois = analysis_result.get('pois', [])
        isochrones = analysis_result.get('isochrones')
    elif hasattr(analysis_result, 'pois'):
        # Handle AnalysisResult object
        pois = getattr(analysis_result, 'pois', [])
        isochrones = getattr(analysis_result, 'isochrones', None)

    return pois, isochrones


def find_closest_poi(poi_df, clicked_lat: float, clicked_lon: float, max_distance: float = 0.01):
    """Find the closest POI to clicked coordinates.
    
    Args:
        poi_df: DataFrame with POI data
        clicked_lat: Clicked latitude
        clicked_lon: Clicked longitude
        max_distance: Maximum distance to consider (degrees)
        
    Returns:
        Closest POI data or None
    """
    import numpy as np

    # Calculate distances
    distances = np.sqrt((poi_df['lat'] - clicked_lat)**2 + (poi_df['lon'] - clicked_lon)**2)
    min_idx = distances.idxmin()

    if distances[min_idx] <= max_distance:
        return poi_df.iloc[min_idx].to_dict()

    return None


def handle_map_rendering_error(error: Exception, analysis_result: dict[str, Any]):
    """Handle map rendering errors with detailed troubleshooting.
    
    Args:
        error: The exception that occurred
        analysis_result: The analysis result data
    """
    logger.error(f"Error rendering map: {error}", exc_info=True)

    # Import error dialog if available
    try:
        from .dialogs import dialogs_available, show_error_dialog
        if dialogs_available():
            show_error_dialog(
                "Map Rendering Failed",
                f"Error details: {error!s}\n\nThis could be due to:\n"
                f"- Invalid analysis data format\n"
                f"- Missing required map data (POIs or isochrones)\n"
                f"- Folium/mapping library issues\n"
                f"- Browser compatibility problems"
            )
        else:
            st.error(f"Unable to render map: {error!s}")
    except ImportError:
        st.error(f"Unable to render map: {error!s}")

    # Add troubleshooting info
    with st.expander("🔧 Map Troubleshooting"):
        st.markdown(f"""
        **Possible solutions:**
        1. **Refresh the page** and try the analysis again
        2. **Check your data**: Ensure the analysis completed successfully
        3. **Try a different location** or POI type
        4. **Disable browser extensions** that might interfere with maps
        5. **Clear browser cache** and reload the page
        
        **Technical details:**
        - Error type: `{type(error).__name__}`
        - Error message: `{error!s}`
        
        **Debug information:**
        - Analysis result type: `{type(analysis_result).__name__}`
        - Has POI data: `{bool(analysis_result.get('pois', []) if isinstance(analysis_result, dict) else False)}`
        - POI count: `{len(analysis_result.get('pois', [])) if isinstance(analysis_result, dict) else 'N/A'}`
        """)

    # Add a retry button
    if st.button("🔄 Retry Map Rendering"):
        st.rerun()


@st.fragment
def render_interactive_map(
    analysis_result: dict[str, Any],
    height: int = 600,
    update_interval: int | None = None
) -> None:
    """Render an interactive map as a fragment that can update independently.
    
    This fragment allows the map to be rerun without rerunning the entire app,
    improving performance when users interact with map controls.
    
    Args:
        analysis_result: Analysis results containing POI and isochrone data
        height: Height of the map in pixels
        update_interval: If set, auto-refresh the map at this interval (seconds)
    """
    # Get base map configuration
    base_config = get_map_base_config()

    # Add map controls in the fragment
    col1, col2, col3 = st.columns(3)

    with col1:
        show_isochrone = st.checkbox("Show Travel Time Area", value=True)

    with col2:
        show_poi_labels = st.checkbox("Show POI Labels", value=True)

    with col3:
        map_style = st.selectbox("Map Style", ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter"], index=0)

    # Create the map with current settings
    try:
        # Handle different result formats (dict, object, or AnalysisResult)
        pois, isochrones = extract_analysis_data(analysis_result)

        if not pois:
            st.info("No POI data available to display on map.")
            return

        # Convert POI list to DataFrame format expected by create_poi_map
        import pandas as pd

        # Transform POI data to include name from tags
        processed_pois = []
        for poi in pois:
            processed_poi = poi.copy() if isinstance(poi, dict) else {
                'lat': getattr(poi, 'lat', 0),
                'lon': getattr(poi, 'lon', 0),
                'name': getattr(poi, 'name', 'Unnamed'),
                'type': getattr(poi, 'type', 'POI')
            }

            # Extract name from tags, with fallback
            if isinstance(processed_poi, dict):
                if 'tags' in processed_poi and isinstance(processed_poi['tags'], dict):
                    processed_poi['name'] = processed_poi['tags'].get('name', f"Unnamed {processed_poi.get('type', 'POI')}")
                elif 'name' not in processed_poi or not processed_poi['name']:
                    processed_poi['name'] = f"Unnamed {processed_poi.get('type', 'POI')}"

            processed_pois.append(processed_poi)

        poi_df = pd.DataFrame(processed_pois)

        # Ensure required columns exist
        required_cols = ['lat', 'lon', 'name']
        missing_cols = [col for col in required_cols if col not in poi_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required POI data columns: {missing_cols}")

        # Process isochrone data
        isochrone_data = None
        isochrone_bounds = None
        center_lat = poi_df['lat'].mean()  # Default fallback
        center_lon = poi_df['lon'].mean()  # Default fallback

        logger.info(f"Fragment - Show isochrone: {show_isochrone}")
        logger.info(f"Fragment - Isochrones type: {type(isochrones)}")
        logger.info(f"Fragment - Isochrones value: {isochrones}")

        # Calculate bounds and center from isochrone if available
        if isochrones is not None and hasattr(isochrones, 'geometry') and not isochrones.empty:
            logger.info(f"Fragment - Processing isochrones for map bounds, shape: {isochrones.shape}")
            try:
                # Calculate isochrone bounds for map extent
                minx, miny, maxx, maxy = isochrones.total_bounds
                isochrone_bounds = [[miny, minx], [maxy, maxx]]

                # Use isochrone centroid as map center
                isochrone_centroid = isochrones.geometry.centroid.iloc[0]
                center_lat = isochrone_centroid.y
                center_lon = isochrone_centroid.x
                logger.info(f"Fragment - Using isochrone center: ({center_lat:.6f}, {center_lon:.6f})")

                # Convert to GeoJSON if we need to show the isochrone overlay
                if show_isochrone:
                    isochrone_data = isochrones.to_json() if hasattr(isochrones, 'to_json') else None
                    logger.info(f"Fragment - Successfully converted to GeoJSON: {isochrone_data is not None}")

            except Exception as e:
                logger.warning(f"Could not process isochrones: {e}")
        else:
            logger.info("Fragment - No valid isochrones found, using POI center")

        # Create the map
        map_obj = create_poi_map(
            center_lat=center_lat,
            center_lon=center_lon,
            pois=poi_df,
            isochrone_data=isochrone_data,
            isochrone_bounds=isochrone_bounds,
            zoom_start=base_config.get('zoom_start', 12),
            tiles=map_style,
            show_poi_labels=show_poi_labels
        )

        # Display the map with full width
        map_data = st_folium(
            map_obj,
            height=height,
            width=None,  # None means use full container width
            returned_objects=["last_object_clicked"],
            key=f"map_{id(analysis_result)}"
        )

        # Show clicked POI information
        if map_data['last_object_clicked'] and map_data['last_object_clicked'].get('lat'):
            clicked_lat = map_data['last_object_clicked']['lat']
            clicked_lon = map_data['last_object_clicked']['lon']

            # Find closest POI to clicked location
            closest_poi = find_closest_poi(poi_df, clicked_lat, clicked_lon)
            if closest_poi is not None:
                st.info(f"📍 Selected: {closest_poi['name']} ({closest_poi.get('type', 'Unknown type')})")

    except Exception as e:
        handle_map_rendering_error(e, analysis_result)


@st.fragment(run_every=30)  # Auto-refresh every 30 seconds
def render_live_metrics(analysis_result: dict[str, Any]) -> None:
    """Render metrics that can update independently.
    
    This fragment displays key metrics and can auto-refresh to show
    the latest data without rerunning the entire app.
    
    Args:
        analysis_result: Analysis results containing metrics
    """
    if not analysis_result:
        return

    # Extract metrics with safe defaults
    poi_count = analysis_result.get('poi_count', 0)
    population = analysis_result.get('total_population', 0)
    area_km2 = analysis_result.get('area_km2', 0)
    census_units = analysis_result.get('census_units_analyzed', 0)

    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="POIs Found",
            value=f"{poi_count:,}",
            delta=None,
            help="Number of points of interest found in the search area"
        )

    with col2:
        st.metric(
            label="Population",
            value=f"{population:,}",
            delta=None,
            help="Total population within the travel time area"
        )

    with col3:
        st.metric(
            label="Area",
            value=f"{area_km2:.1f} km²",
            delta=None,
            help="Total area covered by the travel time isochrone"
        )

    with col4:
        st.metric(
            label="Census Units",
            value=f"{census_units:,}",
            delta=None,
            help="Number of census block groups analyzed"
        )

    # Add timestamp
    import datetime
    st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")


@st.fragment
def render_demographic_charts(
    analysis_result: dict[str, Any],
    census_vars: list[str]
) -> None:
    """Render demographic charts as a fragment.
    
    This allows demographic visualizations to update independently
    when users change chart settings.
    
    Args:
        analysis_result: Analysis results containing demographic data
        census_vars: List of census variable codes to display
    """
    if not analysis_result:
        st.info("No analysis results available.")
        return

    # Extract demographics from different result formats
    demographics = {}
    if isinstance(analysis_result, dict):
        demographics = analysis_result.get('demographics', {})
    elif hasattr(analysis_result, 'demographics'):
        demographics = getattr(analysis_result, 'demographics', {})

    if not demographics:
        st.info("No demographic data available. Run an analysis with census variables selected.")
        return

    # Filter to only show variables that have data
    available_vars = [var for var in census_vars if var in demographics and demographics[var] is not None]

    if not available_vars:
        st.warning("No data available for the selected census variables.")
        return

    # Chart controls
    col1, col2 = st.columns([2, 1])

    with col1:
        chart_type = st.radio(
            "Chart Type",
            options=["Bar Chart", "Table", "Summary Cards"],
            horizontal=True
        )

    with col2:
        show_formatted = st.checkbox("Format Values", value=True, help="Show human-readable formatted values")

    if chart_type == "Bar Chart":
        render_demographic_bar_chart(demographics, available_vars, show_formatted)
    elif chart_type == "Table":
        render_demographic_table(demographics, available_vars, show_formatted)
    else:  # Summary Cards
        render_demographic_cards(demographics, available_vars, show_formatted)


def render_demographic_bar_chart(demographics: dict, census_vars: list[str], show_formatted: bool):
    """Render demographic data as a bar chart."""
    import pandas as pd
    import plotly.express as px


    # Prepare data for bar chart
    data = []
    for var_code in census_vars:
        if var_code in demographics and demographics[var_code] is not None:
            value = demographics[var_code]
            if show_formatted:
                # Get human-readable name
                var_names = {
                    "B01003_001E": "Total Population",
                    "B19013_001E": "Median Household Income",
                    "B25077_001E": "Median Home Value",
                    "B15003_022E": "Bachelor's Degree Holders",
                    "B08301_021E": "Public Transit Users",
                    "B17001_002E": "Population in Poverty"
                }
                display_name = var_names.get(var_code, var_code)
            else:
                display_name = var_code

            data.append({
                'Variable': display_name,
                'Value': float(value),
                'Code': var_code
            })

    if data:
        df = pd.DataFrame(data)

        # Create bar chart with better formatting
        fig = px.bar(
            df,
            x='Variable',
            y='Value',
            title="Demographic Analysis Results",
            hover_data=['Code'] if not show_formatted else None
        )

        # Improve chart appearance
        fig.update_layout(
            xaxis_title="Demographic Variables",
            yaxis_title="Value",
            showlegend=False,
            height=400
        )

        # Format y-axis based on data type
        if any('income' in var.lower() or 'value' in var.lower() for var in df['Variable']):
            fig.update_yaxis(tickformat='$,.0f')
        else:
            fig.update_yaxis(tickformat=',.0f')

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid data for chart display")


def render_demographic_table(demographics: dict, census_vars: list[str], show_formatted: bool):
    """Render demographic data as a formatted table."""
    import pandas as pd

    from ..utils.formatters import format_census_variable

    # Prepare table data
    table_data = []
    for var_code in census_vars:
        if var_code in demographics and demographics[var_code] is not None:
            value = demographics[var_code]

            if show_formatted:
                formatted_value = format_census_variable(var_code, value)
                # Extract just the formatted value part
                if ': ' in formatted_value:
                    display_value = formatted_value.split(': ', 1)[1]
                    variable_name = formatted_value.split(': ', 1)[0]
                else:
                    display_value = str(value)
                    variable_name = var_code
            else:
                display_value = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
                variable_name = var_code

            table_data.append({
                'Variable': variable_name,
                'Value': display_value,
                'Code': var_code
            })

    if table_data:
        df = pd.DataFrame(table_data)

        # Configure column display
        column_config = {
            'Variable': st.column_config.TextColumn('Demographic Variable', width='medium'),
            'Value': st.column_config.TextColumn('Value', width='medium'),
        }

        if not show_formatted:
            column_config['Code'] = st.column_config.TextColumn('Census Code', width='small')
        else:
            # Hide code column when showing formatted names
            df = df.drop('Code', axis=1)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
    else:
        st.warning("No data available for table display")


def render_demographic_cards(demographics: dict, census_vars: list[str], show_formatted: bool):
    """Render demographic data as summary cards."""
    from ..utils.formatters import format_census_variable

    # Create cards in columns
    num_vars = len(census_vars)
    if num_vars <= 2:
        cols = st.columns(num_vars)
    elif num_vars <= 4:
        cols = st.columns(2)
    else:
        cols = st.columns(3)

    col_idx = 0
    for var_code in census_vars:
        if var_code in demographics and demographics[var_code] is not None:
            value = demographics[var_code]

            with cols[col_idx % len(cols)]:
                if show_formatted:
                    formatted = format_census_variable(var_code, value)
                    if ': ' in formatted:
                        var_name, display_value = formatted.split(': ', 1)
                    else:
                        var_name = var_code
                        display_value = str(value)
                else:
                    var_name = var_code
                    display_value = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)

                # Create metric card
                st.metric(
                    label=var_name,
                    value=display_value,
                    help=f"Census variable: {var_code}"
                )

            col_idx += 1


@st.fragment
def render_poi_table_fragment(
    analysis_result: dict[str, Any],
    page_size: int = 10
) -> None:
    """Render POI table as a fragment with pagination and sorting.
    
    This allows the POI table to have its own pagination and sorting without
    rerunning the entire app.
    
    Args:
        analysis_result: Analysis results containing POI data
        page_size: Number of POIs to show per page
    """
    # Extract POIs from different result formats
    pois, _ = extract_analysis_data(analysis_result)

    if not pois:
        st.info("No POIs found in the analysis area.")
        return

    # Table controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader(f"🏢 Points of Interest ({len(pois)} found)")

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=["Distance", "Name", "Type"],
            index=0
        )

    with col3:
        page_size = st.selectbox(
            "Items per page",
            options=[5, 10, 20, 50],
            index=1
        )

    # Process and sort POI data
    processed_pois = []
    for poi in pois:
        # Handle both dict and object formats
        if isinstance(poi, dict):
            # Extract name from tags if available
            name = 'Unnamed'
            if 'tags' in poi and isinstance(poi['tags'], dict):
                name = poi['tags'].get('name', f"Unnamed {poi.get('type', 'POI')}")
            elif 'name' in poi:
                name = poi['name']

            # Extract address from tags if available
            address = 'N/A'
            if 'tags' in poi and isinstance(poi['tags'], dict):
                addr_parts = []
                for addr_field in ['addr:housenumber', 'addr:street', 'addr:city']:
                    if poi['tags'].get(addr_field):
                        addr_parts.append(poi['tags'][addr_field])
                if addr_parts:
                    address = ' '.join(addr_parts)

            # Extract other fields
            poi_type = poi.get('type', 'Unknown')
            distance = poi.get('distance', 0)
            travel_time = poi.get('travel_time', 0)
            lat = poi.get('lat', 0)
            lon = poi.get('lon', 0)
        else:
            # Handle object format
            name = getattr(poi, 'name', 'Unnamed')
            poi_type = getattr(poi, 'type', 'Unknown')
            distance = getattr(poi, 'distance', 0)
            travel_time = getattr(poi, 'travel_time', 0)
            lat = getattr(poi, 'lat', 0)
            lon = getattr(poi, 'lon', 0)
            address = getattr(poi, 'address', 'N/A')

        processed_pois.append({
            'Name': name,
            'Type': poi_type,
            'Distance (km)': round(float(distance), 2),
            'Travel Time (min)': round(float(travel_time), 1) if travel_time else 0,
            'Address': address,
            'Coordinates': f"{lat:.6f}, {lon:.6f}"
        })

    # Sort data
    import pandas as pd
    df = pd.DataFrame(processed_pois)

    if sort_by == "Distance":
        df = df.sort_values('Distance (km)')
    elif sort_by == "Name":
        df = df.sort_values('Name')
    elif sort_by == "Type":
        df = df.sort_values('Type')

    # Pagination
    total_pages = (len(df) + page_size - 1) // page_size

    # Page selector
    col1, col2 = st.columns([1, 3])
    with col1:
        page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )

    with col2:
        st.write(f"Showing {min((page-1)*page_size + 1, len(df))} to {min(page*page_size, len(df))} of {len(df)} POIs")

    # Calculate indices for current page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(df))

    # Display table with enhanced configuration
    if not df.empty:
        page_df = df.iloc[start_idx:end_idx].reset_index(drop=True)

        # Configure columns
        column_config = {
            'Name': st.column_config.TextColumn('Name', width='large'),
            'Type': st.column_config.TextColumn('Type', width='medium'),
            'Distance (km)': st.column_config.NumberColumn('Distance (km)', format='%.2f km', width='small'),
            'Travel Time (min)': st.column_config.NumberColumn('Travel Time (min)', format='%.1f min', width='small'),
            'Address': st.column_config.TextColumn('Address', width='large'),
            'Coordinates': st.column_config.TextColumn('Coordinates', width='medium')
        }

        st.dataframe(
            page_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )

        # Enhanced navigation
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if page > 1:
                if st.button("⏮️ First"):
                    st.rerun()

        with col2:
            if page > 1:
                if st.button("← Previous"):
                    st.rerun()

        with col3:
            st.write(f"Page {page} of {total_pages}")

        with col4:
            if page < total_pages:
                if st.button("Next →"):
                    st.rerun()

        with col5:
            if page < total_pages:
                if st.button("Last ⏭️"):
                    st.rerun()

        # Export options for current view
        with st.expander("📥 Export Options"):
            col1, col2 = st.columns(2)

            with col1:
                # Export current page
                csv_data = page_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download Current Page (CSV)",
                    data=csv_data,
                    file_name=f"pois_page_{page}.csv",
                    mime="text/csv"
                )

            with col2:
                # Export all POIs
                all_csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download All POIs (CSV)",
                    data=all_csv_data,
                    file_name="all_pois.csv",
                    mime="text/csv"
                )
    else:
        st.warning("No POI data to display")
