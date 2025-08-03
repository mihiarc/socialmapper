"""Tests for export data preparation."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from socialmapper.export.base import DataPrepConfig
from socialmapper.export.preparation import (
    add_travel_columns,
    deduplicate_records,
    extract_geoid_components,
    prepare_census_data,
    process_fips_codes,
    reorder_columns,
)


class TestExtractGeoidComponents:
    """Test GEOID component extraction."""

    def test_valid_geoid_extraction(self):
        """Test extraction from valid GEOID."""
        df = pd.DataFrame({
            'GEOID': ['120010001001', '120010001002', '120010002001']
        })

        result = extract_geoid_components(df)

        assert 'tract' in result.columns
        assert 'block_group' in result.columns
        assert list(result['tract']) == ['000100', '000100', '000200']
        assert list(result['block_group']) == ['1', '2', '1']

    def test_missing_geoid_column(self):
        """Test with missing GEOID column."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        result = extract_geoid_components(df)

        # Should return unchanged
        assert 'tract' not in result.columns
        assert 'block_group' not in result.columns
        pd.testing.assert_frame_equal(result, df)

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame({'GEOID': []})
        result = extract_geoid_components(df)

        # Should handle empty DataFrame
        assert result.empty

    def test_short_geoid(self):
        """Test with GEOID too short for extraction."""
        df = pd.DataFrame({'GEOID': ['12001']})  # Too short
        result = extract_geoid_components(df)

        # Should not add columns
        assert 'tract' not in result.columns
        assert 'block_group' not in result.columns

    def test_numeric_geoid(self):
        """Test with numeric GEOID values."""
        df = pd.DataFrame({'GEOID': [120010001001, 120010001002]})
        result = extract_geoid_components(df)

        # Should convert to string and extract
        assert 'tract' in result.columns
        assert result['GEOID'].dtype == 'object'  # String type


class TestProcessFipsCodes:
    """Test FIPS code processing."""

    def test_state_fips_processing(self):
        """Test state FIPS code processing."""
        df = pd.DataFrame({
            'STATE': ['1', '12', '123']
        })

        result = process_fips_codes(df)

        assert 'state_fips' in result.columns
        assert list(result['state_fips']) == ['01', '12', '123']

    def test_county_fips_processing(self):
        """Test county FIPS code processing."""
        df = pd.DataFrame({
            'STATE': ['12', '6'],
            'COUNTY': ['1', '59']
        })

        result = process_fips_codes(df)

        assert 'county_fips' in result.columns
        assert list(result['county_fips']) == ['12001', '06059']

    def test_numeric_fips_codes(self):
        """Test with numeric FIPS codes."""
        df = pd.DataFrame({
            'STATE': [12, 6],
            'COUNTY': [1, 59]
        })

        result = process_fips_codes(df)

        assert 'state_fips' in result.columns
        assert 'county_fips' in result.columns
        assert result['state_fips'].dtype == 'object'

    def test_missing_columns(self):
        """Test with missing STATE/COUNTY columns."""
        df = pd.DataFrame({'other': [1, 2]})
        result = process_fips_codes(df)

        assert 'state_fips' not in result.columns
        assert 'county_fips' not in result.columns

    def test_null_values(self):
        """Test with null values."""
        df = pd.DataFrame({
            'STATE': [None, '12', ''],
            'COUNTY': ['1', None, '3']
        })

        result = process_fips_codes(df)
        # Should handle nulls gracefully
        assert 'state_fips' in result.columns
        assert 'county_fips' in result.columns


