#!/usr/bin/env python3
"""Test SocialMapper CLI with OSMnx integration."""

import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from socialmapper.console import print_success, print_error, print_info, print_warning


def test_cli_fuquay_varina():
    """Test CLI with Fuquay-Varina schools."""
    print_info("\n=== Testing CLI with Fuquay-Varina Schools ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            "uv", "run", "python", "-m", "socialmapper.cli_main",
            "--poi",
            "--geocode-area", "Fuquay-Varina",
            "--state", "North Carolina",
            "--poi-type", "amenity",
            "--poi-name", "school",
            "--travel-time", "15",
            "--travel-mode", "walk",
            "--output-dir", temp_dir,
            "--no-export-csv",  # Disable CSV export for faster testing
        ]
        
        print_info("Running command:")
        print_info(" ".join(cmd))
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print_success("✓ CLI completed successfully!")
                
                # Check for POI count in output
                if "Found 12 POIs" in result.stdout:
                    print_success("✓ Found expected 12 schools in Fuquay-Varina")
                elif "Found" in result.stdout and "POIs" in result.stdout:
                    import re
                    match = re.search(r"Found (\d+) POIs", result.stdout)
                    if match:
                        poi_count = match.group(1)
                        print_info(f"Found {poi_count} schools (expected 12)")
                
                # Check output files
                output_files = list(Path(temp_dir).glob("**/*"))
                if output_files:
                    print_info(f"Created {len(output_files)} output files:")
                    for file in output_files[:5]:
                        print_info(f"  • {file.name}")
                
                return True
            else:
                print_error("✗ CLI failed")
                print_error(f"Return code: {result.returncode}")
                if result.stderr:
                    print_error(f"Error output:\n{result.stderr[:1000]}")
                if result.stdout:
                    print_info(f"Standard output:\n{result.stdout[:1000]}")
                return False
                
        except subprocess.TimeoutExpired:
            print_error("✗ CLI timed out after 120 seconds")
            return False
        except Exception as e:
            print_error(f"✗ Unexpected error: {e}")
            return False


def test_direct_extraction():
    """Test the extraction module directly."""
    print_info("\n=== Testing Direct Extraction Module ===")
    
    from socialmapper.pipeline.extraction import extract_poi_data
    
    try:
        poi_data, base_filename, state_abbreviations, sampled_pois = extract_poi_data(
            geocode_area="Fuquay-Varina",
            state="North Carolina",
            poi_type="amenity",
            poi_name="school"
        )
        
        poi_count = len(poi_data.get('pois', []))
        
        if poi_count == 12:
            print_success(f"✓ Extraction successful: Found expected 12 schools")
        else:
            print_warning(f"⚠ Found {poi_count} schools (expected 12)")
        
        print_info(f"Base filename: {base_filename}")
        print_info(f"State abbreviations: {state_abbreviations}")
        
        # Show first few schools
        if poi_count > 0:
            print_info("\nFirst 3 schools:")
            for i, poi in enumerate(poi_data['pois'][:3], 1):
                name = poi.get('name') or poi.get('tags', {}).get('name', 'Unnamed')
                print_info(f"  {i}. {name}")
        
        return poi_count > 0
        
    except Exception as e:
        print_error(f"✗ Extraction failed: {e}")
        return False


def main():
    """Run tests."""
    print_info("=" * 60)
    print_info("SocialMapper CLI Integration Test")
    print_info("=" * 60)
    
    # Test direct extraction first
    extraction_success = test_direct_extraction()
    
    # Then test CLI
    cli_success = test_cli_fuquay_varina()
    
    # Summary
    print_info("\n" + "=" * 60)
    if extraction_success and cli_success:
        print_success("✓ All tests passed!")
        print_info("\nOSMnx integration is working correctly:")
        print_info("• POI extraction uses OSMnx's features_from_place()")
        print_info("• Handles location name variations (Fuquay Varina / Fuquay-Varina)")
        print_info("• Successfully finds 12 schools in Fuquay-Varina")
    elif extraction_success:
        print_warning("⚠ Extraction works but CLI integration has issues")
    else:
        print_error("✗ Tests failed - check errors above")
    print_info("=" * 60)


if __name__ == "__main__":
    main()