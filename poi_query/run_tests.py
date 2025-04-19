#!/usr/bin/env python3
"""
Script to run the census_data.py tests and help with troubleshooting.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

def check_api_key():
    """Check if a Census API key is available in the environment."""
    # Try to load from .env file
    load_dotenv()
    
    # Check for the key
    api_key = os.environ.get('CENSUS_API_KEY')
    if not api_key:
        print("⚠️ Census API Key not found!")
        print("Please set the CENSUS_API_KEY environment variable or add it to a .env file.")
        print("You can get a Census API key at: https://api.census.gov/data/key_signup.html")
        return False
    else:
        print(f"✅ Census API Key found: {api_key[:4]}...{api_key[-4:]}")
        return True

def check_pytest():
    """Check if pytest is installed."""
    try:
        subprocess.run(["pytest", "--version"], capture_output=True, check=True)
        print("✅ pytest is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ pytest not installed")
        return False

def install_pytest():
    """Install pytest if needed."""
    try:
        print("Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
        print("✅ pytest installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install pytest: {e}")
        return False

def run_tests(verbose=False, real_data=False):
    """Run the tests for census_data.py."""
    current_dir = Path(__file__).parent
    test_file = current_dir / "test_census_data.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Running tests from {test_file}...")
    
    # Build command
    cmd = ["pytest", "-xvs", str(test_file)]
    
    # Select specific tests if requested
    if not real_data:
        # Skip the real data test by default
        cmd.append("-k")
        cmd.append("not test_with_real_geojson")
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. See output for details.")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def display_troubleshooting_guide():
    """Display a troubleshooting guide for common issues."""
    print("\n" + "="*80)
    print("TROUBLESHOOTING GUIDE")
    print("="*80)
    
    print("\nCommon Issues:")
    
    print("\n1. Census API Key Issues")
    print("   - Make sure you have a valid Census API key")
    print("   - Add it to a .env file as CENSUS_API_KEY=your_key_here")
    print("   - Or set it as an environment variable: export CENSUS_API_KEY=your_key_here")
    
    print("\n2. GEOID Format Mismatches")
    print("   - The tests will help identify if there are format differences between your")
    print("     block group IDs and what the Census API expects")
    print("   - Common issues include:")
    print("     * Missing leading zeros")
    print("     * Different length identifiers")
    print("     * Missing or extra components (state, county, tract, block group)")
    
    print("\n3. Census API Connection Issues")
    print("   - Check your internet connection")
    print("   - Make sure the Census API endpoint is available")
    print("   - Verify you're using a valid year and dataset (default: 2021 acs/acs5)")
    
    print("\n4. Data Structure Issues")
    print("   - The test will report the structure of your block groups GeoJSON")
    print("   - Make sure it contains the expected columns (GEOID, STATE, etc.)")
    
    print("\nFor more help:")
    print("  - Check the Census API documentation: https://www.census.gov/data/developers/guidance/api-user-guide.html")
    print("  - Examine the Census data structure using the API's variables endpoint")

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Run tests for census_data.py")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--real-data", "-r", action="store_true", 
                       help="Include tests with real data files from the results directory")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("CENSUS DATA MODULE TESTER")
    print("="*80)
    
    # System checks
    has_key = check_api_key()
    has_pytest = check_pytest()
    
    if not has_pytest:
        if not install_pytest():
            print("Please install pytest manually: pip install pytest")
            return
    
    # Run the tests
    if not has_key:
        print("\n⚠️ Running tests without Census API key - API tests will be skipped")
    
    print("\nRunning tests...")
    success = run_tests(verbose=args.verbose, real_data=args.real_data)
    
    # Always show troubleshooting information
    display_troubleshooting_guide()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 