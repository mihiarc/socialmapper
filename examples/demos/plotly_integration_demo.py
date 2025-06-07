#!/usr/bin/env python3
"""
Plotly Mapbox Demo for SocialMapper
Demonstrates the Plotly Mapbox approach compared to Folium
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from pathlib import Path
import os
from typing import Dict, Any, Optional, List
from streamlit_plotly_mapbox_events import plotly_mapbox_events

# Import SocialMapper modules - handle errors gracefully
IMPORT_ERROR = None
try:
    from socialmapper.core import run_socialmapper
    from socialmapper.ui.rich_console import create_streamlit_banner, create_rich_panel, create_performance_table
    from socialmapper.util import get_readable_census_variables
    print("SocialMapper modules imported successfully!")
except ImportError as e:
    IMPORT_ERROR = str(e)
    print(f"Warning: SocialMapper import failed: {e}")
    # We'll handle this in the main function after set_page_config

def create_sample_data():
    """Create sample census and POI data for demo purposes"""
    # Sample coordinates around Raleigh, NC area
    lat_center, lon_center = 35.7796, -78.6382
    
    # Create sample block groups
    np.random.seed(42)
    n_blockgroups = 50
    
    # Generate random points around center
    lats = np.random.normal(lat_center, 0.1, n_blockgroups)
    lons = np.random.normal(lon_center, 0.1, n_blockgroups)
    
    # Create sample census data
    census_data = []
    for i in range(n_blockgroups):
        census_data.append({
            'GEOID': f'370830{i:03d}01',
            'lat': lats[i],
            'lon': lons[i],
            'total_population': np.random.randint(500, 3000),
            'median_income': np.random.randint(30000, 120000),
            'poverty_rate': np.random.uniform(5, 35),
            'education_bachelors': np.random.uniform(15, 70),
            'housing_median_value': np.random.randint(150000, 800000)
        })
    
    census_df = pd.DataFrame(census_data)
    
    # Create sample POI data
    poi_data = [
        {'name': 'Main Library', 'lat': lat_center + 0.02, 'lon': lon_center - 0.01, 'type': 'library'},
        {'name': 'Central School', 'lat': lat_center - 0.01, 'lon': lon_center + 0.02, 'type': 'school'},
        {'name': 'Community Center', 'lat': lat_center + 0.01, 'lon': lon_center - 0.02, 'type': 'community'},
    ]
    poi_df = pd.DataFrame(poi_data)
    
    return census_df, poi_df

def create_plotly_mapbox_map(
    census_df: pd.DataFrame,
    poi_df: pd.DataFrame,
    variable: str = 'median_income',
    colorscale: str = 'Viridis',
    height: int = 600
) -> go.Figure:
    """Create a Plotly Mapbox map with census data and POIs"""
    
    # Create the base map
    fig = go.Figure()
    
    # Add census data as scatter points with color coding
    fig.add_trace(go.Scattermap(
        lat=census_df['lat'],
        lon=census_df['lon'],
        mode='markers',
        marker=dict(
            size=12,
            color=census_df[variable],
            colorscale=colorscale,
            colorbar=dict(
                title=variable.replace('_', ' ').title(),
                x=1.02
            ),
            opacity=0.7
        ),
        text=[f"GEOID: {row['GEOID']}<br>"
              f"Population: {row['total_population']:,}<br>"
              f"Median Income: ${row['median_income']:,}<br>"
              f"Poverty Rate: {row['poverty_rate']:.1f}%<br>"
              f"Bachelor's+: {row['education_bachelors']:.1f}%"
              for _, row in census_df.iterrows()],
        hovertemplate='<b>Block Group</b><br>%{text}<extra></extra>',
        name='Census Block Groups',
        customdata=census_df[['GEOID', variable]].values
    ))
    
    # Add POIs as distinct markers
    poi_colors = {'library': 'red', 'school': 'blue', 'community': 'green'}
    poi_symbols = {'library': 'library', 'school': 'school', 'community': 'town-hall'}
    
    for poi_type in poi_df['type'].unique():
        poi_subset = poi_df[poi_df['type'] == poi_type]
        fig.add_trace(go.Scattermap(
            lat=poi_subset['lat'],
            lon=poi_subset['lon'],
            mode='markers',
            marker=dict(
                size=15,
                color=poi_colors.get(poi_type, 'orange'),
                symbol=poi_symbols.get(poi_type, 'marker'),
                opacity=0.9
            ),
            text=poi_subset['name'],
            hovertemplate='<b>%{text}</b><br>Type: ' + poi_type + '<extra></extra>',
            name=f'{poi_type.title()}s',
            customdata=poi_subset[['name', 'type']].values
        ))
    
    # Update layout for map
    fig.update_layout(
        map=dict(
            style='open-street-map',
            center=dict(
                lat=census_df['lat'].mean(),
                lon=census_df['lon'].mean()
            ),
            zoom=10
        ),
        height=height,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        title="Plotly Mapbox Interactive Demo",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )
    
    return fig

def create_advanced_plotly_map(
    census_df: pd.DataFrame,
    poi_df: pd.DataFrame,
    variable: str = 'median_income'
) -> go.Figure:
    """Create an advanced Plotly map with custom interactions"""
    
    fig = go.Figure()
    
    # Create choropleth-style circles for census data
    # Normalize values for circle sizes
    values = census_df[variable]
    min_val, max_val = values.min(), values.max()
    normalized_sizes = 8 + (values - min_val) / (max_val - min_val) * 20
    
    # Add census data with variable-sized circles
    fig.add_trace(go.Scattermap(
        lat=census_df['lat'],
        lon=census_df['lon'],
        mode='markers',
        marker=dict(
            size=normalized_sizes,
            color=census_df[variable],
            colorscale='RdYlBu_r',
            colorbar=dict(
                title=variable.replace('_', ' ').title(),
                x=1.02,
                len=0.7
            ),
            opacity=0.6,
            sizemode='diameter'
        ),
        text=[f"<b>Block Group {row['GEOID'][-3:]}</b><br>"
              f"👥 Population: {row['total_population']:,}<br>"
              f"💰 Median Income: ${row['median_income']:,}<br>"
              f"📊 Poverty Rate: {row['poverty_rate']:.1f}%<br>"
              f"🎓 Bachelor's+: {row['education_bachelors']:.1f}%<br>"
              f"🏠 Median Home Value: ${row['housing_median_value']:,}"
              for _, row in census_df.iterrows()],
        hovertemplate='%{text}<extra></extra>',
        name='Demographics',
        customdata=census_df.drop(columns=['geometry'], errors='ignore').to_dict('records')
    ))
    
    # Add POIs with custom icons and styling
    poi_configs = {
        'library': {'color': '#E74C3C', 'symbol': 'library', 'emoji': '📚'},
        'school': {'color': '#3498DB', 'symbol': 'school', 'emoji': '🏫'},
        'community': {'color': '#2ECC71', 'symbol': 'town-hall', 'emoji': '🏛️'}
    }
    
    for poi_type in poi_df['type'].unique():
        poi_subset = poi_df[poi_df['type'] == poi_type]
        config = poi_configs.get(poi_type, {'color': '#F39C12', 'symbol': 'marker', 'emoji': '📍'})
        
        fig.add_trace(go.Scattermap(
            lat=poi_subset['lat'],
            lon=poi_subset['lon'],
            mode='markers',
            marker=dict(
                size=18,
                color=config['color'],
                symbol=config['symbol'],
                opacity=0.9
            ),
            text=[f"<b>{config['emoji']} {row['name']}</b><br>"
                  f"Type: {row['type'].title()}<br>"
                  f"Click for analysis!"
                  for _, row in poi_subset.iterrows()],
            hovertemplate='%{text}<extra></extra>',
            name=f"{config['emoji']} {poi_type.title()}s",
            customdata=poi_subset.drop(columns=['geometry'], errors='ignore').to_dict('records')
        ))
    
    # Update layout with better styling
    fig.update_layout(
        map=dict(
            style='open-street-map',
            center=dict(
                lat=census_df['lat'].mean(),
                lon=census_df['lon'].mean()
            ),
            zoom=11
        ),
        height=650,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        title=dict(
            text="🗺️ Advanced Plotly Mapbox Demo - Interactive Census & POI Mapping",
            font=dict(size=20),
            x=0.5
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="black",
            borderwidth=1
        ),
        font=dict(family="Arial, sans-serif")
    )
    
    return fig

def main():
    """Main Streamlit app"""
    
    # Page config
    st.set_page_config(
        page_title="Plotly Mapbox Demo - SocialMapper",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check for import errors first
    if IMPORT_ERROR:
        st.error(f"Error importing SocialMapper: {IMPORT_ERROR}")
        st.info("Make sure you're running this from the SocialMapper directory with the package installed.")
        st.warning("Some features may not work. Try using 'Sample Data' mode to explore Plotly features.")
    
    # Create banner
    if IMPORT_ERROR:
        # Fallback banner if SocialMapper imports failed
        st.title("🗺️ Plotly Mapbox Explorer")
        st.markdown("*Interactive mapping with advanced event handling*")
    else:
        st.markdown(create_streamlit_banner(
            "🗺️ Plotly Mapbox Explorer",
            "Interactive mapping with advanced event handling"
        ), unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        demo_mode = st.selectbox(
            "Demo Mode",
            ["Sample Data", "Real SocialMapper Data"],
            help="Choose between sample data or run real SocialMapper analysis"
        )
        
        if demo_mode == "Sample Data":
            # Sample data configuration
            st.subheader("Map Visualization")
            variable = st.selectbox(
                "Census Variable",
                ["median_income", "total_population", "poverty_rate", "education_bachelors", "housing_median_value"],
                help="Select variable to visualize"
            )
            
            colorscale = st.selectbox(
                "Color Scale",
                ["Viridis", "RdYlBu", "RdBu", "Spectral", "Plasma", "Inferno"],
                help="Choose color scheme"
            )
            
            map_style = st.selectbox(
                "Map Style",
                ["Basic Interactive", "Advanced with Events"],
                help="Choose map complexity level"
            )
            
        else:
            # Real SocialMapper configuration
            st.subheader("📍 Location")
            city = st.text_input("City", value="Raleigh", help="Enter city name")
            state = st.text_input("State", value="NC", help="Enter state abbreviation")
            
            st.subheader("🏢 POI Configuration")
            poi_type = st.selectbox(
                "POI Type",
                ["library", "school", "hospital", "park"],
                help="Type of points of interest to find"
            )
            
            travel_time = st.slider(
                "Travel Time (minutes)", 
                min_value=5, 
                max_value=30, 
                value=15,
                help="Maximum travel time for isochrone analysis"
            )
                        
            st.subheader("📊 Census Variables")
            if IMPORT_ERROR:
                # Fallback variables if import failed
                available_vars = ["median_income", "total_population", "poverty_rate", "education_bachelors"]
            else:
                available_vars = get_readable_census_variables()
            selected_vars = st.multiselect(
                 "Select Variables",
                 available_vars,
                 default=["median_income", "total_population"],
                 help="Choose census variables to analyze"
             )
    
    # Main content area
    if demo_mode == "Sample Data":
        st.header("📊 Sample Data Visualization")
        
        # Create sample data
        with st.spinner("Generating sample data..."):
            census_df, poi_df = create_sample_data()
        
        # Display data info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Census Block Groups", len(census_df))
        with col2:
            st.metric("Points of Interest", len(poi_df))
        
        if map_style == "Basic Interactive":
            # Basic Plotly map
            st.subheader("🗺️ Basic Plotly Mapbox Map")
            fig = create_plotly_mapbox_map(census_df, poi_df, variable, colorscale)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show data table
            with st.expander("📋 View Data"):
                tab1, tab2 = st.tabs(["Census Data", "POI Data"])
                with tab1:
                    st.dataframe(census_df)
                with tab2:
                    st.dataframe(poi_df)
        
        else:
            # Advanced map with events
            st.subheader("🗺️ Advanced Plotly Mapbox with Events")
            
            fig = create_advanced_plotly_map(census_df, poi_df, variable)
            
            # Use plotly_mapbox_events for interaction (works with scattermap too)
            selected_data = plotly_mapbox_events(
                fig, 
                click_event=True,
                hover_event=True,
                select_event=True,
                key="plotly_map"
            )
            
            # Handle map interactions
            if selected_data and len(selected_data) > 0:
                st.subheader("🎯 Map Interaction Results")
                
                # Process the most recent interaction
                latest_event = selected_data[-1]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Event Details:**")
                    st.json(latest_event)
                
                with col2:
                    if 'pointIndex' in latest_event:
                        point_idx = latest_event['pointIndex']
                        curve_number = latest_event.get('curveNumber', 0)
                        
                        if curve_number == 0:  # Census data
                            if point_idx < len(census_df):
                                selected_bg = census_df.iloc[point_idx]
                                st.markdown("**Selected Block Group:**")
                                st.markdown(f"- **GEOID:** {selected_bg['GEOID']}")
                                st.markdown(f"- **Population:** {selected_bg['total_population']:,}")
                                st.markdown(f"- **Median Income:** ${selected_bg['median_income']:,}")
                                st.markdown(f"- **Poverty Rate:** {selected_bg['poverty_rate']:.1f}%")
                                
                                # Show mini chart for this block group
                                metrics = ['total_population', 'median_income', 'poverty_rate', 'education_bachelors']
                                values = [selected_bg[m] for m in metrics]
                                mini_fig = go.Figure(data=go.Bar(x=metrics, y=values))
                                mini_fig.update_layout(height=300, title="Block Group Metrics")
                                st.plotly_chart(mini_fig, use_container_width=True)
                        
                        else:  # POI data
                            poi_idx = point_idx
                            # Adjust for POI traces (they start after census trace)
                            poi_types = poi_df['type'].unique()
                            if curve_number - 1 < len(poi_types):
                                poi_type = poi_types[curve_number - 1]
                                poi_subset = poi_df[poi_df['type'] == poi_type]
                                if poi_idx < len(poi_subset):
                                    selected_poi = poi_subset.iloc[poi_idx]
                                    st.markdown("**Selected POI:**")
                                    st.markdown(f"- **Name:** {selected_poi['name']}")
                                    st.markdown(f"- **Type:** {selected_poi['type'].title()}")
                                    st.markdown(f"- **Coordinates:** ({selected_poi['lat']:.4f}, {selected_poi['lon']:.4f})")
                                    
                                    # Calculate nearby census data
                                    poi_lat, poi_lon = selected_poi['lat'], selected_poi['lon']
                                    distances = np.sqrt((census_df['lat'] - poi_lat)**2 + (census_df['lon'] - poi_lon)**2)
                                    nearby_bg = census_df.loc[distances.idxmin()]
                                    
                                    st.markdown("**Nearest Block Group:**")
                                    st.markdown(f"- **GEOID:** {nearby_bg['GEOID']}")
                                    st.markdown(f"- **Distance:** {distances.min():.4f}° (~{distances.min()*69:.1f} miles)")
                                    st.markdown(f"- **Population:** {nearby_bg['total_population']:,}")
            
            # Show data in tabs
            with st.expander("📋 View Raw Data"):
                tab1, tab2 = st.tabs(["Census Data", "POI Data"])
                with tab1:
                    st.dataframe(census_df)
                with tab2:
                    st.dataframe(poi_df)
    
    else:
        # Real SocialMapper data
        st.header("🔄 Real SocialMapper Analysis")
        
        if IMPORT_ERROR:
            st.error("Cannot run real SocialMapper analysis due to import errors.")
            st.info("Please fix the import issues or use 'Sample Data' mode to explore Plotly features.")
        elif st.button("🚀 Run SocialMapper Analysis", type="primary"):
            with st.spinner("Running SocialMapper analysis..."):
                try:
                    # Run SocialMapper
                    results = run_socialmapper(
                        geocode_area=f"{city}, {state}",
                        poi_type=poi_type,
                        travel_time=travel_time,
                        census_variables=selected_vars,
                        export_csv=True,
                        export_maps=False,  # We'll use Plotly instead
                        use_interactive_maps=False  # Disable Folium
                    )
                    
                    st.success("✅ Analysis completed!")
                    
                    # Process results for Plotly visualization
                    if results:
                        st.subheader("📊 Analysis Results")
                        
                        # Display POI data
                        poi_data = results.get("poi_data")
                        if poi_data and 'pois' in poi_data:
                            poi_df_real = pd.DataFrame(poi_data['pois'])
                            st.markdown(f"**Found {len(poi_df_real)} POIs**")
                            
                            # Display sample POIs
                            with st.expander("View POIs"):
                                st.dataframe(poi_df_real.head(10))
                        
                        # Load and display census data if available
                        census_files = results.get("census_files", [])
                        if census_files:
                            # Load the first census file
                            census_file = census_files[0]
                            if os.path.exists(census_file):
                                census_gdf = gpd.read_file(census_file)
                                
                                # Convert to regular DataFrame for Plotly
                                census_df_real = census_gdf.copy()
                                census_df_real['lat'] = census_gdf.geometry.centroid.y
                                census_df_real['lon'] = census_gdf.geometry.centroid.x
                                
                                st.markdown(f"**Loaded {len(census_df_real)} census block groups**")
                                
                                # Create Plotly map with real data
                                if len(selected_vars) > 0:
                                    var_to_plot = selected_vars[0]  # Use first selected variable
                                    
                                    # Find the actual column name in the data
                                    matching_cols = [col for col in census_df_real.columns if var_to_plot.lower() in col.lower()]
                                    if matching_cols:
                                        actual_col = matching_cols[0]
                                        
                                        # Create real data map
                                        real_fig = create_plotly_mapbox_map(
                                            census_df_real, 
                                            poi_df_real if 'poi_df_real' in locals() else pd.DataFrame(),
                                            actual_col,
                                            "Viridis"
                                        )
                                        real_fig.update_layout(title=f"SocialMapper Results: {var_to_plot} in {city}, {state}")
                                        
                                        st.plotly_chart(real_fig, use_container_width=True)
                                    else:
                                        st.warning(f"Variable '{var_to_plot}' not found in census data")
                                        st.info(f"Available columns: {list(census_df_real.columns)}")
                            else:
                                st.error(f"Census file not found: {census_file}")
                        else:
                            st.warning("No census data files generated")
                    
                except Exception as e:
                    st.error(f"Error running SocialMapper: {e}")
                    st.info("Try with the sample data mode to explore Plotly features")
    
    # Comparison section
    st.header("📊 Plotly Mapbox vs Folium Comparison")
    
    comparison_data = {
        "Feature": [
            "Performance", "Interactivity", "Event Handling", "Customization", 
            "3D Support", "Animation", "Streaming Updates", "Mobile Support",
            "Integration", "Learning Curve"
        ],
        "Plotly Mapbox": [
            "⭐⭐⭐⭐⭐ Excellent", "⭐⭐⭐⭐⭐ Rich interactions", "⭐⭐⭐⭐⭐ Advanced events", 
            "⭐⭐⭐⭐⭐ Highly customizable", "⭐⭐⭐⭐⭐ Native 3D", "⭐⭐⭐⭐⭐ Built-in animations",
            "⭐⭐⭐⭐⭐ Real-time updates", "⭐⭐⭐⭐⭐ Responsive", "⭐⭐⭐⭐⭐ Plotly ecosystem",
            "⭐⭐⭐ Moderate"
        ],
        "Folium": [
            "⭐⭐⭐⭐ Good", "⭐⭐⭐⭐ Standard interactions", "⭐⭐⭐ Basic events",
            "⭐⭐⭐⭐ Good customization", "⭐⭐ Limited 3D", "⭐⭐ Basic animations",
            "⭐⭐ Limited streaming", "⭐⭐⭐⭐ Good mobile", "⭐⭐⭐⭐ Leaflet ecosystem",
            "⭐⭐⭐⭐⭐ Easy to learn"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # Key advantages
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Plotly Mapbox Advantages
        - **Advanced Event Handling**: Click, hover, select, zoom events
        - **Performance**: Faster rendering with large datasets
        - **Ecosystem Integration**: Works seamlessly with Plotly/Dash
        - **3D & Animation**: Native support for 3D visualizations
        - **Real-time Updates**: Easy to update maps dynamically
        - **Professional Styling**: More customization options
        """)
    
    with col2:
        st.markdown("""
        ### 🍃 Folium Advantages  
        - **Simplicity**: Easier to learn and implement
        - **Leaflet Ecosystem**: Access to many Leaflet plugins
        - **Quick Prototyping**: Faster to create basic maps
        - **Documentation**: Extensive tutorials and examples
        - **Static Export**: Better for static map generation
        - **Geospatial Focus**: Built specifically for geo-visualization
        """)

if __name__ == "__main__":
    main()