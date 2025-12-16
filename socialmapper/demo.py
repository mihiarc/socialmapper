"""
Demo module for SocialMapper providing sample data and quick starts.

This module enables users to explore SocialMapper without requiring
Census API keys. It includes pre-generated sample data for major cities
and provides quick-start functions for common use cases.

Examples
--------
>>> from socialmapper import demo
>>> result = demo.quick_start("Portland, OR")
>>> print(f"Found {result['poi_count']} libraries")
>>> print(f"Population: {result['total_population']:,}")

>>> # See what demos are available
>>> demo.list_available_demos()
"""

import json
from pathlib import Path
from typing import Any, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .api_result_types import CensusDataResult
from .constants import DEMO_DISPLAY_LIMIT
from .exceptions import ValidationError

console = Console()

# Directory containing demo data files
DEMO_DATA_DIR = Path(__file__).parent / "data" / "demo"

# Available demo locations
DEMO_LOCATIONS = {
    "Portland, OR": {
        "display_name": "Portland, Oregon",
        "coords": (45.5152, -122.6784),
        "description": "Rose City with excellent library coverage",
    },
    "Chapel Hill, NC": {
        "display_name": "Chapel Hill, North Carolina",
        "coords": (35.9132, -79.0558),
        "description": "College town with strong community amenities",
    },
    "Durham, NC": {
        "display_name": "Durham, North Carolina",
        "coords": (35.9940, -78.8986),
        "description": "Bull City with vibrant food scene",
    },
}


def _load_demo_data(location: str, data_type: str) -> dict[str, Any]:
    """
    Load demo data from JSON files.

    Parameters
    ----------
    location : str
        Location name (e.g., "Portland, OR").
    data_type : str
        Type of data: "isochrone", "census", or "pois".

    Returns
    -------
    dict
        Loaded demo data.

    Raises
    ------
    ValidationError
        If location or data type is not available in demo data.
    """
    if location not in DEMO_LOCATIONS:
        raise ValidationError(
            f"Demo data not available for '{location}'. "
            f"Available: {', '.join(DEMO_LOCATIONS.keys())}"
        )

    # Normalize location name to filename
    location_slug = location.lower().replace(", ", "_").replace(" ", "_")
    filename = f"{location_slug}_{data_type}.json"
    filepath = DEMO_DATA_DIR / filename

    if not filepath.exists():
        raise ValidationError(
            f"Demo data file not found: {filename}. "
            f"Please ensure demo data is properly installed."
        )

    with filepath.open() as f:
        return json.load(f)


