#!/usr/bin/env python3
"""
Test script to verify Census API key loading
"""

import os
from dotenv import load_dotenv

print("Testing Census API key loading...")

# Load .env file
load_dotenv()

# Check environment variable
api_key = os.getenv('CENSUS_API_KEY')
print(f"Environment variable CENSUS_API_KEY: {'✅ Found' if api_key else '❌ Not found'}")
if api_key:
    print(f"Key (first 10 chars): {api_key[:10]}...")

# Test the SocialMapper utility function
try:
    from socialmapper.util import get_census_api_key
    sm_key = get_census_api_key()
    print(f"SocialMapper get_census_api_key(): {'✅ Found' if sm_key else '❌ Not found'}")
    if sm_key:
        print(f"Key (first 10 chars): {sm_key[:10]}...")
        
    if api_key == sm_key:
        print("✅ Both methods return the same key!")
    else:
        print("❌ Keys don't match!")
        
except ImportError as e:
    print(f"❌ Error importing SocialMapper: {e}")

print("\nTest complete!") 