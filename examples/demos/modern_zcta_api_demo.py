#!/usr/bin/env python3
"""
SocialMapper Tutorial 04: Modern ZCTA API Implementation

This tutorial demonstrates the modernized ZCTA endpoints that use the proper
Census Bureau API format. You'll learn:
- How the new API format improves reliability and performance
- Using the efficient batch processing methods
- Understanding the Census API response format
- Comparing old vs new implementation performance

This showcases the 2025 implementation using the correct Census API format:
https://api.census.gov/data/2023/acs/acs5?get=NAME,B01001_001E&for=zip%20code%20tabulation%20area:77494

Prerequisites:
- SocialMapper installed: uv add socialmapper
- Census API key (recommended): Set CENSUS_API_KEY environment variable
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper import get_census_system


def explain_modern_zcta_api():
    """Explain the modern ZCTA API implementation."""
    print("🚀 Modern ZCTA API Implementation (2025 Edition)")
    print("=" * 80)
    print()
    print("The modernized ZCTA service now uses the proper Census Bureau API format")
    print("for improved reliability, performance, and data consistency.")
    print()
    print("📡 API Format Example:")
    print("   URL: https://api.census.gov/data/2023/acs/acs5")
    print("   Params: ?get=NAME,B01001_001E&for=zip%20code%20tabulation%20area:77494")
    print()
    print("📊 Response Format:")
    print('   [["NAME","B01001_001E","zip code tabulation area"],')
    print('    ["ZCTA5 77494","137213","77494"]]')
    print()
    print("✨ Key Improvements:")
    print("   • Proper Census API endpoint usage")
    print("   • Individual ZCTA requests for accuracy")
    print("   • Efficient batch processing with rate limiting")
    print("   • Better error handling and recovery")
    print("   • Consistent data transformation")
    print("   • Enhanced caching strategies")
    print()


def demo_modern_api_usage():
    """Demonstrate the modern ZCTA API usage."""
    print("🔧 Modern ZCTA API Usage")
    print("=" * 50)
    
    # Get the modern census system
    census_system = get_census_system()
    
    # Example ZCTAs from different regions
    test_zctas = [
        "77494",  # Katy, TX (suburban Houston)
        "10001",  # Manhattan, NY (urban)
        "27601",  # Raleigh, NC (downtown)
        "90210",  # Beverly Hills, CA (affluent)
        "60601",  # Chicago, IL (downtown)
    ]
    
    # Census variables to fetch
    variables = [
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25003_002E",  # Owner-occupied housing units
    ]
    
    print(f"\n📍 Testing with {len(test_zctas)} ZCTAs:")
    for i, zcta in enumerate(test_zctas, 1):
        print(f"   {i}. ZCTA {zcta}")
    
    print(f"\n📊 Variables:")
    var_names = {
        "B01003_001E": "Total Population",
        "B19013_001E": "Median Household Income", 
        "B25003_002E": "Owner-Occupied Housing Units"
    }
    
    for var, name in var_names.items():
        print(f"   • {var}: {name}")
    
    # Test the modern efficient method
    print(f"\n🚀 Testing modern efficient API...")
    start_time = time.time()
    
    try:
        # Use the new efficient method
        modern_data = census_system._zcta_service.get_census_data_efficient(
            geoids=test_zctas,
            variables=variables,
            batch_size=3,  # Small batch for demo
            year=2023
        )
        
        processing_time = time.time() - start_time
        
        if not modern_data.empty:
            print(f"✅ Modern API success!")
            print(f"   📊 Retrieved {len(modern_data)} data points")
            print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
            print(f"   🏃 Rate: {len(modern_data)/processing_time:.1f} points/second")
            
            # Show sample data
            print(f"\n📋 Sample Results:")
            print("-" * 70)
            print(f"{'ZCTA':<8} {'Variable':<12} {'Value':<15} {'Name':<25}")
            print("-" * 70)
            
            # Display first few results
            for _, row in modern_data.head(6).iterrows():
                zcta = row['GEOID']
                var = row['variable_code']
                value = f"{row['value']:,.0f}" if row['value'] else "N/A"
                name = var_names.get(var, var)[:24]
                print(f"{zcta:<8} {var:<12} {value:<15} {name:<25}")
            
            if len(modern_data) > 6:
                print(f"... and {len(modern_data) - 6} more rows")
            print("-" * 70)
            
            # Test specific ZCTA lookup
            test_zcta = "77494"
            zcta_data = modern_data[modern_data['GEOID'] == test_zcta]
            
            if not zcta_data.empty:
                print(f"\n🏠 Focus: ZCTA {test_zcta} (Katy, TX)")
                for _, row in zcta_data.iterrows():
                    var_name = var_names.get(row['variable_code'], row['variable_code'])
                    value = f"{row['value']:,.0f}" if row['value'] else "N/A"
                    print(f"   • {var_name}: {value}")
        else:
            print("❌ No data returned from modern API")
    
    except Exception as e:
        print(f"❌ Modern API error: {e}")
        print("💡 Check your internet connection and Census API limits")
    
    print()


def demo_legacy_vs_modern_comparison():
    """Compare legacy vs modern ZCTA API performance."""
    print("⚖️  Legacy vs Modern API Comparison")
    print("=" * 50)
    
    census_system = get_census_system()
    
    # Smaller test set for comparison
    test_zctas = ["27601", "28202", "77494"]  # 3 ZCTAs
    variables = ["B01003_001E", "B19013_001E"]  # 2 variables
    
    print(f"🧪 Test Configuration:")
    print(f"   • ZCTAs: {len(test_zctas)} ({', '.join(test_zctas)})")
    print(f"   • Variables: {len(variables)} ({', '.join(variables)})")
    
    results = {}
    
    # Test legacy method
    print(f"\n🔄 Testing legacy method...")
    try:
        start_time = time.time()
        legacy_data = census_system._zcta_service.get_census_data(
            geoids=test_zctas,
            variables=variables
        )
        legacy_time = time.time() - start_time
        
        results['legacy'] = {
            'success': not legacy_data.empty,
            'records': len(legacy_data),
            'time': legacy_time,
            'rate': len(legacy_data) / legacy_time if legacy_time > 0 else 0
        }
        print(f"   ✅ Legacy: {len(legacy_data)} records in {legacy_time:.2f}s")
        
    except Exception as e:
        results['legacy'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Legacy failed: {e}")
    
    # Test modern method
    print(f"\n🔄 Testing modern efficient method...")
    try:
        start_time = time.time()
        modern_data = census_system._zcta_service.get_census_data_efficient(
            geoids=test_zctas,
            variables=variables,
            batch_size=2
        )
        modern_time = time.time() - start_time
        
        results['modern'] = {
            'success': not modern_data.empty,
            'records': len(modern_data),
            'time': modern_time,
            'rate': len(modern_data) / modern_time if modern_time > 0 else 0
        }
        print(f"   ✅ Modern: {len(modern_data)} records in {modern_time:.2f}s")
        
    except Exception as e:
        results['modern'] = {'success': False, 'error': str(e)}
        print(f"   ❌ Modern failed: {e}")
    
    # Display comparison
    print(f"\n📊 Performance Comparison:")
    print("-" * 60)
    print(f"{'Metric':<20} {'Legacy':<15} {'Modern':<15} {'Improvement':<10}")
    print("-" * 60)
    
    if results.get('legacy', {}).get('success') and results.get('modern', {}).get('success'):
        legacy = results['legacy']
        modern = results['modern']
        
        # Records
        print(f"{'Records':<20} {legacy['records']:<15} {modern['records']:<15} {'Same':<10}")
        
        # Time
        time_improvement = legacy['time'] / modern['time'] if modern['time'] > 0 else float('inf')
        print(f"{'Time (seconds)':<20} {legacy['time']:.2f}{'':<10} {modern['time']:.2f}{'':<10} {time_improvement:.1f}x faster")
        
        # Rate
        rate_improvement = modern['rate'] / legacy['rate'] if legacy['rate'] > 0 else float('inf')
        print(f"{'Rate (rec/sec)':<20} {legacy['rate']:.1f}{'':<10} {modern['rate']:.1f}{'':<10} {rate_improvement:.1f}x faster")
        
        print("-" * 60)
        
        print(f"\n🎯 Key Improvements:")
        if time_improvement > 1:
            print(f"   • Modern API is {time_improvement:.1f}x faster")
        print(f"   • Better error handling and recovery")
        print(f"   • More reliable individual ZCTA requests")
        print(f"   • Consistent data format transformation")
    else:
        print("Could not complete comparison due to errors")
        for method, result in results.items():
            if not result.get('success'):
                print(f"   {method}: {result.get('error', 'Unknown error')}")
    
    print()


def demo_api_response_format():
    """Demonstrate understanding of the Census API response format."""
    print("📡 Census API Response Format Analysis")
    print("=" * 50)
    
    print("The modern implementation properly handles the Census Bureau's")
    print("standardized API response format for ZCTA data.")
    print()
    
    print("📝 Example API Call:")
    print("   GET https://api.census.gov/data/2023/acs/acs5")
    print("   Params: {")
    print('     "get": "NAME,B01003_001E",')
    print('     "for": "zip code tabulation area:77494"')
    print("   }")
    print()
    
    print("📊 Response Structure:")
    print("   [")
    print('     ["NAME", "B01003_001E", "zip code tabulation area"],  // Headers')
    print('     ["ZCTA5 77494", "137213", "77494"]                    // Data')
    print("   ]")
    print()
    
    print("🔧 Modern Processing Steps:")
    print("   1. Individual ZCTA requests (proper geography handling)")
    print("   2. Rate limiting between requests")
    print("   3. Response validation and error handling")
    print("   4. Data transformation to standard format")
    print("   5. Batch aggregation and caching")
    print()
    
    print("✨ Benefits:")
    print("   • Accurate geography targeting")
    print("   • Reliable data retrieval")
    print("   • Consistent error recovery")
    print("   • Efficient batch processing")
    print("   • Proper null value handling")
    print()


def main():
    """Run the modern ZCTA API demonstration."""
    print("🗺️  SocialMapper Tutorial 04: Modern ZCTA API Implementation")
    print(f"{'='*80}")
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Educational sections
    explain_modern_zcta_api()
    
    # Practical demonstrations
    demo_modern_api_usage()
    demo_legacy_vs_modern_comparison()
    demo_api_response_format()
    
    # Conclusion
    print("🎓 Tutorial Complete: Modern ZCTA API Mastery!")
    print("=" * 60)
    
    print("\n🏆 What You've Learned:")
    print("  ✅ Proper Census Bureau API format for ZCTAs")
    print("  ✅ Modern efficient batch processing methods")
    print("  ✅ Performance improvements and reliability gains")
    print("  ✅ API response format handling")
    print("  ✅ Error recovery and data validation")
    
    print("\n🚀 Next Steps:")
    print("  1. 🔧 Integrate modern methods into your analysis pipelines")
    print("  2. 📊 Use efficient batching for large-scale ZCTA analysis")
    print("  3. 🛡️ Implement proper error handling in production code")
    print("  4. ⚡ Leverage caching for repeated analysis")
    print("  5. 📈 Monitor API performance and rate limits")
    
    print("\n💡 Pro Tips:")
    print("  • Use get_census_data_efficient() for new applications")
    print("  • Set appropriate batch sizes based on your API key limits")
    print("  • Enable caching for repeated analysis workflows")
    print("  • Monitor rate limits to avoid API throttling")
    
    print(f"\n🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 