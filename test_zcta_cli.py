#!/usr/bin/env python3
"""
Quick CLI Test Script for ZCTA Feature

This script tests the ZCTA feature using various CLI commands
to ensure everything is working properly.
"""

import subprocess
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def run_command(cmd: str, description: str, timeout: int = 300):
    """Run a CLI command and report results."""
    console.print(f"\n🧪 Testing: {description}")
    console.print(f"Command: {cmd}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            console.print(f"✅ SUCCESS ({elapsed:.1f}s)")
            if result.stdout:
                console.print("Output preview:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            console.print(f"❌ FAILED ({elapsed:.1f}s)")
            console.print(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        console.print(f"⏰ TIMEOUT (>{timeout}s)")
    except Exception as e:
        console.print(f"💥 ERROR: {e}")

def create_test_data():
    """Create minimal test data."""
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Simple CSV with 2 points
    csv_content = """name,lat,lon,type
Seattle Central Library,47.6062,-122.3321,library
University Library,47.6613,-122.3138,library"""
    
    csv_file = test_dir / "test_coords.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    # Simple address file
    addresses = """address
1000 4th Ave, Seattle, WA
5009 Roosevelt Way NE, Seattle, WA"""
    
    addr_file = test_dir / "test_addresses.csv"  
    with open(addr_file, 'w') as f:
        f.write(addresses)
    
    console.print(f"✅ Created test data in {test_dir}/")
    return csv_file, addr_file

def main():
    """Run ZCTA CLI tests."""
    
    console.print(Panel.fit(
        "🧪 ZCTA Feature CLI Tests\n\n"
        "This script runs quick tests of the ZCTA CLI functionality\n"
        "using minimal test data to verify everything works.",
        title="CLI Test Suite",
        border_style="bold blue"
    ))
    
    # Create test data
    console.print("\n📋 Creating test data...")
    csv_file, addr_file = create_test_data()
    
    # Test scenarios
    tests = [
        {
            "cmd": f"python -m socialmapper.cli --custom-coords {csv_file} --travel-time 10 --geographic-level block-group --export-csv --no-export-maps",
            "desc": "Block Groups (baseline)",
            "timeout": 180
        },
        {
            "cmd": f"python -m socialmapper.cli --custom-coords {csv_file} --travel-time 10 --geographic-level zcta --export-csv --no-export-maps", 
            "desc": "ZCTAs (new feature)",
            "timeout": 180
        },
        {
            "cmd": "python -m socialmapper.cli --poi --geocode-area 'Seattle' --state 'WA' --poi-type 'amenity' --poi-name 'library' --geographic-level zcta --travel-time 10 --export-csv --no-export-maps",
            "desc": "POI search with ZCTAs",
            "timeout": 240
        },
        {
            "cmd": f"python -m socialmapper.cli --addresses --address-file {addr_file} --geographic-level zcta --travel-time 10 --export-csv --no-export-maps",
            "desc": "Address geocoding with ZCTAs", 
            "timeout": 240
        }
    ]
    
    # Run tests
    console.print(f"\n🚀 Running {len(tests)} CLI tests...")
    
    passed = 0
    for i, test in enumerate(tests, 1):
        console.print(f"\n{'='*60}")
        console.print(f"Test {i}/{len(tests)}: {test['desc']}")
        console.print("="*60)
        
        try:
            run_command(test["cmd"], test["desc"], test["timeout"])
            passed += 1
        except KeyboardInterrupt:
            console.print("\n⏹️ Tests interrupted by user")
            break
        except Exception as e:
            console.print(f"💥 Test failed with error: {e}")
    
    # Summary
    console.print(f"\n{'='*60}")
    console.print("📊 TEST SUMMARY")
    console.print("="*60)
    console.print(f"✅ Passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        console.print("\n🎉 All tests passed! ZCTA feature is working correctly.")
    else:
        console.print(f"\n⚠️ {len(tests) - passed} test(s) failed. Check the output above.")
    
    console.print("\n📁 Check the 'output/' directory for generated files")
    console.print("💡 Tip: Run the full demo with 'python demo_zcta_feature.py'")

if __name__ == "__main__":
    main() 