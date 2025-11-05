#!/usr/bin/env python3
"""
SocialMapper Quick Start - Zero to Analysis in 2 Minutes

This script demonstrates SocialMapper's capabilities using demo mode.
No API keys or setup required - just run and see results!

Usage:
    python quick_start.py
    python quick_start.py --city "Chapel Hill, NC"
    python quick_start.py --city "Portland, OR" --travel-time 20
    python quick_start.py --full  # Run all examples
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path if running from examples folder
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper import demo


def print_header(text: str, emoji: str = "🔍") -> None:
    """Print a formatted section header."""
    print(f"\n{emoji} {text}")
    print("=" * (len(text) + 4))


def quick_demo(city: str = "Portland, OR", **kwargs) -> dict[str, Any]:
    """
    Run a quick demo analysis for any city.

    Parameters
    ----------
    city : str
        Demo city name (see demo.list_available_demos())
    **kwargs
        Additional parameters for demo.quick_start()

    Returns
    -------
    dict
        Analysis results
    """
    print_header(f"Quick Analysis: {city}", "🚀")

    # Run the analysis
    result = demo.quick_start(city, **kwargs)

    # The demo module already prints formatted output
    # Return result for further processing if needed
    return result


def compare_travel_modes(city: str = "Portland, OR") -> None:
    """
    Compare accessibility across different travel modes.

    Shows how travel mode affects the area and population reached.
    """
    print_header("Travel Mode Comparison", "🚶🚴🚗")

    modes = ["walk", "bike", "drive"]
    results = []

    for mode in modes:
        print(f"\nAnalyzing {mode} mode...")
        result = demo.quick_start(
            city,
            travel_mode=mode,
            travel_time=15
        )
        results.append({
            "mode": mode,
            "area_sq_km": result.get("area_sq_km", 0),
            "population": result.get("total_population", 0),
            "poi_count": result.get("poi_count", 0)
        })

    # Display comparison table
    print("\n" + "─" * 60)
    print(f"{'Mode':<10} {'Area (km²)':<12} {'Population':<12} {'POIs':<8}")
    print("─" * 60)

    for r in results:
        print(f"{r['mode']:<10} {r['area_sq_km']:<12.1f} "
              f"{r['population']:<12,} {r['poi_count']:<8}")

    print("─" * 60)

    # Calculate ratios
    walk_area = results[0]["area_sq_km"]
    bike_area = results[1]["area_sq_km"]
    drive_area = results[2]["area_sq_km"]

    if walk_area > 0:
        print(f"\n📊 Insights:")
        print(f"  • Biking reaches {bike_area/walk_area:.1f}x more area than walking")
        print(f"  • Driving reaches {drive_area/walk_area:.1f}x more area than walking")


def analyze_all_cities() -> None:
    """
    Run analysis for all available demo cities.

    Shows the diversity of results across different urban contexts.
    """
    print_header("All Demo Cities Analysis", "🏙️")

    # Get list of available cities
    cities = ["Portland, OR", "Chapel Hill, NC", "Durham, NC",
              "Atlanta, GA", "Boston, MA"]

    print("\nAnalyzing accessibility across demo cities...\n")

    summary = []

    for city in cities:
        try:
            result = demo.quick_start(
                city,
                travel_time=15,
                travel_mode="walk"
            )

            summary.append({
                "city": city,
                "population": result.get("total_population", 0),
                "libraries": result.get("poi_count", 0),
                "area_sq_km": result.get("area_sq_km", 0),
                "median_income": result.get("median_income", 0)
            })
            print(f"✓ {city}")
        except Exception as e:
            print(f"✗ {city}: {str(e)}")

    # Display summary table
    print("\n" + "─" * 80)
    print(f"{'City':<20} {'Population':<12} {'Libraries':<12} "
          f"{'Area (km²)':<12} {'Income':<12}")
    print("─" * 80)

    for s in summary:
        print(f"{s['city']:<20} {s['population']:<12,} {s['libraries']:<12} "
              f"{s['area_sq_km']:<12.1f} ${s['median_income']:<11,}")

    print("─" * 80)


def explore_poi_categories(city: str = "Portland, OR") -> None:
    """
    Explore different POI categories for accessibility analysis.

    Shows how to analyze different types of community resources.
    """
    print_header("POI Category Exploration", "📍")

    categories = ["library", "grocery", "hospital", "school", "park"]

    print(f"\nAnalyzing different POI types in {city}...\n")

    for category in categories:
        # Note: Current demo doesn't support poi_category parameter
        # Using default POIs for demonstration
        result = demo.quick_start(
            city,
            travel_time=15,
            travel_mode="walk",
            display_results=False
        )

        count = result.get("poi_count", 0)
        emoji = {
            "library": "📚",
            "grocery": "🛒",
            "hospital": "🏥",
            "school": "🏫",
            "park": "🌳"
        }.get(category, "📍")

        print(f"{emoji} {category.capitalize():<12} Found {count} within 15-min walk")

        # Show closest 3
        if result.get("pois"):
            print(f"   Closest 3:")
            for poi in result["pois"][:3]:
                name = poi.get("name", "Unknown")
                dist = poi.get("distance_km", 0)
                print(f"   • {name[:30]:<30} ({dist:.1f} km)")
        print()


def save_results_example(city: str = "Portland, OR") -> None:
    """
    Demonstrate how to save analysis results.

    Shows export to JSON and potential CSV conversion.
    """
    print_header("Saving Results", "💾")

    # Run analysis
    result = demo.quick_start(city)

    # Save to JSON
    output_file = Path("quick_start_results.json")
    with open(output_file, "w") as f:
        # Filter out non-serializable items if any
        clean_result = {
            "location": result.get("location"),
            "travel_time": result.get("travel_time"),
            "travel_mode": result.get("travel_mode"),
            "area_sq_km": result.get("area_sq_km"),
            "poi_count": result.get("poi_count"),
            "total_population": result.get("total_population"),
            "median_income": result.get("median_income"),
            "pois": result.get("pois", [])[:5]  # Just top 5 for example
        }
        json.dump(clean_result, f, indent=2)

    print(f"\n✅ Results saved to: {output_file.absolute()}")
    print(f"   File size: {output_file.stat().st_size} bytes")

    # Show preview of saved data
    print("\n📄 Preview of saved data:")
    print(json.dumps(clean_result, indent=2)[:500] + "...")

    # Suggest next steps
    print("\n💡 Next steps:")
    print("   1. Load in pandas: pd.read_json('quick_start_results.json')")
    print("   2. Share with colleagues")
    print("   3. Use for reports or presentations")


def transition_to_live_data() -> None:
    """
    Show how to transition from demo to live data.

    Educational example showing the API similarity.
    """
    print_header("Transition to Live Data", "🔄")

    print("\nDemo mode is great for learning, but real analysis needs live data.")
    print("\nHere's how the code changes:\n")

    # Show demo code
    print("📚 DEMO MODE (No API key needed):")
    print("-" * 40)
    print("""from socialmapper import demo

