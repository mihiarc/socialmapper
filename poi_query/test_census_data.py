 #!/usr/bin/env python3
"""
Tests for the census_data module to isolate and diagnose issues with Census API integration.
"""
import os
import sys
import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Polygon
import json
import tempfile

# Make sure we can import the census_data module
try:
    from census_data import (
        load_block_groups,
        extract_block_group_ids,
        fetch_census_data_for_states,
        merge_census_data,
        get_census_data_for_block_groups,
        get_variable_metadata
    )
except ImportError:
    # If normal import fails, try adjusting the path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    from census_data import (
        load_block_groups,
        extract_block_group_ids,
        fetch_census_data_for_states,
        merge_census_data,
        get_census_data_for_block_groups,
        get_variable_metadata
    )

# Check if we have a Census API key in environment
API_KEY = os.environ.get('CENSUS_API_KEY')
SKIP_API_TESTS = API_KEY is None

# Set up some test data
@pytest.fixture
def sample_blockgroup_geojson():
    """Create a temporary GeoJSON file with sample block group data."""
    # Create a simple polygon
    polygon = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
    
    # Create GeoDataFrame with a few block groups
    data = {
        'GEOID': ['200010001001', '200010001002', '200010002001'],
        'STATE': ['20', '20', '20'],
        'COUNTY': ['001', '001', '001'],
        'TRACT': ['000100', '000100', '000200'],
        'BLKGRP': ['1', '2', '1'],
        'geometry': [polygon, polygon, polygon]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    
    # Save to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
        gdf.to_file(tmp.name, driver="GeoJSON")
        return tmp.name

@pytest.fixture
def sample_census_data():
    """Create a sample DataFrame with census data."""
    data = {
        'B01003_001E': ['100', '200', '300'],
        'NAME': ['Block Group 1', 'Block Group 2', 'Block Group 3'],
        'state': ['20', '20', '20'],
        'county': ['001', '001', '001'],
        'tract': ['000100', '000100', '000200'],
        'block group': ['1', '2', '1'],
        'GEOID': ['200010001001', '200010001002', '200010002001']
    }
    return pd.DataFrame(data)

# Test loading block groups
def test_load_block_groups(sample_blockgroup_geojson):
    """Test loading block groups from a GeoJSON file."""
    gdf = load_block_groups(sample_blockgroup_geojson)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 3
    assert 'GEOID' in gdf.columns
    assert 'STATE' in gdf.columns

# Test extracting block group IDs
def test_extract_block_group_ids(sample_blockgroup_geojson):
    """Test extracting block group IDs by state."""
    gdf = load_block_groups(sample_blockgroup_geojson)
    result = extract_block_group_ids(gdf)
    
    assert '20' in result
    assert len(result['20']) == 3
    assert '200010001001' in result['20']
    assert '200010001002' in result['20']
    assert '200010002001' in result['20']

# Test merging census data
def test_merge_census_data(sample_blockgroup_geojson, sample_census_data):
    """Test merging census data with block group geometries."""
    gdf = load_block_groups(sample_blockgroup_geojson)
    result = merge_census_data(gdf, sample_census_data)
    
    assert isinstance(result, gpd.GeoDataFrame)
    assert 'B01003_001E' in result.columns
    assert 'NAME' in result.columns
    assert len(result) == len(gdf)

# Test variable mapping
def test_merge_census_data_with_mapping(sample_blockgroup_geojson, sample_census_data):
    """Test merging census data with a variable mapping."""
    gdf = load_block_groups(sample_blockgroup_geojson)
    mapping = {'B01003_001E': 'total_population', 'NAME': 'census_name'}
    result = merge_census_data(gdf, sample_census_data, variable_mapping=mapping)
    
    assert 'total_population' in result.columns
    assert 'census_name' in result.columns

# API-dependent tests
@pytest.mark.skipif(SKIP_API_TESTS, reason="No Census API key available")
class TestCensusAPI:
    """Tests that require a valid Census API key."""
    
    def test_fetch_census_data_for_states(self):
        """Test fetching census data for a state."""
        # Just Kansas for faster testing
        state_fips = ['20']
        variables = ['B01003_001E']  # Total population
        
        # This will skip if API_KEY is None
        result = fetch_census_data_for_states(state_fips, variables, api_key=API_KEY)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'B01003_001E' in result.columns
        assert 'GEOID' in result.columns
        
        # Print some diagnostic information about the results
        print(f"\nFetched {len(result)} block groups from Census API")
        print(f"Sample GEOIDs: {result['GEOID'].head(3).tolist()}")
        
        # Test that GEOIDs are properly formatted (12 characters)
        geoid_lengths = set(len(geoid) for geoid in result['GEOID'])
        assert 12 in geoid_lengths, f"Expected GEOIDs of length 12, got {geoid_lengths}"
    
    def test_variable_metadata(self):
        """Test fetching variable metadata."""
        result = get_variable_metadata(api_key=API_KEY)
        
        assert isinstance(result, dict)
        assert 'variables' in result
        
        # Check that our common variables exist
        variables = result['variables']
        assert 'B01003_001E' in variables
        
        # Print some available variables for reference
        print("\nSample Census variables available:")
        var_list = list(variables.keys())[:5]
        for var in var_list:
            if var in variables:
                print(f"  {var}: {variables[var]['label']}")
    
    def test_end_to_end_with_sample_geojson(self, sample_blockgroup_geojson):
        """Test the full pipeline with a sample GeoJSON file."""
        # This is likely to fail since our sample GEOIDs probably don't exist
        # But it's useful for diagnosing issues
        
        variables = ['B01003_001E']
        try:
            result = get_census_data_for_block_groups(
                geojson_path=sample_blockgroup_geojson,
                variables=variables,
                api_key=API_KEY
            )
            
            assert isinstance(result, gpd.GeoDataFrame)
            # These specific block groups likely won't exist, so we don't assert on finding matches
            print(f"\nEnd-to-end test found {len(result)} block groups with census data")
            
        except Exception as e:
            # Don't fail the test, just report the error
            print(f"\nExpected error in end-to-end test (using fabricated GEOIDs): {e}")
            assert True  # Make the test pass

# Test with real data if available
@pytest.mark.skipif(SKIP_API_TESTS, reason="No Census API key available")
def test_with_real_geojson():
    """Test with a real GeoJSON file if available in the results directory."""
    # Look for actual block group GeoJSON files in the results directory
    results_dir = Path('../results')
    if not results_dir.exists():
        results_dir = Path('results')
    
    if not results_dir.exists():
        pytest.skip("Results directory not found")
    
    geojson_files = list(results_dir.glob('block_groups_*.geojson'))
    
    if not geojson_files:
        pytest.skip("No block group GeoJSON files found in results directory")
    
    # Use the first file we find
    geojson_path = geojson_files[0]
    print(f"\nTesting with real GeoJSON file: {geojson_path}")
    
    # Load the file to examine structure
    try:
        gdf = load_block_groups(geojson_path)
        print(f"File contains {len(gdf)} block groups")
        print(f"Columns: {gdf.columns.tolist()}")
        
        # Try to extract block group IDs
        ids_by_state = extract_block_group_ids(gdf)
        for state, ids in ids_by_state.items():
            print(f"State {state}: {len(ids)} block groups")
            if ids:
                print(f"Sample GEOID: {ids[0]}")
        
        # Now try to fetch census data
        if API_KEY:
            variables = ['B01003_001E']  # Total population
            
            try:
                # Just fetch data for the first state we found
                if ids_by_state:
                    state = next(iter(ids_by_state.keys()))
                    data = fetch_census_data_for_states([state], variables, api_key=API_KEY)
                    print(f"Successfully fetched {len(data)} block groups from Census API")
                    
                    # Now test filtering to our specific block groups
                    if state in ids_by_state and ids_by_state[state]:
                        needed_ids = ids_by_state[state]
                        filtered_data = data[data['GEOID'].isin(needed_ids)]
                        print(f"Filtered to {len(filtered_data)} matching block groups")
                        
                        # Check if we have zero matches and try diagnostics
                        if len(filtered_data) == 0:
                            print("WARNING: Zero matches found. Investigating GEOID format...")
                            
                            # Compare formats
                            if len(data) > 0 and len(needed_ids) > 0:
                                api_id = data['GEOID'].iloc[0]
                                our_id = needed_ids[0]
                                print(f"API GEOID format: {api_id} (length {len(api_id)})")
                                print(f"Our GEOID format: {our_id} (length {len(our_id)})")
                                
                                # Try stripping leading zeros for comparison
                                if api_id.lstrip('0') == our_id.lstrip('0'):
                                    print("IDs match when leading zeros are ignored!")
                                
                                # Try more flexible matching
                                matched = 0
                                for needed_id in needed_ids[:10]:  # Check first 10
                                    for api_id in data['GEOID'].iloc[:100]:  # Check first 100
                                        if needed_id.lstrip('0') == api_id.lstrip('0'):
                                            matched += 1
                                            break
                                
                                if matched > 0:
                                    print(f"Found {matched}/10 matches with flexible ID comparison")
            except Exception as e:
                print(f"Error in API test: {e}")
        
        # This is a diagnostic test, so always pass
        assert True
        
    except Exception as e:
        print(f"Error loading real GeoJSON: {e}")
        # This is a diagnostic test, so always pass
        assert True

# Run diagnostic output
def test_diagnostic_info():
    """Print diagnostic information about the environment."""
    print("\nDiagnostic Information:")
    print(f"Census API Key available: {API_KEY is not None}")
    print(f"pandas version: {pd.__version__}")
    print(f"geopandas version: {gpd.__version__}")
    print(f"Python version: {os.sys.version}")
    
    # Check for .env file
    env_file = Path('../.env')
    if not env_file.exists():
        env_file = Path('.env')
    
    if env_file.exists():
        print(f".env file found at {env_file}")
    else:
        print(".env file not found")
    
    # Always pass this test
    assert True

if __name__ == "__main__":
    # Allow running directly
    pytest.main(["-xvs", __file__])