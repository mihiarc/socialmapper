"""Address Geocoding Tutorial - Interactive Version.

This page mirrors the [Address Geocoding Tutorial](https://mihiarc.github.io/socialmapper/tutorials/address-geocoding-tutorial/) documentation example,
demonstrating how to convert addresses into coordinates for analysis.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

# Set up logging
logger = logging.getLogger(__name__)

# Try importing geocoding components
try:
    from socialmapper import SocialMapperBuilder, SocialMapperClient
    from socialmapper.geocoding import (
        AddressInput,
        AddressProvider,
        AddressQuality,
        GeocodingConfig,
        geocode_address,
    )
    GEOCODING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import geocoding components: {e}")
    GEOCODING_AVAILABLE = False



def render_address_geocoding_page():
    """Render the Address Geocoding tutorial page."""
    st.header("📮 Address Geocoding Tutorial")

    st.markdown("""
    This tutorial demonstrates how to convert addresses into coordinates for analysis.

    **What you'll learn:**
    - 📍 Understanding geocoding providers and quality levels
    - 🔍 Single address vs batch processing
    - 🗺️ Integration with SocialMapper workflows
    - ⚠️ Error handling and performance optimization
    - 📁 Creating POI datasets from address lists

    *This tutorial mirrors the documentation example: geocoding addresses and analyzing accessibility.*
    """)

    # Check if geocoding is available
    if not GEOCODING_AVAILABLE:
        st.error("""
        ❌ Geocoding components are not available. Please ensure SocialMapper is installed with geocoding support.

        Try: `uv pip install -e .`
        """)
        return

    # Tutorial steps info
    with st.container():
        st.info("""
        💡 **Tutorial Steps:**
        1. Understanding Geocoding - Learn about providers and quality
        2. Single Address - Geocode individual addresses
        3. Quality Levels - Understand geocoding accuracy
        4. Batch Processing - Handle multiple addresses efficiently
        5. SocialMapper Integration - Use geocoded data for analysis
        """)

    # Create tabs for tutorial steps
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Understanding",
        "📍 Single Address",
        "📊 Quality Levels",
        "📋 Batch Processing",
        "🗺️ Integration"
    ])

    with tab1:
        render_understanding_geocoding()

    with tab2:
        render_single_address_section()

    with tab3:
        render_quality_levels()

    with tab4:
        render_batch_address_section()

    with tab5:
        render_integration_section()


def render_understanding_geocoding():
    """Step 1: Understanding Geocoding - Educational content."""
    st.subheader("📍 Understanding Address Geocoding")

    st.markdown("""
    Address geocoding converts human-readable addresses into geographic coordinates (latitude/longitude).
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **🎯 Why Use Geocoding?**
        • Convert address lists into mappable coordinates
        • Analyze service accessibility by street address
        • Integrate business locations with demographic data
        • Create custom POI datasets from address databases

        **📍 Common Use Cases:**
        • Customer address analysis
        • Service area planning
        • Site selection studies
        • Demographic profiling by address
        """)

    with col2:
        st.success("""
        **🏗️ SocialMapper Providers:**

        **Nominatim (OpenStreetMap):**
        • Free and open source
        • Global coverage
        • Good for general use
        • Rate limited for fairness

        **Census Bureau:**
        • US addresses only
        • Very accurate for US
        • Government data source
        • Free with API key

        ✅ Automatic fallback between providers!
        """)

    # Quality levels explanation
    st.markdown("### 📊 Geocoding Quality Levels")

    quality_df = pd.DataFrame({
        'Quality Level': ['EXACT', 'INTERPOLATED', 'CENTROID', 'APPROXIMATE'],
        'Description': [
            'Rooftop-level precision',
            'Street segment interpolation',
            'City/ZIP centroid',
            'State/region level'
        ],
        'Use Cases': [
            'Critical applications',
            'Most business uses',
            'Regional analysis',
            'Rough estimates only'
        ],
        'Accuracy': [
            '< 50 meters',
            '< 200 meters',
            '< 5 km',
            '> 5 km'
        ]
    })

    st.dataframe(quality_df.set_index('Quality Level'), use_container_width=True)


def render_single_address_section():
    """Step 2: Single Address Geocoding."""
    st.subheader("📍 Single Address Geocoding")

    st.markdown("""
    Let's start by geocoding a single address. We'll use a famous address as our example.
    """)

    # Pre-populate with tutorial example
    st.info("""
    🏦 **Tutorial Example**: We'll geocode the White House address:
    1600 Pennsylvania Avenue NW, Washington, DC 20500
    """)

    with st.form("single_address"):
        address = st.text_input(
            "Street Address",
            value="1600 Pennsylvania Avenue NW, Washington, DC 20500",
            help="Enter a full street address",
            key="single_address_input"
        )

        # Provider selection
        col1, col2 = st.columns(2)

        with col1:
            provider = st.selectbox(
                "Geocoding Provider",
                options=["Nominatim (OpenStreetMap)", "Census Bureau"],
                help="Choose the geocoding service"
            )

        with col2:
            min_quality = st.selectbox(
                "Minimum Quality Threshold",
                options=["APPROXIMATE", "CENTROID", "INTERPOLATED", "EXACT"],
                index=0,
                help="Minimum acceptable geocoding quality"
            )

        submitted = st.form_submit_button("🔍 Geocode Address", type="primary")

    if submitted and address:
        with st.spinner("🔍 Geocoding address..."):
            try:
                # Create address input
                address_input = AddressInput(
                    address=address,
                    id="single_demo",
                    source="tutorial"
                )

                # Configure geocoding
                selected_provider = AddressProvider.NOMINATIM if "Nominatim" in provider else AddressProvider.CENSUS
                quality_map = {
                    "EXACT": AddressQuality.EXACT,
                    "INTERPOLATED": AddressQuality.INTERPOLATED,
                    "CENTROID": AddressQuality.CENTROID,
                    "APPROXIMATE": AddressQuality.APPROXIMATE
                }

                config = GeocodingConfig(
                    primary_provider=selected_provider,
                    fallback_providers=[AddressProvider.CENSUS] if selected_provider == AddressProvider.NOMINATIM else [AddressProvider.NOMINATIM],
                    min_quality_threshold=quality_map[min_quality]
                )

                # Geocode the address
                result = geocode_address(address_input, config)

                if result.success:
                    st.success("✅ Address geocoded successfully!")

                    # Display results in tutorial format
                    st.markdown("### 📊 Geocoding Results")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Latitude", f"{result.latitude:.6f}")
                        st.metric("Longitude", f"{result.longitude:.6f}")

                    with col2:
                        st.metric("Quality", result.quality.value)
                        st.metric("Confidence Score", f"{result.confidence_score:.2f}")

                    # Additional info
                    with st.expander("🔍 Detailed Results"):
                        st.markdown(f"""
                        **Provider Used**: {result.provider_used.value}
                        **Formatted Address**: {result.formatted_address if result.formatted_address else 'N/A'}
                        **Processing Time**: {result.processing_time_ms:.0f}ms
                        """)

                        # Show on map if available
                        if result.latitude and result.longitude:
                            map_data = pd.DataFrame({
                                'lat': [result.latitude],
                                'lon': [result.longitude]
                            })
                            st.map(map_data, zoom=15)
                else:
                    st.error(f"❌ Geocoding failed: {result.error_message}")

                    # Educational error guidance
                    if "rate limit" in result.error_message.lower():
                        st.info("💡 **Rate Limit Hit**: Try using a different provider or wait a moment before retrying.")
                    elif "not found" in result.error_message.lower():
                        st.info("💡 **Address Not Found**: Try a more complete address or check for typos.")

            except Exception as e:
                st.error(f"💥 Error: {e!s}")
                st.info("💡 Check your internet connection and try again.")


def render_quality_levels():
    """Step 3: Understanding Quality Levels."""
    st.subheader("📊 Understanding Quality Levels")

    st.markdown("""
    Different addresses return different quality levels. Let's test some examples to understand
    how geocoding quality varies with address specificity.
    """)

    # Test cases from tutorial
    test_addresses = [
        {
            "address": "1600 Pennsylvania Avenue NW, Washington, DC 20500",
            "expected": "High quality - exact street address",
            "icon": "🏢"
        },
        {
            "address": "Washington, DC",
            "expected": "Medium quality - city level",
            "icon": "🏙️"
        },
        {
            "address": "North Carolina",
            "expected": "Low quality - state level",
            "icon": "🗺️"
        }
    ]

    st.info("🧪 **Experiment**: Click to geocode different address types and see the quality levels.")

    for i, test_case in enumerate(test_addresses):
        with st.expander(f"{test_case['icon']} Test {i+1}: {test_case['address']}", expanded=i==0):
            st.caption(f"Expected: {test_case['expected']}")

            if st.button("Geocode This Address", key=f"quality_test_{i}"):
                with st.spinner("Geocoding..."):
                    try:
                        address_input = AddressInput(address=test_case["address"])
                        config = GeocodingConfig(
                            primary_provider=AddressProvider.NOMINATIM,
                            min_quality_threshold=AddressQuality.APPROXIMATE
                        )

                        result = geocode_address(address_input, config)

                        if result.success:
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("Quality", result.quality.value)
                            with col2:
                                st.metric("Coordinates", f"{result.latitude:.4f}, {result.longitude:.4f}")
                            with col3:
                                quality_emoji = {
                                    "EXACT": "🎯",
                                    "INTERPOLATED": "📏",
                                    "CENTROID": "📍",
                                    "APPROXIMATE": "🌐"
                                }.get(result.quality.value, "❓")
                                st.metric("Quality Level", quality_emoji)

                            # Explanation
                            quality_explanations = {
                                "EXACT": "Rooftop precision - perfect for critical applications",
                                "INTERPOLATED": "Street-level accuracy - suitable for most uses",
                                "CENTROID": "Area center - good for regional analysis",
                                "APPROXIMATE": "Rough location - use with caution"
                            }

                            st.success(f"✅ {quality_explanations.get(result.quality.value, 'Unknown quality')}")
                        else:
                            st.error(f"❌ Failed: {result.error_message}")

                    except Exception as e:
                        st.error(f"Error: {e!s}")

    # Best practices
    st.markdown("### 💡 Quality Best Practices")

    col1, col2 = st.columns(2)

    with col1:
        st.warning("""
        **🎯 When to Require High Quality:**
        - Emergency services
        - Delivery routing
        - Legal/compliance uses
        - Precise demographic analysis
        """)

    with col2:
        st.info("""
        **🌐 When Lower Quality is OK:**
        - Regional market analysis
        - General demographic trends
        - Approximate distance calculations
        - Initial data exploration
        """)


def render_batch_address_section():
    """Step 4: Batch Address Processing."""
    st.subheader("📋 Batch Address Processing")

    st.markdown("""
    Process multiple addresses efficiently. Perfect for analyzing customer lists,
    store locations, or any address dataset.
    """)

    # Option to use sample data or upload
    data_source = st.radio(
        "Choose data source:",
        ["Use tutorial sample addresses", "Upload your own CSV"],
        horizontal=True
    )

    addresses_to_process = []

    if data_source == "Use tutorial sample addresses":
        # Tutorial sample addresses (North Carolina locations)
        sample_addresses = [
            "100 N Tryon St, Charlotte, NC",
            "301 E Hargett St, Raleigh, NC",
            "120 E Main St, Durham, NC",
            "100 N Greene St, Greensboro, NC",
            "100 Coxe Ave, Asheville, NC"
        ]

        st.info("📋 **Tutorial Sample**: 5 North Carolina city addresses")

        # Display sample addresses
        sample_df = pd.DataFrame({
            'address': sample_addresses,
            'city': ['Charlotte', 'Raleigh', 'Durham', 'Greensboro', 'Asheville']
        })
        st.dataframe(sample_df, use_container_width=True)

        addresses_to_process = sample_addresses

    else:  # Upload CSV
        uploaded_file = st.file_uploader(
            "Upload CSV with addresses",
            type="csv",
            help="CSV should have an 'address' column"
        )

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)

                # Look for address column
                address_col = None
                for col in ['address', 'Address', 'ADDRESS', 'street_address']:
                    if col in df.columns:
                        address_col = col
                        break

                if address_col:
                    addresses_to_process = df[address_col].tolist()
                    st.success(f"✅ Loaded {len(addresses_to_process)} addresses")

                    # Preview
                    with st.expander("Address Preview"):
                        st.dataframe(df.head())
                else:
                    st.error("CSV must contain an 'address' column")

            except Exception as e:
                st.error(f"Error reading file: {e!s}")

    # Batch processing configuration
    if addresses_to_process:
        st.markdown("### ⚙️ Batch Processing Configuration")

        col1, col2 = st.columns(2)

        with col1:
            batch_provider = st.selectbox(
                "Primary Provider",
                ["Census Bureau (US only)", "Nominatim (Global)"],
                help="Census is best for US addresses"
            )

            batch_size = st.slider(
                "Batch Size",
                min_value=1,
                max_value=10,
                value=3,
                help="Process this many addresses at once"
            )

        with col2:
            enable_cache = st.checkbox(
                "Enable Caching",
                value=True,
                help="Cache results to avoid re-geocoding"
            )

            delay_seconds = st.slider(
                "Delay Between Batches (seconds)",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                help="Be respectful to free APIs"
            )

        # Process button
        if st.button("🔄 Process Batch", type="primary", key="process_batch"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_placeholder = st.empty()

            try:
                # Create address inputs
                address_inputs = [
                    AddressInput(
                        address=addr,
                        id=f"batch_{i}",
                        source="tutorial_batch"
                    )
                    for i, addr in enumerate(addresses_to_process)
                ]

                # Configure batch processing
                selected_provider = AddressProvider.CENSUS if "Census" in batch_provider else AddressProvider.NOMINATIM

                config = GeocodingConfig(
                    primary_provider=selected_provider,
                    fallback_providers=[AddressProvider.NOMINATIM] if selected_provider == AddressProvider.CENSUS else [AddressProvider.CENSUS],
                    min_quality_threshold=AddressQuality.APPROXIMATE,
                    enable_cache=enable_cache,
                    batch_size=batch_size,
                    batch_delay_seconds=delay_seconds
                )

                # Process addresses
                status_text.text("🔄 Batch geocoding in progress...")

                # Simulate progress for demo (in real implementation, use actual progress)
                results = []
                for i, addr_input in enumerate(address_inputs):
                    progress_bar.progress((i + 1) / len(address_inputs))
                    status_text.text(f"Processing address {i+1} of {len(address_inputs)}...")

                    # Geocode individual address
                    result = geocode_address(addr_input, config)
                    results.append(result)

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

                # Analyze results
                successful = [r for r in results if r.success]
                failed = [r for r in results if not r.success]

                # Display summary
                with results_placeholder.container():
                    st.success("✅ Batch processing complete!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Processed", len(results))
                    with col2:
                        st.metric("Successful", f"{len(successful)} ({len(successful)/len(results)*100:.1f}%)")
                    with col3:
                        st.metric("Failed", len(failed))

                    # Show results table
                    if successful:
                        st.markdown("### 📍 Geocoding Results")

                        # Create results dataframe
                        results_data = [
                            {
                                'Address': result.input_address.address,
                                'Latitude': f"{result.latitude:.6f}",
                                'Longitude': f"{result.longitude:.6f}",
                                'Quality': result.quality.value,
                                'Provider': result.provider_used.value
                            }
                            for result in successful
                        ]

                        results_df = pd.DataFrame(results_data)
                        st.dataframe(results_df, use_container_width=True)

                        # Download button
                        csv = results_df.to_csv(index=False)
                        st.download_button(
                            label="💾 Download Geocoded Results",
                            data=csv,
                            file_name="geocoded_addresses.csv",
                            mime="text/csv"
                        )

                        # Store results in session state for integration
                        st.session_state.geocoded_results = successful

                    # Show failures if any
                    if failed:
                        with st.expander(f"⚠️ Failed Geocodes ({len(failed)})"):
                            for result in failed:
                                st.error(f"{result.input_address.address}: {result.error_message}")

            except Exception as e:
                st.error(f"💥 Batch processing error: {e!s}")
                logger.error(f"Batch processing error: {e}")

    # Template download
    with st.expander("📋 Download Address Template"):
        st.markdown("""
        Use this template to prepare your address data for batch geocoding.
        The CSV should have at least an 'address' column.
        """)

        template_df = pd.DataFrame({
            'address': [
                '123 Main St, Durham, NC 27701',
                '456 Oak Ave, Chapel Hill, NC 27514',
                '789 Pine Rd, Raleigh, NC 27603'
            ],
            'name': ['Downtown Office', 'Chapel Hill Branch', 'Raleigh Location'],
            'category': ['Office', 'Retail', 'Warehouse']
        })

        st.dataframe(template_df, use_container_width=True)

        csv = template_df.to_csv(index=False)
        st.download_button(
            label="💾 Download Address Template",
            data=csv,
            file_name="address_template.csv",
            mime="text/csv"
        )


def render_integration_section():
    """Step 5: SocialMapper Integration."""
    st.subheader("🗺️ SocialMapper Integration")

    st.markdown("""
    Convert geocoded addresses into SocialMapper analysis. This shows how to use
    your geocoded address data for demographic and accessibility analysis.
    """)

    # Check for geocoded results in session state
    if 'geocoded_results' in st.session_state and st.session_state.geocoded_results:
        st.success(f"✅ Found {len(st.session_state.geocoded_results)} geocoded addresses ready for analysis")

        # Show preview of geocoded data
        with st.expander("View Geocoded Addresses"):
            preview_data = [
                {
                    'Address': r.input_address.address,
                    'Lat': f"{r.latitude:.4f}",
                    'Lon': f"{r.longitude:.4f}",
                    'Quality': r.quality.value
                }
                for r in st.session_state.geocoded_results[:5]  # Show first 5
            ]
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
    else:
        st.info("💡 First geocode some addresses in the previous tabs, then return here for integration.")

        # Demo mode
        if st.button("Use Demo Addresses", key="use_demo_integration"):
            # Create demo geocoded results
            demo_results = [
                {
                    'name': 'Charlotte Location',
                    'latitude': 35.2271,
                    'longitude': -80.8431,
                    'address': '100 N Tryon St, Charlotte, NC'
                },
                {
                    'name': 'Raleigh Location',
                    'latitude': 35.7796,
                    'longitude': -78.6382,
                    'address': '301 E Hargett St, Raleigh, NC'
                },
                {
                    'name': 'Durham Location',
                    'latitude': 35.9940,
                    'longitude': -78.8986,
                    'address': '120 E Main St, Durham, NC'
                }
            ]
            st.session_state.demo_geocoded_results = demo_results
            st.rerun()

    # Integration options
    st.markdown("### 🎯 Analysis Options")

    col1, col2 = st.columns(2)

    with col1:
        travel_time = st.slider(
            "Travel Time (minutes)",
            min_value=5,
            max_value=30,
            value=15,
            help="Analyze area within this travel time"
        )

        travel_mode = st.selectbox(
            "Travel Mode",
            ["drive", "walk", "bike"],
            help="How people travel from the addresses"
        )

    with col2:
        census_vars = st.multiselect(
            "Census Variables",
            ["total_population", "median_household_income", "median_age"],
            default=["total_population", "median_household_income"],
            help="Demographic variables to analyze"
        )

        export_maps = st.checkbox(
            "Generate Maps",
            value=False,
            help="Create visual maps (takes longer)"
        )

    # Run analysis button
    if st.button("🚀 Run SocialMapper Analysis", type="primary", key="run_integration"):
        geocoded_data = st.session_state.get('geocoded_results') or st.session_state.get('demo_geocoded_results', [])

        if geocoded_data:
            with st.spinner("🗺️ Running demographic analysis..."):
                try:
                    # Save geocoded data to temporary CSV
                    output_dir = Path("output/tutorial_geocoding")
                    output_dir.mkdir(parents=True, exist_ok=True)

                    csv_path = output_dir / "geocoded_addresses.csv"

                    # Convert to DataFrame
                    if isinstance(geocoded_data[0], dict):
                        df = pd.DataFrame(geocoded_data)
                    else:
                        # Convert geocoding results to dataframe
                        data = []
                        for result in geocoded_data:
                            if result.success:
                                data.append({
                                    'name': result.input_address.address.split(',')[0],
                                    'latitude': result.latitude,
                                    'longitude': result.longitude,
                                    'address': result.input_address.address
                                })
                        df = pd.DataFrame(data)

                    df.to_csv(csv_path, index=False)

                    # Use with SocialMapper
                    with SocialMapperClient() as client:
                        config = (SocialMapperBuilder()
                            .with_custom_pois(str(csv_path))
                            .with_travel_time(travel_time)
                            .with_travel_mode(travel_mode)
                            .with_census_variables(*census_vars)
                            .with_exports(csv=True, maps=export_maps)
                            .with_output_directory(str(output_dir))
                            .build()
                        )

                        result = client.run_analysis(config)

                        if result.is_ok():
                            analysis = result.unwrap()

                            st.success("✅ SocialMapper Analysis Complete!")

                            # Display results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Locations Analyzed", analysis.poi_count)
                            with col2:
                                st.metric("Census Areas", analysis.census_units_analyzed)
                            with col3:
                                st.metric("Travel Time", f"{travel_time} min")

                            # Files generated
                            if analysis.files_generated:
                                st.markdown("### 📁 Generated Files")
                                st.info(f"Results saved to: {output_dir}")

                                # List files
                                for file_type, file_path in analysis.files_generated.items():
                                    st.text(f"• {file_type}: {Path(file_path).name}")
                        else:
                            error = result.unwrap_err()
                            st.error(f"❌ Analysis failed: {error.message}")

                except Exception as e:
                    st.error(f"💥 Integration error: {e!s}")
                    logger.error(f"Integration error: {e}")

    # Best practices
    st.markdown("### 💡 Integration Best Practices")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **📋 Address Preparation:**
        • Include name/ID for each location
        • Verify geocoding quality first
        • Remove failed geocodes
        • Consider grouping by category
        """)

    with col2:
        st.warning("""
        **🎯 Analysis Tips:**
        • Start with shorter travel times
        • Use drive mode for regional analysis
        • Walk mode for local accessibility
        • Limit locations for faster processing
        """)

    # Error handling examples
    with st.expander("⚠️ Common Issues & Solutions"):
        st.markdown("""
        **Empty Address Error**
        - Solution: Filter out empty rows before geocoding

        **Low Quality Geocodes**
        - Solution: Set minimum quality threshold
        - Consider manual review for critical addresses

        **Rate Limiting**
        - Solution: Add delays between requests
        - Use caching to avoid re-geocoding
        - Consider batch processing

        **Provider Failures**
        - Solution: Configure fallback providers
        - Try different primary provider for your region
        """)