class TestAddTravelColumns:
    """Test travel column addition."""

    def test_add_poi_info_from_list(self):
        """Test adding POI info from list."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        poi_data = [{
            'name': 'Test Library',
            'type': 'library',
            'lat': 37.7749,
            'lon': -122.4194
        }]

        result = add_travel_columns(df, poi_data)

        assert result['poi_name'].iloc[0] == 'Test Library'
        assert result['poi_type'].iloc[0] == 'library'
        assert result['poi_lat'].iloc[0] == 37.7749
        assert result['poi_lon'].iloc[0] == -122.4194

    def test_add_poi_info_from_dict(self):
        """Test adding POI info from dictionary."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        poi_data = {
            'pois': [{
                'name': 'Test Park',
                'type': 'park',
                'lat': 40.7128,
                'lon': -74.0060
            }]
        }

        result = add_travel_columns(df, poi_data)

        assert result['poi_name'].iloc[0] == 'Test Park'
        assert result['poi_type'].iloc[0] == 'park'

    def test_add_travel_time_and_mode(self):
        """Test adding travel time and mode."""
        df = pd.DataFrame({'id': [1, 2, 3]})

        result = add_travel_columns(
            df,
            poi_data={},
            travel_time_minutes=15,
            travel_mode='walk'
        )

        assert all(result['travel_time_minutes'] == 15)
        assert all(result['travel_mode'] == 'walk')

    def test_empty_poi_data(self):
        """Test with empty POI data."""
        df = pd.DataFrame({'id': [1, 2, 3]})

        result = add_travel_columns(df, poi_data=[])

        # Should not add POI columns
        assert 'poi_name' not in result.columns

    def test_missing_poi_fields(self):
        """Test with POI missing some fields."""
        df = pd.DataFrame({'id': [1, 2]})
        poi_data = [{'name': 'Test'}]  # Missing type, lat, lon

        result = add_travel_columns(df, poi_data)

        assert result['poi_name'].iloc[0] == 'Test'
        assert result['poi_type'].iloc[0] == 'Unknown'
        assert pd.isna(result['poi_lat'].iloc[0])


class TestReorderColumns:
    """Test column reordering."""

    def test_basic_reordering(self):
        """Test basic column reordering."""
        df = pd.DataFrame({
            'col3': [1, 2, 3],
            'col1': [4, 5, 6],
            'col2': [7, 8, 9]
        })

        config = DataPrepConfig(
            preferred_column_order=['col1', 'col2', 'col3']
        )

        result = reorder_columns(df, config)

        assert list(result.columns) == ['col1', 'col2', 'col3']

    def test_missing_preferred_columns(self):
        """Test with some preferred columns missing."""
        df = pd.DataFrame({
            'col2': [1, 2],
            'col4': [3, 4]
        })

        config = DataPrepConfig(
            preferred_column_order=['col1', 'col2', 'col3']
        )

        result = reorder_columns(df, config)

        # Should include existing preferred columns first, then others
        assert list(result.columns) == ['col2', 'col4']

    def test_excluded_columns(self):
        """Test column exclusion."""
        df = pd.DataFrame({
            'keep1': [1, 2],
            'exclude1': [3, 4],
            'keep2': [5, 6],
            'geometry': [None, None]
        })

        config = DataPrepConfig(
            preferred_column_order=['keep1', 'keep2'],
            excluded_columns=['exclude1', 'geometry']
        )

        result = reorder_columns(df, config)

        assert 'exclude1' not in result.columns
        assert 'geometry' not in result.columns
        assert list(result.columns) == ['keep1', 'keep2']


