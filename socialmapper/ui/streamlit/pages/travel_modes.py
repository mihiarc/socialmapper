"""Travel Modes comparison page for the Streamlit application."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.ui.streamlit.config import CENSUS_VARIABLES, POI_TYPES, TRAVEL_MODES
from socialmapper.ui.streamlit.utils import format_number

logger = logging.getLogger(__name__)


def render_travel_modes_page():
    """Render the Travel Modes tutorial page."""
    st.header("Travel Mode Comparison")

    st.markdown("""
    Compare accessibility across different modes of transportation to understand how travel 
    options affect access to community resources.
    
    **What you'll learn:**
    - 🚶 Walking accessibility (5 km/h)
    - 🚴 Biking accessibility (15 km/h) 
    - 🚗 Driving accessibility (city speeds)
    - 📊 Comparative analysis and equity insights
    """)

    # Initialize session state
    if 'travel_mode_results' not in st.session_state:
        st.session_state.travel_mode_results = {}

    # Configuration form
    st.subheader("Configure Multi-Modal Analysis")

    with st.form("travel_mode_analysis"):
        col1, col2 = st.columns(2)

        with col1:
            location = st.text_input(
                "Location",
                value="Chapel Hill",
                help="City or area name"
            )

            state = st.text_input(
                "State",
                value="North Carolina",
                help="Full state name or abbreviation"
            )

            # POI selection
            poi_category = st.selectbox(
                "POI Category",
                options=list(POI_TYPES.keys()),
                format_func=lambda x: x.title()
            )

            poi_type = st.selectbox(
                "POI Type",
                options=POI_TYPES[poi_category],
                format_func=lambda x: x.replace('_', ' ').title()
            )

        with col2:
            travel_time = st.slider(
                "Travel Time (minutes)",
                min_value=5,
                max_value=30,
                value=15,
                step=5
            )

            modes = st.multiselect(
                "Travel Modes to Compare",
                options=list(TRAVEL_MODES.keys()),
                default=["walk", "bike", "drive"],
                format_func=lambda x: f"{TRAVEL_MODES[x]['icon']} {TRAVEL_MODES[x]['name']}"
            )

            # Census variables
            st.markdown("**Census Variables:**")
            selected_vars = []
            # Default to population and income
            default_vars = ["B01003_001E", "B19013_001E"]
            for var_code, var_name in list(CENSUS_VARIABLES.items())[:4]:  # Show first 4
                if st.checkbox(
                    var_name,
                    value=var_code in default_vars,
                    key=f"travel_census_{var_code}"
                ):
                    selected_vars.append(var_code)

        # Limit POIs for faster processing
        with st.expander("Advanced Options"):
            limit_pois = st.number_input(
                "Limit POIs (0 for all)",
                min_value=0,
                max_value=20,
                value=5,
                help="Limit the number of POIs to analyze for faster processing"
            )

        submitted = st.form_submit_button("🚀 Compare Travel Modes", type="primary")

    if submitted:
        if not modes:
            st.error("Please select at least one travel mode")
        elif not selected_vars:
            st.error("Please select at least one census variable")
        else:
            run_travel_mode_comparison(
                location, state, poi_category, poi_type,
                travel_time, modes, selected_vars, limit_pois
            )

    # Display results if available
    if st.session_state.travel_mode_results:
        display_travel_mode_results()


def run_travel_mode_comparison(location: str, state: str, poi_category: str,
                              poi_type: str, travel_time: int, modes: list[str],
                              census_vars: list[str], limit_pois: int):
    """Run analysis for multiple travel modes and store results."""
    # Clear previous results
    st.session_state.travel_mode_results = {}

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    results_by_mode = {}
    total_modes = len(modes)

    # Run analysis for each mode
    for idx, mode in enumerate(modes):
        status_text.text(f"Analyzing {TRAVEL_MODES[mode]['name']} accessibility...")
        progress = (idx / total_modes) * 0.8  # Reserve 20% for final processing
        progress_bar.progress(progress)

        try:
            with SocialMapperClient() as client:
                # Build configuration
                builder = (SocialMapperBuilder()
                    .with_location(location, state)
                    .with_osm_pois(poi_category, poi_type)
                    .with_travel_time(travel_time)
                    .with_travel_mode(mode)
                    .with_census_variables(*[k for k, v in CENSUS_VARIABLES.items() if k in census_vars])
                    .with_exports(csv=True, maps=True, isochrones=True)
                )

                # Apply POI limit if specified
                if limit_pois > 0:
                    builder = builder.limit_pois(limit_pois)

                config = builder.build()

                # Execute analysis
                result = client.run_analysis(config)

                if result.is_ok():
                    analysis_result = result.unwrap()
                    results_by_mode[mode] = {
                        'result': analysis_result,
                        'travel_time': travel_time,
                        'location': location,
                        'poi_type': poi_type
                    }
                else:
                    error = result.unwrap_err()
                    st.error(f"Error analyzing {mode}: {error.message}")
                    logger.error(f"Travel mode analysis error for {mode}: {error}")

        except Exception as e:
            st.error(f"Error during {mode} analysis: {e!s}")
            logger.exception(f"Error in travel mode analysis for {mode}")

    # Store results
    if results_by_mode:
        status_text.text("Processing comparison data...")
        progress_bar.progress(0.9)

        st.session_state.travel_mode_results = {
            'modes': results_by_mode,
            'location': location,
            'poi_type': poi_type,
            'travel_time': travel_time,
            'census_vars': census_vars
        }

        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        st.success(f"✅ Completed analysis for {len(results_by_mode)} travel modes")
        st.rerun()
    else:
        progress_bar.progress(0)
        status_text.text("")


def display_travel_mode_results():
    """Display comparison results for multiple travel modes."""
    results_data = st.session_state.travel_mode_results
    modes_data = results_data['modes']
    location = results_data['location']
    poi_type = results_data['poi_type']
    travel_time = results_data['travel_time']

    st.subheader("📊 Travel Mode Comparison Results")
    st.caption(f"{location} • {poi_type.replace('_', ' ').title()} • {travel_time} minutes")

    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", "🗺️ Maps", "📊 Demographics",
        "⚖️ Equity Analysis", "💾 Export"
    ])

    with tab1:
        display_overview_metrics(modes_data)

    with tab2:
        display_map_comparison(modes_data)

    with tab3:
        display_demographic_comparison(modes_data, results_data['census_vars'])

    with tab4:
        display_equity_analysis(modes_data, results_data['census_vars'])

    with tab5:
        display_export_options(modes_data)


def display_overview_metrics(modes_data: dict[str, Any]):
    """Display overview metrics comparing travel modes."""
    st.markdown("### Key Metrics Comparison")

    # Prepare comparison data
    comparison_data = []
    for mode, data in modes_data.items():
        result = data['result']
        comparison_data.append({
            'Mode': TRAVEL_MODES[mode]['name'],
            'Icon': TRAVEL_MODES[mode]['icon'],
            'POIs Accessible': result.poi_count,
            'Census Units': result.census_units_analyzed,
            'Population Served': getattr(result, 'total_population_served', 0)
        })

    comparison_df = pd.DataFrame(comparison_data)

    # Display metrics in columns
    cols = st.columns(len(modes_data))
    for idx, (mode, data) in enumerate(modes_data.items()):
        with cols[idx]:
            result = data['result']
            mode_info = TRAVEL_MODES[mode]

            st.markdown(f"### {mode_info['icon']} {mode_info['name']}")
            st.metric("POIs Accessible", format_number(result.poi_count))
            st.metric("Census Units", format_number(result.census_units_analyzed))

            # Calculate area if possible
            if hasattr(result, 'total_area_sqkm'):
                st.metric("Coverage Area", f"{result.total_area_sqkm:.1f} km²")

    # Comparative bar chart
    st.markdown("### Accessibility by Mode")

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("POIs Accessible", "Census Units Covered", "Population Served")
    )

    # POIs chart
    fig.add_trace(
        go.Bar(
            x=comparison_df['Mode'],
            y=comparison_df['POIs Accessible'],
            name="POIs",
            marker_color=[TRAVEL_MODES[m]['color'] for m in modes_data]
        ),
        row=1, col=1
    )

    # Census units chart
    fig.add_trace(
        go.Bar(
            x=comparison_df['Mode'],
            y=comparison_df['Census Units'],
            name="Census Units",
            marker_color=[TRAVEL_MODES[m]['color'] for m in modes_data],
            showlegend=False
        ),
        row=1, col=2
    )

    # Population chart
    fig.add_trace(
        go.Bar(
            x=comparison_df['Mode'],
            y=comparison_df['Population Served'],
            name="Population",
            marker_color=[TRAVEL_MODES[m]['color'] for m in modes_data],
            showlegend=False
        ),
        row=1, col=3
    )

    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Relative comparison
    if 'walk' in modes_data and len(modes_data) > 1:
        st.markdown("### Relative Coverage (vs Walking)")
        walk_pois = modes_data['walk']['result'].poi_count
        walk_units = modes_data['walk']['result'].census_units_analyzed

        relative_cols = st.columns(len(modes_data) - 1)
        col_idx = 0

        for mode, data in modes_data.items():
            if mode != 'walk':
                with relative_cols[col_idx]:
                    result = data['result']
                    poi_factor = result.poi_count / walk_pois if walk_pois > 0 else 0
                    unit_factor = result.census_units_analyzed / walk_units if walk_units > 0 else 0

                    st.markdown(f"**{TRAVEL_MODES[mode]['icon']} {TRAVEL_MODES[mode]['name']}**")
                    st.metric("POI Access", f"{poi_factor:.1f}x")
                    st.metric("Area Coverage", f"{unit_factor:.1f}x")
                col_idx += 1


def display_map_comparison(modes_data: dict[str, Any]):
    """Display map comparison across travel modes."""
    st.markdown("### Map Comparison")

    # Find map files for each mode
    map_files_by_mode = {}
    for mode, data in modes_data.items():
        result = data['result']
        if result.files_generated:
            for file_type, file_path in result.files_generated.items():
                if 'map' in str(file_type).lower() and Path(file_path).is_dir():
                    map_files = list(Path(file_path).glob("*accessibility*.png"))
                    if map_files:
                        map_files_by_mode[mode] = map_files[0]

    if map_files_by_mode:
        # Display maps side by side
        cols = st.columns(len(map_files_by_mode))
        for idx, (mode, map_file) in enumerate(map_files_by_mode.items()):
            with cols[idx]:
                mode_info = TRAVEL_MODES[mode]
                st.image(
                    str(map_file),
                    caption=f"{mode_info['icon']} {mode_info['name']}",
                    use_container_width=True
                )
    else:
        st.info("Map visualizations will be available after analysis completes.")

    # Show detailed map selector
    if map_files_by_mode:
        st.markdown("### Detailed Maps by Mode")

        selected_mode = st.selectbox(
            "Select mode for detailed maps:",
            options=list(modes_data.keys()),
            format_func=lambda x: f"{TRAVEL_MODES[x]['icon']} {TRAVEL_MODES[x]['name']}"
        )

        if selected_mode:
            result = modes_data[selected_mode]['result']
            if result.files_generated:
                for file_type, file_path in result.files_generated.items():
                    if 'map' in str(file_type).lower() and Path(file_path).is_dir():
                        map_files = sorted(Path(file_path).glob("*.png"))
                        if map_files:
                            # Map type selector
                            map_options = {}
                            for f in map_files:
                                if 'accessibility' in f.name:
                                    label = "Accessibility Overview"
                                elif 'distance' in f.name:
                                    label = "Distance to POIs"
                                elif 'b01003' in f.name.lower():
                                    label = "Population Density"
                                elif 'b19013' in f.name.lower():
                                    label = "Median Income"
                                else:
                                    label = f.stem
                                map_options[label] = f

                            if map_options:
                                selected_map_type = st.selectbox(
                                    "Select map type:",
                                    options=list(map_options.keys())
                                )

                                st.image(
                                    str(map_options[selected_map_type]),
                                    caption=f"{selected_map_type} - {TRAVEL_MODES[selected_mode]['name']}",
                                    use_container_width=True
                                )


def display_demographic_comparison(modes_data: dict[str, Any], census_vars: list[str]):
    """Display demographic comparison across travel modes."""
    st.markdown("### Demographic Comparison")

    # Load census data for each mode
    census_data_by_mode = {}
    for mode, data in modes_data.items():
        result = data['result']
        if result.files_generated:
            for file_type, file_path in result.files_generated.items():
                if 'census' in str(file_type).lower() and str(file_path).endswith('.csv'):
                    try:
                        df = pd.read_csv(file_path)
                        census_data_by_mode[mode] = df
                    except:
                        pass

    if census_data_by_mode:
        # Summary statistics comparison
        st.markdown("#### Census Variable Summary by Mode")

        summary_data = []
        for var_code in census_vars:
            var_name = CENSUS_VARIABLES.get(var_code, var_code)

            for mode, df in census_data_by_mode.items():
                if var_code in df.columns:
                    col_data = df[var_code].dropna()
                    if len(col_data) > 0:
                        summary_data.append({
                            'Variable': var_name,
                            'Mode': TRAVEL_MODES[mode]['name'],
                            'Total': col_data.sum() if 'population' in var_name.lower() else len(col_data),
                            'Average': col_data.mean(),
                            'Median': col_data.median()
                        })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)

            # Pivot for better comparison
            for metric in ['Average', 'Median']:
                st.markdown(f"##### {metric} Values by Mode")
                pivot_df = summary_df.pivot(index='Variable', columns='Mode', values=metric)

                # Format values
                for col in pivot_df.columns:
                    pivot_df[col] = pivot_df[col].apply(lambda x: format_number(x) if pd.notna(x) else "N/A")

                st.dataframe(pivot_df, use_container_width=True)

        # Distance distribution comparison
        st.markdown("#### Distance Distribution by Mode")

        distance_data = []
        for mode, df in census_data_by_mode.items():
            if 'travel_distance_km' in df.columns:
                distances = df['travel_distance_km'].dropna()
                distance_data.extend([{
                    'Mode': TRAVEL_MODES[mode]['name'],
                    'Distance (km)': d
                } for d in distances])

        if distance_data:
            distance_df = pd.DataFrame(distance_data)

            fig = px.box(
                distance_df,
                x='Mode',
                y='Distance (km)',
                color='Mode',
                title='Travel Distance Distribution to Nearest POI'
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Demographic data will be available after analysis completes.")


def display_equity_analysis(modes_data: dict[str, Any], census_vars: list[str]):
    """Display equity analysis comparing travel modes."""
    st.markdown("### Equity Analysis")

    # Check if we have income data
    has_income = 'B19013_001E' in census_vars
    has_poverty = 'B17001_002E' in census_vars

    if not (has_income or has_poverty):
        st.info("Add income or poverty census variables to enable equity analysis.")
        return

    # Load census data
    census_data_by_mode = {}
    for mode, data in modes_data.items():
        result = data['result']
        if result.files_generated:
            for file_type, file_path in result.files_generated.items():
                if 'census' in str(file_type).lower() and str(file_path).endswith('.csv'):
                    try:
                        df = pd.read_csv(file_path)
                        census_data_by_mode[mode] = df
                    except:
                        pass

    if census_data_by_mode and has_income:
        st.markdown("#### Income Distribution by Travel Mode Access")

        # Prepare income data
        income_data = []
        for mode, df in census_data_by_mode.items():
            if 'B19013_001E' in df.columns:
                income_values = df['B19013_001E'].dropna()
                income_data.extend([{
                    'Mode': TRAVEL_MODES[mode]['name'],
                    'Median Household Income': income
                } for income in income_values if income > 0])

        if income_data:
            income_df = pd.DataFrame(income_data)

            # Violin plot for income distribution
            fig = px.violin(
                income_df,
                x='Mode',
                y='Median Household Income',
                color='Mode',
                title='Income Distribution of Areas Served by Each Mode',
                box=True
            )

            st.plotly_chart(fig, use_container_width=True)

            # Calculate equity metrics
            st.markdown("#### Equity Metrics")

            equity_metrics = []
            for mode, df in census_data_by_mode.items():
                if 'B19013_001E' in df.columns:
                    income_data = df['B19013_001E'].dropna()
                    if len(income_data) > 0:
                        # Calculate percentage of low-income areas served
                        # Using $50,000 as threshold
                        low_income_threshold = 50000
                        low_income_areas = (income_data < low_income_threshold).sum()
                        pct_low_income = (low_income_areas / len(income_data)) * 100

                        equity_metrics.append({
                            'Mode': TRAVEL_MODES[mode]['name'],
                            'Avg Income': f"${income_data.mean():,.0f}",
                            'Low Income Areas': f"{pct_low_income:.1f}%",
                            'Income Range': f"${income_data.min():,.0f} - ${income_data.max():,.0f}"
                        })

            if equity_metrics:
                equity_df = pd.DataFrame(equity_metrics)
                st.dataframe(equity_df, use_container_width=True)

    # Key insights
    st.markdown("#### Key Equity Insights")

    insights = []

    # Compare walking vs driving access
    if 'walk' in modes_data and 'drive' in modes_data:
        walk_pois = modes_data['walk']['result'].poi_count
        drive_pois = modes_data['drive']['result'].poi_count

        if walk_pois > 0:
            accessibility_gap = ((drive_pois - walk_pois) / walk_pois) * 100
            poi_type = st.session_state.travel_mode_results.get('poi_type', 'services')
            insights.append(f"🚗 Driving provides {accessibility_gap:.0f}% more access to {poi_type} than walking")

    # Population without car access insight
    if 'walk' in census_data_by_mode:
        walk_df = census_data_by_mode['walk']
        if 'B01003_001E' in walk_df.columns:
            walk_only_pop = walk_df['B01003_001E'].sum()
            insights.append(f"🚶 {format_number(walk_only_pop)} people rely on walking distance to access services")

    # Display insights
    if insights:
        for insight in insights:
            st.info(insight)

    # Recommendations
    st.markdown("#### Recommendations for Improving Equity")

    recommendations = [
        "🚲 Invest in bike infrastructure to bridge the gap between walking and driving access",
        "🚌 Consider transit routes connecting underserved areas to essential services",
        "🏗️ Prioritize new facilities in areas with limited walking/biking access",
        "🌳 Create pedestrian-friendly corridors to improve walkability"
    ]

    for rec in recommendations:
        st.write(rec)


def display_export_options(modes_data: dict[str, Any]):
    """Display export options for travel mode comparison results."""
    st.markdown("### Export Results")

    # Create download buttons for each mode
    for mode, data in modes_data.items():
        result = data['result']
        mode_info = TRAVEL_MODES[mode]

        st.markdown(f"#### {mode_info['icon']} {mode_info['name']} Results")

        if result.files_generated:
            cols = st.columns(3)
            col_idx = 0

            for file_type, file_path in result.files_generated.items():
                path_obj = Path(file_path)

                if path_obj.exists() and path_obj.is_file():
                    with cols[col_idx % 3]:
                        with open(file_path, 'rb') as f:
                            file_data = f.read()

                        st.download_button(
                            label=f"Download {file_type.replace('_', ' ').title()}",
                            data=file_data,
                            file_name=f"{mode}_{path_obj.name}",
                            mime='text/csv' if str(file_path).endswith('.csv') else 'application/octet-stream'
                        )
                    col_idx += 1

    # Combined comparison report
    st.markdown("#### Combined Analysis Report")

    comparison_summary = {
        'analysis_type': 'travel_mode_comparison',
        'location': st.session_state.travel_mode_results['location'],
        'poi_type': st.session_state.travel_mode_results['poi_type'],
        'travel_time': st.session_state.travel_mode_results['travel_time'],
        'modes_analyzed': list(modes_data.keys()),
        'results': {}
    }

    for mode, data in modes_data.items():
        result = data['result']
        comparison_summary['results'][mode] = {
            'poi_count': result.poi_count,
            'census_units_analyzed': result.census_units_analyzed,
            'files_generated': list(result.files_generated.keys()) if result.files_generated else []
        }

    st.download_button(
        label="📄 Download Comparison Summary (JSON)",
        data=pd.Series(comparison_summary).to_json(indent=2),
        file_name="travel_mode_comparison_summary.json",
        mime="application/json"
    )