def list_available_demos() -> None:
    """
    Display all available demo locations and their features.

    Shows a formatted table of demo cities with descriptions and
    available demo types.

    Examples
    --------
    >>> from socialmapper import demo
    >>> demo.list_available_demos()
    """
    table = Table(title="🗺️  SocialMapper Demo Locations", show_header=True)
    table.add_column("Location", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Available Demos", style="green")

    for loc_info in DEMO_LOCATIONS.values():
        demos = "✓ Libraries  ✓ Food Access  ✓ Quick Start"
        table.add_row(
            loc_info["display_name"],
            loc_info["description"],
            demos,
        )

    console.print(table)
    console.print()
    console.print(
        Panel(
            "[bold cyan]Getting Started[/bold cyan]\n\n"
            "Try a quick start demo:\n"
            "[white]>>> from socialmapper import demo[/white]\n"
            "[white]>>> result = demo.quick_start('Portland, OR')[/white]\n\n"
            "Or explore specific features:\n"
            "[white]>>> demo.show_libraries('Chapel Hill, NC')[/white]\n"
            "[white]>>> demo.show_food_access('Durham, NC')[/white]",
            border_style="blue",
        )
    )


def quick_start(
    location: str = "Portland, OR",
    travel_time: int = 15,
    travel_mode: Literal["drive", "walk", "bike"] = "drive",
) -> dict[str, Any]:
    """
    Run complete accessibility analysis with cached demo data.

    Demonstrates a full SocialMapper workflow without API calls,
    including isochrone generation, POI discovery, and demographic
    analysis.

    Parameters
    ----------
    location : str, optional
        Demo location name. Must be one of the available demo
        locations. Default is "Portland, OR".
    travel_time : int, optional
        Travel time in minutes (5, 10, 15, 20, or 30).
        Default is 15.
    travel_mode : {'drive', 'walk', 'bike'}, optional
        Mode of transportation. Default is 'drive'.

    Returns
    -------
    dict
        Analysis results containing:
        - 'location': Location name
        - 'isochrone': Travel-time polygon data
        - 'poi_count': Number of POIs found
        - 'pois': List of discovered POIs
        - 'total_population': Population in accessible area
        - 'median_income': Median household income
        - 'census_blocks': Census block group data
        - 'area_sq_km': Isochrone area in square kilometers

    Raises
    ------
    ValidationError
        If location is not available in demo data.

    Examples
    --------
    >>> from socialmapper import demo
    >>> result = demo.quick_start("Portland, OR")
    >>> print(f"Found {result['poi_count']} libraries")
    Found 12 libraries

    >>> result = demo.quick_start("Durham, NC", travel_time=20)
    >>> print(f"Population: {result['total_population']:,}")
    Population: 45,234
    """
    _validate_demo_location(location)
    _show_demo_mode_banner(location)

    # Load cached demo data
    isochrone_data = _load_demo_data(location, "isochrone")
    census_data = _load_demo_data(location, "census")
    poi_data = _load_demo_data(location, "pois")

    # Extract relevant travel time data (use 15min as default if not found)
    iso = isochrone_data.get(f"{travel_time}min_{travel_mode}",
                              isochrone_data.get("15min_drive"))

    # Calculate totals from census data
    total_pop = sum(
        block.get("population", 0)
        for block in census_data.get("blocks", [])
    )

    # Calculate median income (weighted average)
    incomes = [
        block.get("median_income", 0)
        for block in census_data.get("blocks", [])
        if block.get("median_income")
    ]
    median_income = int(sum(incomes) / len(incomes)) if incomes else 0

    # Filter POIs by category (libraries for quick start)
    pois = [poi for poi in poi_data.get("pois", [])
            if poi.get("category") == "library"]

    result = {
        "location": location,
        "isochrone": iso,
        "poi_count": len(pois),
        "pois": pois,
        "total_population": total_pop,
        "median_income": median_income,
        "census_blocks": census_data.get("blocks", []),
        "area_sq_km": iso.get("properties", {}).get("area_sq_km", 0),
    }

    _display_quick_start_results(result)
    return result


def show_libraries(
    location: str = "Portland, OR",
    travel_time: int = 15,
) -> dict[str, Any]:
    """
    Demonstrate library accessibility analysis with demo data.

    Shows how to discover and analyze library accessibility in
    a demo location without requiring API keys.

    Parameters
    ----------
    location : str, optional
        Demo location name. Default is "Portland, OR".
    travel_time : int, optional
        Travel time in minutes. Default is 15.

    Returns
    -------
    dict
        Library analysis results containing:
        - 'location': Location name
        - 'library_count': Number of libraries found
        - 'libraries': List of library POIs with details
        - 'population_served': Population within travel time
        - 'people_per_library': Population to library ratio

    Examples
    --------
    >>> from socialmapper import demo
    >>> result = demo.show_libraries("Chapel Hill, NC")
    >>> print(f"{result['library_count']} libraries serve "
    ...       f"{result['population_served']:,} people")
    8 libraries serve 32,145 people
    """
    _validate_demo_location(location)
    _show_demo_mode_banner(location, feature="Library Accessibility")

    # Load demo data
    census_data = _load_demo_data(location, "census")
    poi_data = _load_demo_data(location, "pois")

    # Filter libraries
    libraries = [
        poi for poi in poi_data.get("pois", [])
        if poi.get("category") == "library"
    ]

    # Calculate population
    population = sum(
        block.get("population", 0)
        for block in census_data.get("blocks", [])
    )

    result = {
        "location": location,
        "library_count": len(libraries),
        "libraries": libraries,
        "population_served": population,
        "people_per_library": int(population / len(libraries)) if libraries else 0,
    }

    _display_library_results(result)
    return result


def show_food_access(
    location: str = "Portland, OR",
    travel_time: int = 15,
) -> dict[str, Any]:
    """
    Demonstrate food access analysis with demo data.

    Shows how to analyze grocery store and restaurant accessibility
    in a demo location without requiring API keys.

    Parameters
    ----------
    location : str, optional
        Demo location name. Default is "Portland, OR".
    travel_time : int, optional
        Travel time in minutes. Default is 15.

    Returns
    -------
    dict
        Food access analysis results containing:
        - 'location': Location name
        - 'grocery_count': Number of grocery stores
        - 'restaurant_count': Number of restaurants
        - 'food_pois': All food-related POIs
        - 'population_served': Population within travel time

    Examples
    --------
    >>> from socialmapper import demo
    >>> result = demo.show_food_access("Durham, NC")
    >>> print(f"{result['grocery_count']} grocery stores, "
    ...       f"{result['restaurant_count']} restaurants")
    15 grocery stores, 42 restaurants
    """
    _validate_demo_location(location)
    _show_demo_mode_banner(location, feature="Food Access")

    # Load demo data
    census_data = _load_demo_data(location, "census")
    poi_data = _load_demo_data(location, "pois")

    # Filter food-related POIs
    food_categories = {"grocery", "supermarket", "restaurant", "cafe", "fast_food"}
    food_pois = [
        poi for poi in poi_data.get("pois", [])
        if poi.get("category") in food_categories
    ]

    grocery_stores = [
        poi for poi in food_pois
        if poi.get("category") in {"grocery", "supermarket"}
    ]

    restaurants = [
        poi for poi in food_pois
        if poi.get("category") in {"restaurant", "cafe", "fast_food"}
    ]

    # Calculate population
    population = sum(
        block.get("population", 0)
        for block in census_data.get("blocks", [])
    )

    result = {
        "location": location,
        "grocery_count": len(grocery_stores),
        "restaurant_count": len(restaurants),
        "food_pois": food_pois,
        "population_served": population,
    }

    _display_food_access_results(result)
    return result


def _validate_demo_location(location: str) -> None:
    """
    Validate that location is available in demo data.

    Parameters
    ----------
    location : str
        Location name to validate.

    Raises
    ------
    ValidationError
        If location not in demo data with helpful suggestions.
    """
    if location not in DEMO_LOCATIONS:
        available = ", ".join(DEMO_LOCATIONS.keys())
        raise ValidationError(
            f"Demo data not available for '{location}'.\n"
            f"Available demo locations: {available}\n\n"
            f"To use live data with your own location, set up a Census API key:\n"
            f"1. Get a free key at https://api.census.gov/data/key_signup.html\n"
            f"2. Set CENSUS_API_KEY environment variable\n"
            f"3. Use the main SocialMapper API functions"
        )


def _show_demo_mode_banner(location: str, feature: str = "Quick Start") -> None:
    """
    Display banner indicating demo mode is active.

    Parameters
    ----------
    location : str
        Location name being demoed.
    feature : str, optional
        Feature being demonstrated. Default is "Quick Start".
    """
    console.print()
    console.print(
        Panel(
            f"[bold yellow]🎭 Demo Mode[/bold yellow]\n\n"
            f"[white]Location:[/white] {location}\n"
            f"[white]Feature:[/white] {feature}\n\n"
            f"[dim]Using cached sample data. No API keys required!\n"
            f"To use live data, configure your Census API key.[/dim]",
            border_style="yellow",
        )
    )
    console.print()


def _display_quick_start_results(result: dict[str, Any]) -> None:
    """
    Display formatted results for quick_start demo.

    Parameters
    ----------
    result : dict
        Quick start analysis results.
    """
    console.print("[bold green]✓ Analysis Complete![/bold green]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📍 Location", result["location"])
    table.add_row("📚 Libraries Found", str(result["poi_count"]))
    table.add_row("👥 Total Population", f"{result['total_population']:,}")
    table.add_row("💰 Median Income", f"${result['median_income']:,}")
    table.add_row("📏 Area Coverage", f"{result['area_sq_km']:.1f} km²")
    table.add_row("🏘️  Census Blocks", str(len(result["census_blocks"])))

    console.print(table)
    console.print()
    console.print(
        "[dim]Tip: Access detailed data via result['pois'], "
        "result['census_blocks'], etc.[/dim]\n"
    )


def _display_library_results(result: dict[str, Any]) -> None:
    """
    Display formatted results for library demo.

    Parameters
    ----------
    result : dict
        Library analysis results.
    """
    console.print("[bold green]✓ Library Analysis Complete![/bold green]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📍 Location", result["location"])
    table.add_row("📚 Libraries Found", str(result["library_count"]))
    table.add_row("👥 Population Served", f"{result['population_served']:,}")
    table.add_row(
        "📊 People per Library",
        f"{result['people_per_library']:,}"
    )

    console.print(table)
    console.print()

    if result["libraries"]:
        console.print("[bold]Sample Libraries:[/bold]")
        for lib in result["libraries"][:DEMO_DISPLAY_LIMIT]:
            name = lib.get("name", "Unknown Library")
            distance = lib.get("distance_km", 0)
            console.print(f"  • {name} ({distance:.1f} km)")

        if len(result["libraries"]) > DEMO_DISPLAY_LIMIT:
            console.print(f"  [dim]... and {len(result['libraries']) - DEMO_DISPLAY_LIMIT} more[/dim]")

    console.print()


def _display_food_access_results(result: dict[str, Any]) -> None:
    """
    Display formatted results for food access demo.

    Parameters
    ----------
    result : dict
        Food access analysis results.
    """
    console.print("[bold green]✓ Food Access Analysis Complete![/bold green]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📍 Location", result["location"])
    table.add_row("🛒 Grocery Stores", str(result["grocery_count"]))
    table.add_row("🍽️  Restaurants", str(result["restaurant_count"]))
    table.add_row("👥 Population Served", f"{result['population_served']:,}")

    console.print(table)
    console.print()


def get_demo_isochrone(
    location: str,
    travel_time: int = 15,
    travel_mode: str = "drive"
) -> dict[str, Any]:
    """
    Get pre-generated isochrone from demo data.

    Returns a GeoJSON Feature representing a travel-time polygon
    from cached demo data.

    Parameters
    ----------
    location : str
        Demo location name.
    travel_time : int, optional
        Travel time in minutes (5, 10, 15, 20, or 30).
        Default is 15.
    travel_mode : str, optional
        Mode of transportation. Default is "drive".

    Returns
    -------
    dict
        GeoJSON Feature with isochrone geometry and properties.

    Examples
    --------
    >>> from socialmapper import demo
    >>> iso = demo.get_demo_isochrone("Portland, OR", travel_time=20)
    >>> iso['properties']['travel_time']
    20
    """
    _validate_demo_location(location)

    isochrone_data = _load_demo_data(location, "isochrone")
    key = f"{travel_time}min_{travel_mode}"

    if key not in isochrone_data:
        # Fallback to 15min_drive
        key = "15min_drive"
        console.print(
            f"[yellow]Note: Using 15min drive isochrone as "
            f"{travel_time}min {travel_mode} not available in demo data[/yellow]"
        )

    return isochrone_data[key]


def get_demo_census_data(location: str) -> CensusDataResult:
    """
    Get pre-loaded census data from demo data.

    Returns census demographic data for block groups in the demo
    location area.

    Parameters
    ----------
    location : str
        Demo location name.

    Returns
    -------
    CensusDataResult
        Structured census data result with demographics.

    Examples
    --------
    >>> from socialmapper import demo
    >>> census = demo.get_demo_census_data("Chapel Hill, NC")
    >>> len(census.data)
    25
    """
    _validate_demo_location(location)

    census_data = _load_demo_data(location, "census")

    # Convert to expected format
    data_dict = {}
    for block in census_data.get("blocks", []):
        geoid = block.get("geoid")
        if geoid:
            data_dict[geoid] = {
                "population": block.get("population", 0),
                "median_income": block.get("median_income", 0),
                "median_age": block.get("median_age", 0),
            }

    return CensusDataResult(
        data=data_dict,
        location_type="polygon",
        query_info={
            "year": 2023,
            "source": "demo_data",
            "location": location,
        }
    )
