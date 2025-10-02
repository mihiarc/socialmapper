#!/usr/bin/env python3
"""
SocialMapper Tutorial 05: Address Geocoding

This tutorial demonstrates how to convert addresses into coordinates for analysis:
- Understanding geocoding providers and quality levels
- Single address vs batch processing
- Integration with SocialMapper workflows
- Error handling and performance optimization
- Creating POI datasets from address lists

Perfect for:
- Researchers with address lists who need coordinates
- Urban planners analyzing accessibility by address
- Business analysts studying location-based demographics
- Anyone wanting to create custom POI datasets from addresses

Prerequisites:
- SocialMapper installed: uv add socialmapper
- Internet connection for geocoding services
- Optional: Census API key for enhanced accuracy
"""

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv not available - continue without it
    pass

import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console
from rich.panel import Panel

from socialmapper import SocialMapperBuilder, SocialMapperClient
from socialmapper.geocoding import (
    AddressInput,
    AddressProvider,
    AddressQuality,
    GeocodingConfig,
    geocode_address,
    geocode_addresses,
)

# Create console instance
console = Console()


def explain_geocoding():
    """Explain what geocoding is and why it's useful."""
    console.print(Panel(
        """Address geocoding converts human-readable addresses into geographic coordinates (latitude/longitude).

🎯 Why Use Geocoding?
  • Convert address lists into mappable coordinates
  • Analyze service accessibility by street address
  • Integrate business locations with demographic data
  • Create custom POI datasets from address databases

🏗️ SocialMapper Providers:
  • Nominatim (OpenStreetMap): Free, global, good for general use
  • Census Bureau: US-only, very accurate for US addresses
  • Automatic fallback between providers for best results""",
        title="📍 Understanding Address Geocoding",
        border_border_style="cyan",
    ))


def demo_single_address():
    """Demonstrate single address geocoding."""
    console.print("\n[bold cyan]Step 1: Single Address Geocoding[/bold cyan]")
    console.print("Let's start by geocoding a single famous address:\n")

    # Example address
    address_str = "1600 Pennsylvania Avenue NW, Washington, DC 20500"
    console.print(f"🏛️  Address: {address_str}")

    # Create address input
    address = AddressInput(address=address_str, id="white_house", source="tutorial")

    # Configure geocoding
    config = GeocodingConfig(
        primary_provider=AddressProvider.NOMINATIM,
        fallback_providers=[AddressProvider.CENSUS],
        min_quality_threshold=AddressQuality.APPROXIMATE,
    )

    try:
        # Geocode the address
        console.print("🔍 Geocoding...")
        result = geocode_address(address, config)

        if result.success:
            console.print(f"✅ Success! Coordinates: {result.latitude:.6f}, {result.longitude:.6f}")
            console.print(f"📊 Quality: {result.quality.value}")
            console.print(f"🎯 Confidence: {result.confidence_score:.2f}")
            console.print(f"🔧 Provider: {result.provider_used.value}")
            if result.formatted_address:
                console.print(f"📍 Formatted: {result.formatted_address[:80]}...")
        else:
            console.print(f"❌ Failed: {result.error_message}")

    except Exception as e:
        console.print(f"💥 Error: {e}")

    console.print()


def demo_quality_levels():
    """Demonstrate different quality levels."""
    console.print("[bold cyan]Step 2: Understanding Quality Levels[/bold cyan]")
    console.print("Different addresses return different quality levels:\n")

    # Test addresses with different expected quality levels
    test_cases = [
        {
            "address": "1600 Pennsylvania Avenue NW, Washington, DC 20500",
            "expected": "High quality - exact street address",
            "threshold": AddressQuality.EXACT,
        },
        {
            "address": "Washington, DC",
            "expected": "Medium quality - city level",
            "threshold": AddressQuality.CENTROID,
        },
        {
            "address": "North Carolina",
            "expected": "Low quality - state level",
            "threshold": AddressQuality.APPROXIMATE,
        },
    ]

    config = GeocodingConfig(
        primary_provider=AddressProvider.NOMINATIM,
        min_quality_threshold=AddressQuality.APPROXIMATE,  # Accept all for demo
    )

    for i, test in enumerate(test_cases, 1):
        console.print(f"🧪 Test {i}: {test['address']}")
        console.print(f"   Expected: {test['expected']}")

        address = AddressInput(address=test["address"])

        try:
            result = geocode_address(address, config)

            if result.success:
                console.print(
                    f"   ✅ Quality: {result.quality.value} | Coordinates: {result.latitude:.4f}, {result.longitude:.4f}"
                )
            else:
                console.print(f"   ❌ Failed: {result.error_message}")

        except Exception as e:
            console.print(f"   💥 Error: {e}")

        console.print()


