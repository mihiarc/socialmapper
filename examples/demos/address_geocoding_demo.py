#!/usr/bin/env python3
"""
SocialMapper Address Geocoding Demo
==================================

Comprehensive demonstration of the modern address lookup system showing:
- Multiple geocoding providers with intelligent fallback
- Quality validation and caching
- Batch processing with progress tracking
- Integration with SocialMapper workflow
- Error handling and performance monitoring

Author: SocialMapper Team
Date: June 2025
"""

import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from socialmapper.geocoding import (
    geocode_address, geocode_addresses, addresses_to_poi_format,
    AddressInput, GeocodingConfig, AddressProvider, AddressQuality
)
from socialmapper.ui.rich_console import console
from rich.table import Table
from rich.panel import Panel
from rich import box


def print_header(title: str, subtitle: str = ""):
    """Print a formatted header."""
    header_text = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        header_text += f"\n[dim]{subtitle}[/dim]"
    
    panel = Panel(
        header_text,
        box=box.ROUNDED,
        border_style="cyan"
    )
    console.print(panel)


def demo_single_address_geocoding():
    """Demonstrate single address geocoding with different providers."""
    print_header("🏠 Single Address Geocoding Demo", "Testing different providers and quality levels")
    
    # Sample addresses of different types
    test_addresses = [
        "1600 Pennsylvania Avenue NW, Washington, DC 20500",  # The White House
        "350 Fifth Avenue, New York, NY 10118",  # Empire State Building
        "Fuquay-Varina, NC",  # City-level address
        "12345 Nonexistent Street, Nowhere, XX 99999"  # Invalid address
    ]
    
    for i, address_str in enumerate(test_addresses, 1):
        console.print(f"\n[bold]Test {i}: {address_str}[/bold]")
        
        # Create address input
        address = AddressInput(
            address=address_str,
            id=f"test_{i}",
            source="demo"
        )
        
        # Test with different providers
        providers = [AddressProvider.NOMINATIM, AddressProvider.CENSUS]
        
        for provider in providers:
            try:
                config = GeocodingConfig(
                    primary_provider=provider,
                    min_quality_threshold=AddressQuality.APPROXIMATE
                )
                
                start_time = time.time()
                result = geocode_address(address, config)
                elapsed = time.time() - start_time
                
                if result.success:
                    console.print(f"  ✅ {provider.value}: {result.latitude:.6f}, {result.longitude:.6f}")
                    console.print(f"     Quality: {result.quality.value}, Confidence: {result.confidence_score:.2f}")
                    console.print(f"     Time: {elapsed*1000:.1f}ms")
                    if result.formatted_address:
                        console.print(f"     Formatted: {result.formatted_address}")
                else:
                    console.print(f"  ❌ {provider.value}: {result.error_message}")
                    
            except Exception as e:
                console.print(f"  💥 {provider.value}: Error - {e}")


