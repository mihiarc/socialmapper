#!/usr/bin/env python3
"""Example usage of the POI categorization system."""

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from socialmapper.poi_categorization import (
    categorize_poi,
    get_poi_category_info,
    organize_pois_by_category,
)

console = Console()


def main():
    """Demonstrate POI categorization functionality."""

    # Example POIs from OpenStreetMap
    sample_pois = [
        {
            "id": 1234567,
            "type": "node",
            "lat": 35.9132,
            "lon": -79.0558,
            "tags": {
                "amenity": "restaurant",
                "cuisine": "italian",
                "name": "Luigi's Italian Restaurant"
            }
        },
        {
            "id": 2345678,
            "type": "node",
            "lat": 35.9145,
            "lon": -79.0572,
            "tags": {
                "shop": "supermarket",
                "brand": "Whole Foods",
                "name": "Whole Foods Market"
            }
        },
        {
            "id": 3456789,
            "type": "way",
            "lat": 35.9108,
            "lon": -79.0593,
            "tags": {
                "leisure": "park",
                "name": "Forest Hills Park",
                "access": "yes"
            }
        },
        {
            "id": 4567890,
            "type": "node",
            "lat": 35.9119,
            "lon": -79.0545,
            "tags": {
                "amenity": "pharmacy",
                "name": "CVS Pharmacy",
                "healthcare": "pharmacy"
            }
        },
        {
            "id": 5678901,
            "type": "node",
            "lat": 35.9127,
            "lon": -79.0561,
            "tags": {
                "amenity": "bank",
                "brand": "Wells Fargo",
                "name": "Wells Fargo Bank"
            }
        },
        {
            "id": 6789012,
            "type": "node",
            "lat": 35.9101,
            "lon": -79.0589,
            "tags": {
                "amenity": "cafe",
                "name": "The Daily Grind",
                "cuisine": "coffee_shop"
            }
        },
        {
            "id": 7890123,
            "type": "way",
            "lat": 35.9155,
            "lon": -79.0541,
            "tags": {
                "amenity": "school",
                "name": "Chapel Hill High School",
                "operator": "Orange County Schools"
            }
        },
        {
            "id": 8901234,
            "type": "node",
            "lat": 35.9138,
            "lon": -79.0567,
            "tags": {
                "tourism": "hotel",
                "name": "The Carolina Inn",
                "stars": "4"
            }
        }
    ]

    console.print("[bold blue]POI Categorization Example[/bold blue]\n")

    # Show individual categorization
    console.print("[yellow]Individual POI Categorization:[/yellow]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("POI Name", style="cyan", width=30)
    table.add_column("OSM Tags", style="green")
    table.add_column("Category", style="yellow")

    for poi in sample_pois:
        name = poi["tags"].get("name", "Unnamed")
        # Format tags for display
        tags_str = ", ".join([f"{k}={v}" for k, v in poi["tags"].items() if k != "name"][:2])
        category = categorize_poi(poi["tags"])
        table.add_row(name, tags_str, category)

    console.print(table)

    # Organize POIs by category
    console.print("\n[yellow]POIs Organized by Category:[/yellow]")
    categorized = organize_pois_by_category(sample_pois)

    tree = Tree("[bold]Categories[/bold]")
    for category, pois in sorted(categorized.items()):
        category_branch = tree.add(f"[magenta]{category}[/magenta] ({len(pois)} POIs)")
        for poi in pois:
            name = poi["tags"].get("name", "Unnamed")
            poi_type = poi["tags"].get("amenity") or poi["tags"].get("shop") or poi["tags"].get("leisure") or poi["tags"].get("tourism")
            category_branch.add(f"[cyan]{name}[/cyan] [dim]({poi_type})[/dim]")

    console.print(tree)

    # Show category information
    console.print("\n[yellow]Category Information:[/yellow]")
    info = get_poi_category_info()

    info_table = Table(show_header=True, header_style="bold magenta")
    info_table.add_column("Category", style="cyan")
    info_table.add_column("Total Values", justify="right")
    info_table.add_column("Example Values", style="green")

    for category in sorted(info["categories"]):
        details = info["category_details"][category]
        examples = ", ".join(details["sample_values"])
        info_table.add_row(category, str(details["value_count"]), examples)

    console.print(info_table)
    console.print(f"\n[dim]Total categories: {info['total_categories']}[/dim]")


if __name__ == "__main__":
    main()