class TestDeduplicateRecords:
    """Test record deduplication."""

    def test_basic_deduplication(self):
        """Test basic deduplication."""
        df = pd.DataFrame({
            'census_block_group': ['BG1', 'BG1', 'BG2'],
            'poi_name': ['Library', 'Library', 'Library'],
            'distance_miles': [1.0, 2.0, 3.0],
            'population': [1000, 1000, 2000]
        })

        config = DataPrepConfig()
        result = deduplicate_records(df, config)

        # Should have 2 rows (BG1 and BG2)
        assert len(result) == 2
        # Should take minimum distance for BG1
        bg1_row = result[result['census_block_group'] == 'BG1']
        assert bg1_row['distance_miles'].iloc[0] == 1.0

    def test_custom_aggregation_rules(self):
        """Test custom aggregation rules."""
        df = pd.DataFrame({
            'group_col': ['A', 'A', 'B'],
            'min_col': [3, 1, 2],
            'max_col': [5, 10, 7],
            'first_col': ['X', 'Y', 'Z']
        })

        config = DataPrepConfig(
            deduplication_columns=['group_col'],
            deduplication_agg_rules={
                'min_col': 'min',
                'max_col': 'max',
                'first_col': 'first'
            }
        )

        result = deduplicate_records(df, config)

        assert len(result) == 2
        a_row = result[result['group_col'] == 'A']
        assert a_row['min_col'].iloc[0] == 1
        assert a_row['max_col'].iloc[0] == 10
        assert a_row['first_col'].iloc[0] == 'X'

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=['col1', 'col2'])
        config = DataPrepConfig()

        result = deduplicate_records(df, config)
        assert result.empty

    def test_no_valid_groupby_columns(self):
        """Test when no valid groupby columns exist."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })

        config = DataPrepConfig(
            deduplication_columns=['nonexistent_col']
        )

        result = deduplicate_records(df, config)
        # Should return original DataFrame
        pd.testing.assert_frame_equal(result, df)


class TestPrepareCensusData:
    """Test complete census data preparation."""

    def test_full_preparation_pipeline(self):
        """Test full data preparation pipeline."""
        # Create sample census data
        census_data = gpd.GeoDataFrame({
            'GEOID': ['120010001001', '120010001002'],
            'STATE': ['12', '12'],
            'COUNTY': ['001', '001'],
            'total_population': [1000, 2000],
            'median_household_income': [50000, 60000],
            'geometry': [Point(0, 0), Point(1, 1)]
        })

        poi_data = [{
            'name': 'Central Library',
            'type': 'library',
            'lat': 0.5,
            'lon': 0.5
        }]

        result = prepare_census_data(
            census_data,
            poi_data,
            travel_time_minutes=15,
            travel_mode='walk'
        )

        # Check all transformations applied
        assert 'census_block_group' in result.columns
        assert 'tract' in result.columns
        assert 'block_group' in result.columns
        assert 'state_fips' in result.columns
        assert 'county_fips' in result.columns
        assert 'poi_name' in result.columns
        assert result['poi_name'].iloc[0] == 'Central Library'
        assert all(result['travel_time_minutes'] == 15)
        assert all(result['travel_mode'] == 'walk')

        # Check geometry excluded (in default config)
        assert 'geometry' not in result.columns

    def test_empty_census_data(self):
        """Test with empty census data."""
        empty_gdf = gpd.GeoDataFrame(columns=['GEOID'])

        result = prepare_census_data(empty_gdf, poi_data={})

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_none_census_data(self):
        """Test with None census data."""
        result = prepare_census_data(None, poi_data={})

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_no_deduplication(self):
        """Test preparation without deduplication."""
        census_data = gpd.GeoDataFrame({
            'GEOID': ['BG1', 'BG1', 'BG2'],
            'value': [1, 2, 3]
        })

        result = prepare_census_data(
            census_data,
            poi_data={},
            deduplicate=False
        )

        # Should keep all 3 rows
        assert len(result) == 3

    def test_custom_config(self):
        """Test with custom configuration."""
        census_data = gpd.GeoDataFrame({
            'GEOID': ['12001'],
            'custom_col': [100],
            'exclude_me': [200]
        })

        custom_config = DataPrepConfig(
            preferred_column_order=['custom_col', 'census_block_group'],
            excluded_columns=['exclude_me']
        )

        result = prepare_census_data(
            census_data,
            poi_data={},
            config=custom_config
        )

        assert 'exclude_me' not in result.columns
        assert list(result.columns)[0] == 'custom_col'