result = demo.quick_start("Portland, OR")
print(f"Found {result['poi_count']} libraries")""")

    print("\n\n🌐 LIVE MODE (Requires Census API key):")
    print("-" * 40)
    print("""from socialmapper import create_isochrone, get_poi, get_census_data

# Works with ANY location in the US!
isochrone = create_isochrone("Seattle, WA", travel_time=15)
pois = get_poi("Seattle, WA", categories=["library"])
census = get_census_data(polygon=isochrone)

print(f"Found {len(pois)} libraries")
print(f"Population: {census.total_population:,}")""")

    print("\n\n📋 Key differences:")
    print("  ✓ Demo: Pre-computed data, 5 cities, instant results")
    print("  ✓ Live: Real-time data, any US location, requires API key")
    print("\n  Both use the same analysis concepts and similar APIs!")

    print("\n\n🔑 Get your free Census API key:")
    print("  → https://api.census.gov/data/key_signup.html")


def main():
    """Main entry point for the quick start script."""
    parser = argparse.ArgumentParser(
        description="SocialMapper Quick Start - Zero to Analysis in 2 Minutes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run default Portland demo
  %(prog)s --city "Chapel Hill, NC" # Analyze Chapel Hill
  %(prog)s --travel-time 20         # Use 20-minute travel time
  %(prog)s --travel-mode bike       # Use bike mode
  %(prog)s --full                   # Run all examples
        """
    )

    parser.add_argument(
        "--city",
        default="Portland, OR",
        help="Demo city to analyze (default: Portland, OR)"
    )
    parser.add_argument(
        "--travel-time",
        type=int,
        default=15,
        help="Travel time in minutes (default: 15)"
    )
    parser.add_argument(
        "--travel-mode",
        choices=["walk", "bike", "drive"],
        default="walk",
        help="Travel mode (default: walk)"
    )
    # Note: poi_category not supported in current demo.quick_start()
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run all example analyses"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    print("\n🚀 SocialMapper Quick Start")
    print("━" * 50)
    print("No API keys needed - using demo mode!")

    try:
        if args.full:
            # Run all examples
            quick_demo(args.city, travel_time=args.travel_time)
            compare_travel_modes(args.city)
            explore_poi_categories(args.city)
            analyze_all_cities()
            save_results_example(args.city)
            transition_to_live_data()
        else:
            # Run single analysis
            result = quick_demo(
                args.city,
                travel_time=args.travel_time,
                travel_mode=args.travel_mode
            )

            if args.save:
                save_results_example(args.city)

        print("\n✨ Success! You've completed your first SocialMapper analysis.")
        print("   Ready for more? Try: python quick_start.py --full")
        print("   Or check out the tutorials in examples/tutorials/")

    except KeyboardInterrupt:
        print("\n\n👋 Analysis cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Tips:")
        print("  • Make sure SocialMapper is installed: pip install socialmapper")
        print("  • Check available cities: python -c 'from socialmapper import demo; demo.list_available_demos()'")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())