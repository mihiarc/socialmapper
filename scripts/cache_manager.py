#!/usr/bin/env python3
"""Standalone cache management script for SocialMapper."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import socialmapper
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from socialmapper.cache_manager import (
    cleanup_expired_cache_entries,
    clear_all_caches,
    clear_census_cache,
    clear_geocoding_cache,
    get_cache_statistics,
)
from socialmapper.isochrone import clear_network_cache

console = Console()


def show_stats():
    """Display cache statistics."""
    console.print("\n[bold cyan]SocialMapper Cache Statistics[/bold cyan]\n")

    # Get cache statistics
    stats = get_cache_statistics()

    # Create summary table
    table = Table(title="Cache Summary", show_header=True, header_style="bold magenta")
    table.add_column("Cache Type", style="cyan", width=20)
    table.add_column("Size (MB)", justify="right", style="green")
    table.add_column("Items", justify="right", style="yellow")
    table.add_column("Status", style="blue")

    for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
        cache_stats = stats[cache_type]
        table.add_row(
            cache_type.replace("_", " ").title(),
            f"{cache_stats.get('size_mb', 0):.2f}",
            str(cache_stats.get("item_count", 0)),
            cache_stats.get("status", "unknown"),
        )

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{stats['summary']['total_size_mb']:.2f}[/bold]",
        f"[bold]{stats['summary']['total_items']}[/bold]",
        "",
    )

    console.print(table)

    # Show network cache performance if available
    network_stats = stats.get("network_cache", {})
    if network_stats.get("cache_hits") is not None and network_stats.get("cache_hits", 0) > 0:
        console.print("\n[bold cyan]Network Cache Performance[/bold cyan]")
        perf_table = Table(show_header=False)
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", justify="right", style="green")

        perf_table.add_row("Cache Hits", str(network_stats.get("cache_hits", 0)))
        perf_table.add_row("Cache Misses", str(network_stats.get("cache_misses", 0)))
        perf_table.add_row("Hit Rate", f"{network_stats.get('hit_rate_percent', 0):.1f}%")
        perf_table.add_row(
            "Avg Retrieval Time", f"{network_stats.get('avg_retrieval_time_ms', 0):.1f} ms"
        )

        console.print(perf_table)


def clear_cache(args):
    """Clear specified caches."""

    # Confirm action if not --yes
    if not args.yes:
        if args.all:
            message = "Are you sure you want to clear ALL caches? (y/N): "
        else:
            caches = []
            if args.network:
                caches.append("network")
            if args.geocoding:
                caches.append("geocoding")
            if args.census:
                caches.append("census")
            message = f"Are you sure you want to clear {', '.join(caches)} cache(s)? (y/N): "

        response = input(message)
        if response.lower() != "y":
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    # Clear caches
    if args.all:
        console.print("\n[bold]Clearing all caches...[/bold]")
        result = clear_all_caches()

        if result["summary"]["success"]:
            console.print(
                f"[green]✓ All caches cleared successfully! Total: {result['summary']['total_cleared_mb']:.2f} MB[/green]"
            )

            # Show details
            for cache_type, cache_result in result.items():
                if cache_type != "summary" and cache_result.get("success", False):
                    cleared_mb = cache_result.get("cleared_size_mb", 0)
                    console.print(f"  • {cache_type}: {cleared_mb:.2f} MB")
        else:
            console.print("[red]✗ Some caches failed to clear[/red]")
            for cache_type, cache_result in result.items():
                if cache_type != "summary" and not cache_result.get("success", False):
                    console.print(f"  • {cache_type}: {cache_result.get('error', 'Unknown error')}")
    else:
        # Clear individual caches
        if args.network:
            console.print("\n[bold]Clearing network cache...[/bold]")
            try:
                clear_network_cache()
                console.print("[green]✓ Network cache cleared successfully![/green]")
            except Exception as e:
                console.print(f"[red]✗ Failed to clear network cache: {e}[/red]")

        if args.geocoding:
            console.print("\n[bold]Clearing geocoding cache...[/bold]")
            result = clear_geocoding_cache()
            if result["success"]:
                console.print(
                    f"[green]✓ Geocoding cache cleared! ({result['cleared_size_mb']:.2f} MB)[/green]"
                )
            else:
                console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")

        if args.census:
            console.print("\n[bold]Clearing census cache...[/bold]")
            result = clear_census_cache()
            if result["success"]:
                console.print(
                    f"[green]✓ Census cache cleared! ({result['cleared_size_mb']:.2f} MB)[/green]"
                )
            else:
                console.print(f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")


def show_details():
    """Show detailed cache information."""
    stats = get_cache_statistics()

    console.print(Panel.fit("[bold cyan]Detailed Cache Information[/bold cyan]"))

    # Show JSON representation with syntax highlighting
    console.print("\n[bold]Full Statistics:[/bold]")
    import json

    console.print(json.dumps(stats, indent=2, default=str))

    # Show cache locations
    console.print("\n[bold]Cache Locations:[/bold]")
    for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
        cache_data = stats.get(cache_type, {})
        location = cache_data.get("location", "Unknown")
        console.print(f"  • {cache_type.replace('_', ' ').title()}: {location}")

    # Show age information
    console.print("\n[bold]Cache Age:[/bold]")
    for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
        cache_data = stats.get(cache_type, {})
        oldest = cache_data.get("oldest_entry", "N/A")
        newest = cache_data.get("newest_entry", "N/A")
        if oldest != "N/A" or newest != "N/A":
            console.print(f"  • {cache_type.replace('_', ' ').title()}:")
            if oldest != "N/A":
                console.print(f"    Oldest: {oldest}")
            if newest != "N/A":
                console.print(f"    Newest: {newest}")


def main():
    parser = argparse.ArgumentParser(
        description="SocialMapper Cache Manager - Manage application caches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Stats command
    subparsers.add_parser("stats", help="Display cache statistics")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear specified caches")
    clear_parser.add_argument("-n", "--network", action="store_true", help="Clear network cache")
    clear_parser.add_argument(
        "-g", "--geocoding", action="store_true", help="Clear geocoding cache"
    )
    clear_parser.add_argument("-c", "--census", action="store_true", help="Clear census cache")
    clear_parser.add_argument("-a", "--all", action="store_true", help="Clear all caches")
    clear_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # Details command
    subparsers.add_parser("details", help="Show detailed cache information")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up expired cache entries")

    args = parser.parse_args()

    if args.command is None:
        # Default to showing stats
        show_stats()
    elif args.command == "stats":
        show_stats()
    elif args.command == "clear":
        if not any([args.network, args.geocoding, args.census, args.all]):
            console.print(
                "[red]Error: No cache specified. Use --network, --geocoding, --census, or --all[/red]"
            )
            sys.exit(1)
        clear_cache(args)
    elif args.command == "details":
        show_details()
    elif args.command == "cleanup":
        console.print("\n[bold]Cleaning up expired cache entries...[/bold]\n")
        result = cleanup_expired_cache_entries()

        for cache_type, cleanup_result in result.items():
            if cleanup_result.get("success", False):
                console.print(
                    f"[green]✓ {cache_type}:[/green] {cleanup_result.get('message', 'Cleaned')}"
                )
                if "removed_entries" in cleanup_result:
                    console.print(f"  Removed {cleanup_result['removed_entries']} expired entries")
            else:
                console.print(f"[red]✗ {cache_type}:[/red] {cleanup_result.get('error', 'Failed')}")


if __name__ == "__main__":
    main()