def demo_batch_processing():
    """Demonstrate batch address geocoding."""
    console.print("[bold cyan]Step 3: Batch Address Processing[/bold cyan]")
    console.print("Process multiple addresses efficiently:\n")

    # Create sample addresses (North Carolina locations)
    addresses = [
        "100 N Tryon St, Charlotte, NC",
        "301 E Hargett St, Raleigh, NC",
        "120 E Main St, Durham, NC",
        "100 N Greene St, Greensboro, NC",
        "100 Coxe Ave, Asheville, NC",
    ]

    console.print(f"📋 Processing {len(addresses)} addresses:")
    for addr in addresses:
        console.print(f"   • {addr}")
    console.print()

    # Create address inputs
    address_inputs = [
        AddressInput(address=addr, id=f"nc_{i}", source="tutorial_batch")
        for i, addr in enumerate(addresses, 1)
    ]

    # Configure for batch processing
    config = GeocodingConfig(
        primary_provider=AddressProvider.CENSUS,  # Good for US addresses
        fallback_providers=[AddressProvider.NOMINATIM],
        min_quality_threshold=AddressQuality.APPROXIMATE,
        enable_cache=True,
        batch_size=3,
        batch_delay_seconds=0.5,  # Be respectful to free APIs
    )

    try:
        console.print("🔄 Batch geocoding in progress...")
        results = geocode_addresses(address_inputs, config, progress=True)

        # Analyze results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        console.print("\n📊 Batch Results:")
        console.print(
            f"   ✅ Successful: {len(successful)}/{len(results)} ({len(successful) / len(results) * 100:.1f}%)"
        )
        console.print(f"   ❌ Failed: {len(failed)}")

        if successful:
            console.print("\n📍 Successful Geocodes:")
            for result in successful[:3]:  # Show first 3
                console.print(
                    f"   • {result.input_address.address[:40]:<40} → {result.latitude:.4f}, {result.longitude:.4f}"
                )

        return successful

    except Exception as e:
        console.print(f"💥 Batch processing error: {e}")
        return []


def demo_socialmapper_integration(geocoded_results):
    """Demonstrate integration with SocialMapper workflow."""
    console.print("[bold cyan]Step 4: SocialMapper Integration[/bold cyan]")
    console.print("Convert geocoded addresses into SocialMapper analysis:\n")

    if not geocoded_results:
        console.print("❌ No geocoded results available for integration demo")
        return

    # Save geocoded results to CSV for SocialMapper
    output_file = Path("output/tutorial_geocoded_addresses.csv")
    output_file.parent.mkdir(exist_ok=True)

    # Convert to DataFrame
    data = [
        {
            "name": result.input_address.address.split(",")[0],  # Use first part as name
            "latitude": result.latitude,
            "longitude": result.longitude,
            "address": result.input_address.address,
            "quality": result.quality.value,
            "provider": result.provider_used.value,
        }
        for result in geocoded_results
    ]

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)

    console.print(f"💾 Saved {len(data)} addresses to: {output_file}")
    console.print("\n🗺️  Now using with SocialMapper for demographic analysis...")

    try:
        # Use the geocoded addresses with SocialMapper
        with SocialMapperClient() as client:
            config = (
                SocialMapperBuilder()
                .with_custom_pois(str(output_file))
                .with_travel_time(15)
                .with_census_variables("total_population", "median_household_income")
                .with_exports(csv=True, isochrones=False)  # Skip maps for tutorial
                .with_output_directory("output/tutorial_geocoding")
                .build()
            )

            result = client.run_analysis(config)

            if result.is_ok():
                analysis = result.unwrap()
                console.print("✅ SocialMapper Analysis Complete!")
                console.print(f"   📍 Analyzed {analysis.poi_count} geocoded locations")
                console.print(f"   👥 Census data for {analysis.census_units_analyzed} areas")

                if analysis.files_generated:
                    console.print("   📁 Results saved to output/tutorial_geocoding/")
            else:
                error = result.unwrap_err()
                console.print(f"❌ SocialMapper error: {error.message}")

    except Exception as e:
        console.print(f"💥 Integration error: {e}")


