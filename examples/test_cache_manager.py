#!/usr/bin/env python3
"""Test the cache manager functionality."""

import json as json_lib

from rich.console import Console
from rich.json import JSON
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


def display_cache_stats():
    """Display cache statistics in a formatted table."""
    console.print("\n[bold cyan]SocialMapper Cache Statistics[/bold cyan]\n")

    # Get cache statistics
    stats = get_cache_statistics()

    # Create summary table
    table = Table(title="Cache Summary", show_header=True, header_style="bold magenta")
    table.add_column("Cache Type", style="cyan", width=20)
    table.add_column("Size (MB)", justify="right", style="green")
    table.add_column("Items", justify="right", style="yellow")
    table.add_column("Status", style="blue")
    table.add_column("Location", style="dim")

    for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
        cache_stats = stats[cache_type]
        table.add_row(
            cache_type.replace("_", " ").title(),
            f"{cache_stats.get('size_mb', 0):.2f}",
            str(cache_stats.get('item_count', 0)),
            cache_stats.get('status', 'unknown'),
            cache_stats.get('location', 'N/A')
        )

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{stats['summary']['total_size_mb']:.2f}[/bold]",
        f"[bold]{stats['summary']['total_items']}[/bold]",
        "",
        ""
    )

    console.print(table)

    # Show network cache details if available
    network_stats = stats.get('network_cache', {})
    if network_stats.get('cache_hits') is not None:
        console.print("\n[bold cyan]Network Cache Performance[/bold cyan]")
        perf_table = Table(show_header=False)
        perf_table.add_column("Metric", style="cyan")
        perf_table.add_column("Value", justify="right", style="green")

        perf_table.add_row("Cache Hits", str(network_stats.get('cache_hits', 0)))
        perf_table.add_row("Cache Misses", str(network_stats.get('cache_misses', 0)))
        perf_table.add_row("Hit Rate", f"{network_stats.get('hit_rate_percent', 0):.1f}%")
        perf_table.add_row("Avg Retrieval Time", f"{network_stats.get('avg_retrieval_time_ms', 0):.1f} ms")

        if network_stats.get('total_nodes'):
            perf_table.add_row("Total Nodes", f"{network_stats['total_nodes']:,}")
            perf_table.add_row("Total Edges", f"{network_stats['total_edges']:,}")

        console.print(perf_table)

    return stats


def test_cache_operations():
    """Test various cache operations."""
    console.print(Panel.fit("[bold yellow]Testing Cache Manager Operations[/bold yellow]"))

    # Display initial stats
    console.print("\n[bold]Initial Cache State:[/bold]")
    initial_stats = display_cache_stats()

    # Test cleanup of expired entries
    console.print("\n[bold]Testing Cleanup of Expired Entries:[/bold]")
    cleanup_result = cleanup_expired_cache_entries()
    console.print(JSON(json_lib.dumps(cleanup_result, indent=2)))

    # Test individual cache clearing
    console.print("\n[bold]Testing Individual Cache Clearing:[/bold]")

    # Clear geocoding cache
    console.print("\n- Clearing geocoding cache...")
    result = clear_geocoding_cache()
    if result['success']:
        console.print(f"  [green]✓ Success! Cleared {result['cleared_size_mb']:.2f} MB ({result['cleared_items']} items)[/green]")
    else:
        console.print(f"  [red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")

    # Clear census cache
    console.print("\n- Clearing census cache...")
    result = clear_census_cache()
    if result['success']:
        console.print(f"  [green]✓ Success! Cleared {result['cleared_size_mb']:.2f} MB ({result['cleared_items']} items)[/green]")
    else:
        console.print(f"  [red]✗ Failed: {result.get('error', 'Unknown error')}[/red]")

    # Clear network cache
    console.print("\n- Clearing network cache...")
    try:
        clear_network_cache()
        console.print("  [green]✓ Success! Network cache cleared[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Failed: {e!s}[/red]")

    # Display stats after individual clearing
    console.print("\n[bold]Cache State After Individual Clearing:[/bold]")
    display_cache_stats()

    # Test clear all caches
    console.print("\n[bold]Testing Clear All Caches:[/bold]")
    result = clear_all_caches()

    if result['summary']['success']:
        console.print(f"[green]✓ All caches cleared successfully! Total: {result['summary']['total_cleared_mb']:.2f} MB[/green]")
    else:
        console.print("[red]✗ Some caches failed to clear[/red]")

    # Show detailed results
    console.print("\nDetailed Results:")
    for cache_type, cache_result in result.items():
        if cache_type != 'summary':
            status = "✓" if cache_result.get('success', False) else "✗"
            color = "green" if cache_result.get('success', False) else "red"
            console.print(f"  [{color}]{status} {cache_type}[/{color}]")
            if not cache_result.get('success', False):
                console.print(f"    Error: {cache_result.get('error', 'Unknown')}")

    # Final stats
    console.print("\n[bold]Final Cache State:[/bold]")
    display_cache_stats()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test SocialMapper cache manager")
    parser.add_argument('--stats-only', action='store_true', help='Only show statistics, don\'t test operations')
    args = parser.parse_args()

    if args.stats_only:
        display_cache_stats()
    else:
        test_cache_operations()


if __name__ == "__main__":
    main()
