#!/usr/bin/env python3
"""
Test script to demonstrate the quiet mode functionality.

This script demonstrates how to use the quiet mode to suppress log messages.
"""

import sys
import os
from socialmapper.core import set_quiet_logging

# Set up sys.path to find local package
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test quiet mode in SocialMapper")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode")
    args = parser.parse_args()
    
    # Apply quiet mode if requested
    if args.quiet:
        print("Running in quiet mode - most log messages will be suppressed")
        set_quiet_logging()
    else:
        print("Running in normal mode - all log messages will be shown")
    
    # Import SocialMapper modules after logging is configured
    from socialmapper.census_data.cache import DiskCache
    from socialmapper.census_data import fetch_census_data_for_states
    
    # Create a test cache instance
    cache = DiskCache()
    
    # Fetch some test data (this will produce log messages)
    print("\nFetching test data (this may take a few moments)...\n")
    
    # Try getting data from cache or API
    result = cache.get_or_fetch(
        state_fips_list=["48", "13"],  # Texas and Georgia
        variables=["B01003_001E", "B19013_001E"],  # Population and median income
        year=2021,
        dataset="acs/acs5",
        api_key="b607120490031baad1c96ea61d30c8ba8b2bc246",  # Demo key
        use_async=True
    )
    
    print(f"\nSuccessfully retrieved data for {len(result)} block groups") 