def demo_error_handling():
    """Demonstrate error handling and troubleshooting."""
    console.print("[bold cyan]Step 5: Error Handling & Best Practices[/bold cyan]")
    console.print("Learn how to handle common geocoding issues:\n")

    # Test problematic addresses
    problem_addresses = [
        "This is not a real address at all",
        "123 Nonexistent Street, Nowhere, XX 99999",
        "",  # Empty address
        "Paris",  # Ambiguous (Paris, France vs Paris, Texas?)
    ]

    config = GeocodingConfig(
        primary_provider=AddressProvider.NOMINATIM,
        min_quality_threshold=AddressQuality.APPROXIMATE,
        timeout_seconds=5,
        max_retries=1,
    )

    console.print("🧪 Testing problematic addresses:")

    for addr in problem_addresses:
        console.print(f"\n   Testing: '{addr}'")

        if not addr:
            console.print("   ❌ Empty address - skipping")
            continue

        address = AddressInput(address=addr)

        try:
            result = geocode_address(address, config)

            if result.success:
                console.print(
                    f"   ✅ Unexpected success: {result.latitude:.4f}, {result.longitude:.4f}"
                )
                console.print(f"      Quality: {result.quality.value} (verify this is correct!)")
            else:
                console.print(f"   ❌ Failed as expected: {result.error_message}")

        except Exception as e:
            console.print(f"   💥 Exception: {e}")

    console.print("\n💡 Best Practices:")
    console.print("   • Always check result.success before using coordinates")
    console.print("   • Use quality thresholds appropriate for your use case")
    console.print("   • Include fallback providers for reliability")
    console.print("   • Cache results to avoid re-geocoding same addresses")
    console.print("   • Be respectful of API rate limits")


def demo_advanced_tips():
    """Show advanced geocoding tips and configuration."""
    console.print("[bold cyan]Advanced Tips & Configuration[/bold cyan]")
    console.print("Optimize geocoding for your specific needs:\n")

    console.print(Panel(
        """🔧 Custom Configuration Examples:

# High-accuracy US addresses (government/medical)
config = GeocodingConfig(
    primary_provider=AddressProvider.CENSUS,
    min_quality_threshold=AddressQuality.EXACT,
    require_country_match=True,
    default_country='US'
)

# Fast processing for large datasets
config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    fallback_providers=[],  # No fallbacks for speed
    min_quality_threshold=AddressQuality.APPROXIMATE,
    batch_size=10,
    batch_delay_seconds=0.1
)

# International addresses
config = GeocodingConfig(
    primary_provider=AddressProvider.NOMINATIM,
    require_country_match=False,
    timeout_seconds=15,
    max_retries=3
)""",
        title="⚙️ Configuration Patterns",
        border_style="blue",
    ))

    console.print("\n🎯 Use Case Recommendations:")
    console.print("   • Business analysis: Census provider + exact quality")
    console.print("   • Academic research: Nominatim + approximate quality")
    console.print("   • International data: Nominatim only")
    console.print("   • Real-time apps: Enable caching + batch processing")


def main():
    """Run the address geocoding tutorial."""
    console.print(Panel(
        "[bold cyan]Address Geocoding Tutorial[/bold cyan]\nLearn to convert addresses into coordinates for spatial analysis",
        title="🏘️ SocialMapper",
        border_border_style="cyan"
    ))

    try:
        # Educational overview
        explain_geocoding()

        # Step-by-step demos
        demo_single_address()
        demo_quality_levels()
        geocoded_results = demo_batch_processing()
        demo_socialmapper_integration(geocoded_results)
        demo_error_handling()
        demo_advanced_tips()

        # Success summary
        console.print(Panel(
            "[bold green]✅ You've learned to geocode addresses and integrate them with SocialMapper analysis![/bold green]",
            title="🎉 Tutorial Complete!",
            border_style="green"
        ))

        console.print("\n[bold]🎉 What You've Learned:[/bold]")
        console.print("  • Single and batch address geocoding")
        console.print("  • Quality levels and provider selection")
        console.print("  • Error handling and best practices")
        console.print("  • Integration with SocialMapper workflows")
        console.print("  • Advanced configuration options")

        console.print("\n[bold]🚀 Next Steps:[/bold]")
        console.print("  • Try geocoding your own address datasets")
        console.print("  • Experiment with different quality thresholds")
        console.print("  • Compare provider performance for your region")
        console.print("  • Build complete address-to-demographics workflows")
        console.print("  • Explore the address_geocoding.py demo for more examples")

        return 0

    except Exception as e:
        console.print(f"\n[bold red]❌ Tutorial failed: {e}[/bold red]")
        console.print("\n[dim]Check your internet connection and try again.[/dim]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
