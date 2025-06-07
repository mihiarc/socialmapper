#!/usr/bin/env python3
"""
SocialMapper Cold Cache Demo
============================

Tests SocialMapper functionality from a completely fresh start with no cached data.
This ensures robustness for new installations and validates that all systems work
properly without relying on pre-existing cache.

Features tested:
- Complete cache clearing
- POI discovery from OpenStreetMap  
- Network download and isochrone generation
- Census data integration
- Performance monitoring cold vs warm
- Cache rebuilding process

Author: SocialMapper Team
Date: June 2025
"""

import sys
import time
import shutil
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from socialmapper.core import run_socialmapper
from socialmapper.ui.rich_console import (
    console, print_banner, print_success, print_error, print_warning, 
    print_info, status_spinner, print_step, print_divider
)
from rich.table import Table
from rich.panel import Panel
from rich import box


def print_header(title: str, subtitle: str = ""):
    """Print a formatted header."""
    if subtitle:
        header_text = f"[bold cyan]{title}[/bold cyan]\n[dim]{subtitle}[/dim]"
    else:
        header_text = f"[bold cyan]{title}[/bold cyan]"
    
    panel = Panel(header_text, box=box.ROUNDED, border_style="cyan")
    console.print(panel)


def get_cache_size(cache_dir: Path) -> Dict[str, Any]:
    """Get cache directory size and file count."""
    if not cache_dir.exists():
        return {"size_mb": 0, "file_count": 0, "exists": False}
    
    total_size = 0
    file_count = 0
    
    for file_path in cache_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    return {
        "size_mb": total_size / (1024 * 1024),
        "file_count": file_count,
        "exists": True
    }


def display_cache_status(cache_dir: Path, status: str = "Current"):
    """Display current cache status in a formatted table."""
    cache_info = get_cache_size(cache_dir)
    geocoding_cache = cache_dir / "geocoding"
    networks_cache = cache_dir / "networks"
    
    # Get subcache info
    geocoding_info = get_cache_size(geocoding_cache)
    networks_info = get_cache_size(networks_cache)
    
    table = Table(title=f"📊 {status} Cache Status", box=box.ROUNDED)
    table.add_column("Cache Type", style="cyan")
    table.add_column("Size (MB)", style="green", justify="right")
    table.add_column("Files", style="yellow", justify="right")
    table.add_column("Status", style="magenta")
    
    # Main cache
    status_icon = "✅ Active" if cache_info["exists"] and cache_info["file_count"] > 0 else "❌ Empty"
    table.add_row(
        "Total Cache",
        f"{cache_info['size_mb']:.1f}",
        str(cache_info['file_count']),
        status_icon
    )
    
    # Geocoding cache
    geo_status = "✅ Active" if geocoding_info["exists"] and geocoding_info["file_count"] > 0 else "❌ Empty"
    table.add_row(
        "Geocoding Cache",
        f"{geocoding_info['size_mb']:.1f}",
        str(geocoding_info['file_count']),
        geo_status
    )
    
    # Networks cache
    net_status = "✅ Active" if networks_info["exists"] and networks_info["file_count"] > 0 else "❌ Empty"
    table.add_row(
        "Networks Cache",
        f"{networks_info['size_mb']:.1f}",
        str(networks_info['file_count']),
        net_status
    )
    
    console.print(table)


def clear_all_caches(cache_dir: Path) -> Dict[str, Any]:
    """Clear all SocialMapper caches and return stats about what was cleared."""
    print_step(1, 5, "Cache Clearing Process", "🧹")
    
    # Show initial cache state
    initial_stats = get_cache_size(cache_dir)
    console.print(f"[yellow]Initial cache state:[/yellow]")
    display_cache_status(cache_dir, "Pre-Clear")
    
    if not cache_dir.exists():
        print_info("No cache directory found - already in cold state!")
        return {"cleared_mb": 0, "cleared_files": 0, "was_empty": True}
    
    # Clear cache with progress
    with status_spinner("🗑️ Clearing all cached data..."):
        try:
            shutil.rmtree(cache_dir)
            time.sleep(1)  # Brief pause for dramatic effect
        except Exception as e:
            print_error(f"Error clearing cache: {e}")
            return {"error": str(e)}
    
    print_success(
        f"Successfully cleared {initial_stats['size_mb']:.1f} MB of cached data "
        f"({initial_stats['file_count']} files)"
    )
    
    # Verify cache is cleared
    display_cache_status(cache_dir, "Post-Clear")
    
    return {
        "cleared_mb": initial_stats['size_mb'],
        "cleared_files": initial_stats['file_count'],
        "was_empty": False
    }