def demo_batch_geocoding():
    """Demonstrate batch geocoding with progress tracking."""
    print_header("🏙️ Batch Address Geocoding Demo", "Processing multiple addresses with caching and monitoring")
    
    # Sample batch of addresses
    addresses = [
        "100 Universal City Plaza, Universal City, CA 91608",  # Universal Studios
        "1313 Disneyland Dr, Anaheim, CA 92802",  # Disneyland
        "1000 Vin Scully Ave, Los Angeles, CA 90012",  # Dodger Stadium
        "1111 S Figueroa St, Los Angeles, CA 90015",  # Crypto.com Arena
        "1 E 161st St, Bronx, NY 10451",  # Yankee Stadium
        "4 Yawkey Way, Boston, MA 02215",  # Fenway Park
        "900 S Main St, Fuquay-Varina, NC 27526",  # Fuquay-Varina Library
        "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",  # SF City Hall
        "1200 Getty Center Dr, Los Angeles, CA 90049",  # Getty Center
        "2001 Blake St, Denver, CO 80205"  # Coors Field
    ]
    
    # Create address inputs with metadata
    address_inputs = [
        AddressInput(
            address=addr,
            id=f"venue_{i}",
            source="demo_batch"
        )
        for i, addr in enumerate(addresses, 1)
    ]
    
    console.print(f"[bold yellow]🔍 Geocoding {len(address_inputs)} addresses...[/bold yellow]")
    
    # Configure for optimal batch processing
    config = GeocodingConfig(
        primary_provider=AddressProvider.NOMINATIM,
        fallback_providers=[AddressProvider.CENSUS],
        min_quality_threshold=AddressQuality.CENTROID,
        enable_cache=True,
        batch_size=5,
        batch_delay_seconds=0.2  # Be nice to free APIs
    )
    
    start_time = time.time()
    results = geocode_addresses(address_inputs, config, progress=True)
    elapsed = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    console.print(f"\n[bold green]✅ Batch Processing Complete![/bold green]")
    console.print(f"  • Total addresses: {len(results)}")
    console.print(f"  • Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    console.print(f"  • Failed: {len(failed)}")
    console.print(f"  • Total time: {elapsed:.2f}s")
    console.print(f"  • Average per address: {elapsed/len(results)*1000:.1f}ms")
    
    # Show results table
    if successful:
        results_table = Table(title="🗺️ Geocoding Results", box=box.ROUNDED)
        results_table.add_column("Address", style="cyan", no_wrap=False, max_width=40)
        results_table.add_column("Coordinates", style="green")
        results_table.add_column("Quality", style="yellow")
        results_table.add_column("Provider", style="magenta")
        
        for result in successful[:5]:  # Show first 5 results
            coords = f"{result.latitude:.4f}, {result.longitude:.4f}"
            quality = result.quality.value
            provider = result.provider_used.value if result.provider_used else "unknown"
            
            results_table.add_row(
                result.input_address.address[:40] + "..." if len(result.input_address.address) > 40 else result.input_address.address,
                coords,
                quality,
                provider
            )
        
        console.print(results_table)
        
        if len(successful) > 5:
            console.print(f"[dim]... and {len(successful) - 5} more results[/dim]")
    
    return successful


def demo_poi_integration(geocoded_results: List):
    """Demonstrate integration with SocialMapper POI workflow."""
    print_header("🔗 SocialMapper Integration Demo", "Converting geocoded addresses to POI format for analysis")
    
    if not geocoded_results:
        console.print("[red]No geocoded results available for integration demo[/red]")
        return
    
    # Convert to POI format
    console.print("[bold yellow]🔄 Converting to SocialMapper POI format...[/bold yellow]")
    
    # Use the engine to convert results
    from socialmapper.geocoding.engine import AddressGeocodingEngine
    
    config = GeocodingConfig()
    engine = AddressGeocodingEngine(config)
    poi_data = engine.convert_to_poi_format(geocoded_results)
    
    console.print(f"[green]✅ Converted {poi_data['poi_count']} addresses to POI format[/green]")
    
    # Show POI format sample
    if poi_data['pois']:
        poi_table = Table(title="📍 POI Format Sample", box=box.ROUNDED)
        poi_table.add_column("Name", style="cyan")
        poi_table.add_column("Coordinates", style="green")
        poi_table.add_column("Type", style="yellow")
        poi_table.add_column("Quality", style="magenta")
        
        for poi in poi_data['pois'][:3]:  # Show first 3
            coords = f"{poi['lat']:.4f}, {poi['lon']:.4f}"
            quality = poi['tags'].get('geocoding:quality', 'unknown')
            
            poi_table.add_row(
                poi['name'][:30] + "..." if len(poi['name']) > 30 else poi['name'],
                coords,
                poi['type'],
                quality
            )
        
        console.print(poi_table)
    
    # Show metadata
    metadata = poi_data['metadata']
    stats_table = Table(title="📊 Geocoding Statistics", box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Total Addresses", str(metadata['total_addresses']))
    stats_table.add_row("Successful Geocodes", str(metadata['successful_geocodes']))
    stats_table.add_row("Failed Geocodes", str(metadata['failed_geocodes']))
    
    if 'geocoding_stats' in metadata:
        stats = metadata['geocoding_stats']
        stats_table.add_row("Cache Hit Rate", f"{stats.get('cache_hit_rate', 0)*100:.1f}%")
        stats_table.add_row("Success Rate", f"{stats.get('success_rate', 0)*100:.1f}%")
    
    console.print(stats_table)
    
    # Create sample CSV for SocialMapper
    sample_file = "output/demo_geocoded_addresses.csv"
    Path("output").mkdir(exist_ok=True)
    
    if poi_data['pois']:
        df = pd.DataFrame([
            {
                'name': poi['name'],
                'latitude': poi['lat'],
                'longitude': poi['lon'],
                'type': poi['type'],
                'geocoding_provider': poi['tags'].get('geocoding:provider'),
                'geocoding_quality': poi['tags'].get('geocoding:quality'),
                'geocoding_confidence': poi['tags'].get('geocoding:confidence')
            }
            for poi in poi_data['pois']
        ])
        
        df.to_csv(sample_file, index=False)
        console.print(f"[dim]Sample CSV saved to: {sample_file}[/dim]")
        
        # Show how to use with SocialMapper CLI
        console.print("\n[bold]🚀 Usage with SocialMapper CLI:[/bold]")
        cli_command = f"socialmapper --custom-coords {sample_file} --travel-time 15 --export-maps --map-backend plotly"
        console.print(f"[cyan]{cli_command}[/cyan]")


def demo_error_handling_and_quality():
    """Demonstrate error handling and quality validation."""
    print_header("🛡️ Error Handling & Quality Demo", "Testing robustness and quality thresholds")
    
    # Test different quality scenarios
    test_cases = [
        {
            "address": "1600 Pennsylvania Avenue, Washington DC",
            "threshold": AddressQuality.EXACT,
            "description": "High-quality address with exact threshold"
        },
        {
            "address": "Washington, DC",
            "threshold": AddressQuality.EXACT,
            "description": "City-level address with exact threshold (should fail quality check)"
        },
        {
            "address": "Washington, DC",
            "threshold": AddressQuality.CENTROID,
            "description": "City-level address with centroid threshold (should pass)"
        },
        {
            "address": "This is not a real address at all",
            "threshold": AddressQuality.APPROXIMATE,
            "description": "Invalid address (should fail geocoding)"
        }
    ]
    
    quality_table = Table(title="🎯 Quality Threshold Testing", box=box.ROUNDED)
    quality_table.add_column("Test", style="cyan")
    quality_table.add_column("Address", style="yellow")
    quality_table.add_column("Threshold", style="magenta")
    quality_table.add_column("Result", style="green")
    
    for i, test in enumerate(test_cases, 1):
        address = AddressInput(
            address=test["address"],
            quality_threshold=test["threshold"]
        )
        
        config = GeocodingConfig(
            min_quality_threshold=test["threshold"]
        )
        
        try:
            result = geocode_address(address, config)
            
            if result.success:
                status = f"✅ Success ({result.quality.value})"
            else:
                status = f"❌ Failed: {result.error_message}"
                
        except Exception as e:
            status = f"💥 Error: {str(e)}"
        
        quality_table.add_row(
            f"Test {i}",
            test["address"][:30] + "..." if len(test["address"]) > 30 else test["address"],
            test["threshold"].value,
            status
        )
    
    console.print(quality_table)


def demo_performance_comparison():
    """Demonstrate performance characteristics of different providers."""
    print_header("⚡ Performance Comparison Demo", "Benchmarking different geocoding providers")
    
    # Test addresses that should work with both providers
    test_addresses = [
        "1600 Pennsylvania Avenue NW, Washington, DC 20500",
        "350 Fifth Avenue, New York, NY 10118",
        "1 Infinite Loop, Cupertino, CA 95014",
        "1600 Amphitheatre Parkway, Mountain View, CA 94043",
        "410 Terry Avenue North, Seattle, WA 98109"
    ]
    
    providers = [AddressProvider.NOMINATIM, AddressProvider.CENSUS]
    performance_data = []
    
    for provider in providers:
        console.print(f"\n[bold]Testing {provider.value.upper()}...[/bold]")
        
        config = GeocodingConfig(
            primary_provider=provider,
            fallback_providers=[],  # No fallback for pure performance test
            enable_cache=False  # Disable cache for fair comparison
        )
        
        times = []
        successes = 0
        
        for address_str in test_addresses:
            address = AddressInput(address=address_str)
            
            start_time = time.time()
            result = geocode_address(address, config)
            elapsed = time.time() - start_time
            
            times.append(elapsed * 1000)  # Convert to ms
            if result.success:
                successes += 1
        
        avg_time = sum(times) / len(times)
        success_rate = successes / len(test_addresses) * 100
        
        performance_data.append({
            'provider': provider.value.upper(),
            'avg_time_ms': avg_time,
            'success_rate': success_rate,
            'total_time_ms': sum(times)
        })
        
        console.print(f"  Average time: {avg_time:.1f}ms")
        console.print(f"  Success rate: {success_rate:.1f}%")
        console.print(f"  Total time: {sum(times):.1f}ms")
    
    # Performance comparison table
    perf_table = Table(title="🏆 Performance Comparison", box=box.ROUNDED)
    perf_table.add_column("Provider", style="cyan")
    perf_table.add_column("Avg Time (ms)", style="green")
    perf_table.add_column("Success Rate", style="yellow")
    perf_table.add_column("Total Time (ms)", style="magenta")
    
    for data in performance_data:
        perf_table.add_row(
            data['provider'],
            f"{data['avg_time_ms']:.1f}",
            f"{data['success_rate']:.1f}%",
            f"{data['total_time_ms']:.1f}"
        )
    
    console.print(perf_table)


def main():
    """Main demo function."""
    console.print("[bold green]🚀 SocialMapper Address Geocoding Demo[/bold green]")
    console.print("[dim]Comprehensive demonstration of the modern address lookup system[/dim]")
    
    try:
        # Demo 1: Single address geocoding
        demo_single_address_geocoding()
        
        # Demo 2: Batch geocoding
        geocoded_results = demo_batch_geocoding()
        
        # Demo 3: SocialMapper integration
        demo_poi_integration(geocoded_results)
        
        # Demo 4: Error handling and quality
        demo_error_handling_and_quality()
        
        # Demo 5: Performance comparison
        demo_performance_comparison()
        
        # Summary
        print_header("🎉 Demo Complete!", "Address geocoding system is ready for production use")
        
        console.print("\n[bold]Key Features Demonstrated:[/bold]")
        console.print("  • Multiple geocoding providers with intelligent fallback")
        console.print("  • Quality validation and threshold enforcement")
        console.print("  • High-performance caching with Parquet storage")
        console.print("  • Batch processing with progress tracking")
        console.print("  • Seamless SocialMapper integration")
        console.print("  • Robust error handling and monitoring")
        
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("  1. Try address geocoding with your own data")
        console.print("  2. Use the CLI: socialmapper --addresses --address-file your_file.csv")
        console.print("  3. Experiment with different quality thresholds")
        console.print("  4. Compare provider performance for your use case")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Demo failed: {e}[/bold red]")
        raise


if __name__ == "__main__":
    main() 