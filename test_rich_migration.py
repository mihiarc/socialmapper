#!/usr/bin/env python3
"""
Test script for Rich migration in SocialMapper.

This script tests that the Rich console and progress bars work correctly
after replacing logging and tqdm throughout the codebase.
"""

import sys
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from socialmapper.ui.rich_console import (
    console,
    setup_rich_logging,
    get_logger,
    print_info,
    print_success,
    print_warning,
    print_error,
    print_panel,
    print_table,
    print_statistics,
    rich_tqdm,
    progress_bar,
    status
)

def test_rich_logging():
    """Test Rich logging functionality."""
    print_panel("Testing Rich Logging", title="🪵 Logging Test", style="cyan")
    
    # Setup Rich logging
    setup_rich_logging(level="INFO", show_time=True, show_path=False)
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print_success("Rich logging test completed")

def test_rich_console():
    """Test Rich console functionality."""
    print_panel("Testing Rich Console", title="🖥️ Console Test", style="green")
    
    # Test basic console functions
    print_info("This is an info message")
    print_success("This is a success message")
    print_warning("This is a warning message")
    print_error("This is an error message")
    
    # Test table functionality
    sample_data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Los Angeles"},
        {"name": "Charlie", "age": 35, "city": "Chicago"}
    ]
    print_table(sample_data, title="Sample Data Table")
    
    # Test statistics
    stats = {
        "total_items": 100,
        "success_rate": 0.95,
        "average_time": 2.5,
        "cache_hits": 85
    }
    print_statistics(stats, title="Sample Statistics")

def test_rich_progress():
    """Test Rich progress bars."""
    print_panel("Testing Rich Progress Bars", title="📊 Progress Test", style="orange")
    
    # Test basic progress bar
    items = range(50)
    with rich_tqdm(items, desc="Processing items") as pbar:
        for item in pbar:
            time.sleep(0.02)  # Simulate work
    
    print_success("Basic progress bar test completed")
    
    # Test context manager progress bar
    with progress_bar("Advanced processing", total=30) as progress:
        task_id = progress.task_id
        for i in range(30):
            time.sleep(0.03)
            progress.update(task_id, advance=1)
    
    print_success("Advanced progress bar test completed")

def test_rich_status():
    """Test Rich status spinners."""
    print_panel("Testing Rich Status Spinners", title="⏳ Status Test", style="purple")
    
    with status("Loading data..."):
        time.sleep(1)
    
    with status("Processing results...", spinner="earth"):
        time.sleep(1)
    
    print_success("Status spinner test completed")

def test_geocoding_import():
    """Test that the geocoding module imports correctly with Rich."""
    print_panel("Testing Geocoding Import", title="🗺️ Import Test", style="blue")
    
    try:
        from socialmapper.geocoding import (
            geocode_address,
            AddressInput,
            GeocodingConfig
        )
        print_success("Geocoding module imported successfully")
        
        # Test a simple address geocoding
        config = GeocodingConfig(enable_cache=False)
        address = AddressInput(address="1600 Pennsylvania Avenue NW, Washington, DC")
        
        with status("Testing address geocoding..."):
            result = geocode_address(address, config)
        
        if result.success:
            print_success(f"Address geocoded successfully: {result.latitude:.4f}, {result.longitude:.4f}")
        else:
            print_warning(f"Geocoding failed: {result.error_message}")
            
    except Exception as e:
        print_error(f"Geocoding import/test failed: {e}")

def main():
    """Run all Rich migration tests."""
    console.print()
    print_panel(
        "Rich Migration Test Suite\n\nTesting the replacement of logging and tqdm with Rich throughout SocialMapper",
        title="🎨 SocialMapper Rich Migration",
        style="bold cyan"
    )
    
    tests = [
        ("Rich Logging", test_rich_logging),
        ("Rich Console", test_rich_console),
        ("Rich Progress", test_rich_progress),
        ("Rich Status", test_rich_status),
        ("Geocoding Integration", test_geocoding_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            console.print(f"\n{'='*60}")
            test_func()
            passed += 1
        except Exception as e:
            print_error(f"Test '{test_name}' failed: {e}")
            console.print_exception()
    
    console.print(f"\n{'='*60}")
    
    # Final summary
    if passed == total:
        print_success(f"All {total} tests passed! Rich migration successful! 🎉")
    else:
        print_warning(f"{passed}/{total} tests passed. Some issues need attention.")
    
    # Show final statistics
    final_stats = {
        "tests_run": total,
        "tests_passed": passed,
        "success_rate": passed / total if total > 0 else 0,
        "migration_status": "Complete" if passed == total else "Partial"
    }
    print_statistics(final_stats, title="Migration Test Results")

if __name__ == "__main__":
    main() 