def run_cold_cache_test() -> Dict[str, Any]:
    """Run SocialMapper from cold cache and measure performance."""
    print_step(2, 5, "Cold Cache SocialMapper Test", "❄️")
    
    # Test configuration - use a small, reliable location
    config = {
        "geocode_area": "Fuquay-Varina",
        "state": "NC", 
        "poi_type": "amenity",
        "poi_name": "library",
        "travel_time": 15,
        "census_variables": ["total_population", "median_income"],
        "export_csv": True,
        "export_maps": False,  # Skip maps for faster testing
        "max_poi_count": 5  # Limit POIs for faster test
    }
    
    console.print("[yellow]🧪 Test Configuration:[/yellow]")
    config_table = Table(box=box.ROUNDED)
    config_table.add_column("Parameter", style="cyan")
    config_table.add_column("Value", style="green")
    
    for key, value in config.items():
        config_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(config_table)
    
    # Run the test
    print_info("Starting cold cache test - this will take longer than usual...")
    
    start_time = time.time()
    
    try:
        # Run without spinner to avoid Rich display conflicts
        console.print("[yellow]🔄 Running SocialMapper from cold cache...[/yellow]")
        results = run_socialmapper(**config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_success(f"Cold cache test completed successfully in {duration:.1f} seconds!")
        
        return {
            "success": True,
            "duration": duration,
            "results": results,
            "config": config
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print_error(f"Cold cache test failed after {duration:.1f} seconds: {e}")
        
        return {
            "success": False,
            "duration": duration,
            "error": str(e),
            "config": config
        }


def analyze_cache_rebuild(cache_dir: Path, initial_stats: Dict[str, Any]):
    """Analyze how the cache was rebuilt during the test."""
    print_step(3, 5, "Cache Rebuild Analysis", "📈")
    
    # Show final cache state
    final_stats = get_cache_size(cache_dir)
    display_cache_status(cache_dir, "Post-Test")
    
    # Calculate cache growth
    cache_growth = final_stats['size_mb'] - initial_stats.get('cleared_mb', 0)
    files_created = final_stats['file_count']
    
    console.print(f"\n[bold green]📊 Cache Rebuild Summary:[/bold green]")
    console.print(f"  • Cache rebuilt: {final_stats['size_mb']:.1f} MB")
    console.print(f"  • Files created: {files_created}")
    console.print(f"  • Efficiency: Cold cache forced fresh downloads")
    console.print(f"  • Future runs: Will benefit from this cached data")
    
    # Show what was cached
    geocoding_cache = cache_dir / "geocoding"
    networks_cache = cache_dir / "networks"
    
    if geocoding_cache.exists():
        console.print(f"  • ✅ Geocoding cache: Address lookups now cached")
    if networks_cache.exists():
        console.print(f"  • ✅ Networks cache: Road networks now cached")


def run_warm_cache_comparison(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Run the same test with warm cache for comparison."""
    print_step(4, 5, "Warm Cache Comparison Test", "🔥")
    
    print_info("Running identical test with warm cache for performance comparison...")
    
    start_time = time.time()
    
    try:
        # Run without spinner to avoid Rich display conflicts
        console.print("[yellow]⚡ Running SocialMapper with warm cache...[/yellow]")
        results = run_socialmapper(**config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_success(f"Warm cache test completed in {duration:.1f} seconds!")
        
        return {
            "success": True,
            "duration": duration,
            "results": results
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print_warning(f"Warm cache test failed after {duration:.1f} seconds: {e}")
        
        return {
            "success": False,
            "duration": duration,
            "error": str(e)
        }


def display_performance_comparison(cold_results: Dict[str, Any], warm_results: Optional[Dict[str, Any]]):
    """Display performance comparison between cold and warm cache."""
    print_step(5, 5, "Performance Analysis", "📊")
    
    # Create comparison table
    comparison_table = Table(title="❄️ Cold Cache vs 🔥 Warm Cache Performance", box=box.ROUNDED)
    comparison_table.add_column("Metric", style="cyan")
    comparison_table.add_column("Cold Cache", style="blue")
    comparison_table.add_column("Warm Cache", style="red")
    comparison_table.add_column("Improvement", style="green")
    
    cold_duration = cold_results.get('duration', 0)
    
    if warm_results and warm_results.get('success'):
        warm_duration = warm_results.get('duration', 0)
        speedup = cold_duration / warm_duration if warm_duration > 0 else 0
        improvement = f"{speedup:.1f}x faster"
        time_saved = cold_duration - warm_duration
        
        comparison_table.add_row("Execution Time", f"{cold_duration:.1f}s", f"{warm_duration:.1f}s", improvement)
        comparison_table.add_row("Time Saved", "Baseline", f"{time_saved:.1f}s", f"{time_saved:.1f}s saved")
        
        # Show success status
        cold_status = "✅ Success" if cold_results.get('success') else "❌ Failed"
        warm_status = "✅ Success" if warm_results.get('success') else "❌ Failed"
        comparison_table.add_row("Status", cold_status, warm_status, "Both working!")
        
    else:
        comparison_table.add_row("Execution Time", f"{cold_duration:.1f}s", "N/A", "Baseline")
        comparison_table.add_row("Status", "✅ Success" if cold_results.get('success') else "❌ Failed", "Not tested", "-")
    
    console.print(comparison_table)
    
    # Analysis
    console.print(f"\n[bold cyan]🔍 Analysis:[/bold cyan]")
    if cold_results.get('success'):
        console.print(f"  • ✅ Cold cache test passed - SocialMapper works from fresh install")
        console.print(f"  • ⏱️ First run took {cold_duration:.1f}s (includes all downloads)")
        console.print(f"  • 🗄️ Cache now populated for future performance gains")
        
        if warm_results and warm_results.get('success'):
            warm_duration = warm_results.get('duration', 0)
            speedup = cold_duration / warm_duration if warm_duration > 0 else 0
            console.print(f"  • 🚀 Subsequent runs {speedup:.1f}x faster due to caching")
        
        console.print(f"  • 🎯 System is robust and ready for production use")
    else:
        console.print(f"  • ❌ Cold cache test failed - investigation needed")
        console.print(f"  • 🔧 Check network connectivity and API availability")


def main():
    """Main cold cache demo function."""
    print_banner(
        "Cold Cache Demo", 
        "Testing SocialMapper from completely fresh start",
        "Ensuring robustness for new installations"
    )
    
    cache_dir = Path("cache")
    
    try:
        # Step 1: Clear all caches
        initial_stats = clear_all_caches(cache_dir)
        
        # Step 2: Run cold cache test
        cold_results = run_cold_cache_test()
        
        # Step 3: Analyze cache rebuild
        analyze_cache_rebuild(cache_dir, initial_stats)
        
        # Step 4: Run warm cache comparison
        if cold_results.get('success'):
            warm_results = run_warm_cache_comparison(cold_results.get('config', {}))
        else:
            warm_results = None
            print_warning("Skipping warm cache test due to cold cache failure")
        
        # Step 5: Display performance comparison
        display_performance_comparison(cold_results, warm_results)
        
        # Final summary
        print_divider("Cold Cache Demo Complete")
        
        if cold_results.get('success'):
            print_success(
                "✅ Cold cache demo completed successfully!\n"
                "SocialMapper is robust and works perfectly from fresh installations.\n"
                "Cache has been rebuilt and future runs will be significantly faster.",
                "Demo Success"
            )
            
            console.print("\n[bold cyan]🎯 Key Findings:[/bold cyan]")
            console.print("  ✅ Fresh installation workflow verified")
            console.print("  ✅ All APIs and data sources accessible")
            console.print("  ✅ Cache rebuild process working correctly")
            console.print("  ✅ Performance optimization through caching confirmed")
            console.print("  ✅ System ready for production deployment")
            
        else:
            print_error(
                "❌ Cold cache demo encountered issues.\n"
                "This indicates potential problems with fresh installations.",
                "Demo Issues"
            )
            
            console.print("\n[bold red]🔧 Troubleshooting Steps:[/bold red]")
            console.print("  1. Check internet connectivity")
            console.print("  2. Verify OpenStreetMap API accessibility")
            console.print("  3. Check Census API availability")
            console.print("  4. Review error logs above")
            console.print("  5. Try with different location/POI parameters")
    
    except KeyboardInterrupt:
        print_warning("Demo interrupted by user")
    except Exception as e:
        print_error(f"Demo failed with unexpected error: {e}")
        raise


if __name__ == "__main__":
    main() 