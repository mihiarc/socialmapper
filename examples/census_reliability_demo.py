#!/usr/bin/env python3
"""Example demonstrating reliable census data fetching with SocialMapper.

This example shows how to use the enhanced census API client with:
- Circuit breaker for fault tolerance
- Request deduplication
- Comprehensive metrics
- Caching strategies
- Rate limiting
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from socialmapper import SocialMapperBuilder
from socialmapper.census.infrastructure import create_census_system


def main():
    """Demonstrate reliable census data fetching."""
    console = Console()
    
    # Display header
    console.print(Panel.fit(
        "🏛️ Census API Reliability Demo with SocialMapper",
        style="bold blue"
    ))
    
    # Check for API key
    if not os.getenv("CENSUS_API_KEY"):
        console.print("[red]❌ Please set CENSUS_API_KEY environment variable[/red]")
        console.print("Get a free key at: https://api.census.gov/data/key_signup.html")
        return
    
    # Create enhanced census system
    console.print("\n[bold]Creating Enhanced Census System[/bold]")
    census_system = create_census_system(
        enhanced=True,
        cache_type="hybrid",
        rate_limit_requests_per_minute=60,
        adaptive_rate_limiting=True,
        max_retries=3,
        api_timeout_seconds=30,
    )
    
    console.print("✓ Census system created with:")
    console.print("  - Circuit breaker protection")
    console.print("  - Request deduplication")
    console.print("  - Hybrid caching (memory + disk)")
    console.print("  - Adaptive rate limiting")
    console.print("  - Connection pooling")
    
    # Example 1: Basic SocialMapper analysis with Raleigh, NC
    console.print("\n[bold]Example 1: Basic Analysis for Raleigh Libraries[/bold]")
    
    try:
        analysis = (
            SocialMapperBuilder()
            .location("Raleigh, NC")
            .poi_type("amenity")
            .poi_name("library")
            .travel_time(15)
            .travel_mode("drive")
            .geographic_unit("bg")  # Block groups
            .build()
            .analyze()
        )
        
        if analysis.successful:
            results = analysis.results
            console.print(f"✓ Found {results.poi_count} libraries")
            console.print(f"✓ Analyzed {results.census_units_analyzed} block groups")
            console.print(f"✓ Total population within 15-min drive: {results.total_population:,}")
            
            # Display sample demographic data
            if results.census_data:
                display_demographic_summary(console, results.census_data[:5])
        else:
            console.print(f"[red]✗ Analysis failed: {analysis.error}[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    
    # Example 2: Demonstrating caching efficiency
    console.print("\n[bold]Example 2: Cache Efficiency Demo[/bold]")
    
    # First request (cache miss)
    console.print("Making first request (will hit API)...")
    client = census_system["client"]
    
    import time
    start = time.time()
    data1 = client.get_census_data(
        variables=["B01003_001E"],  # Total population
        geography="tract:*",
        year=2022,
        dataset="acs/acs5",
        **{"in": "state:37 county:183"}  # Wake County
    )
    time1 = time.time() - start
    console.print(f"✓ First request took {time1:.2f}s (cache miss)")
    
    # Second request (cache hit)
    console.print("Making same request again (will hit cache)...")
    start = time.time()
    data2 = client.get_census_data(
        variables=["B01003_001E"],
        geography="tract:*", 
        year=2022,
        dataset="acs/acs5",
        **{"in": "state:37 county:183"}
    )
    time2 = time.time() - start
    console.print(f"✓ Second request took {time2:.2f}s (cache hit)")
    console.print(f"✓ Speed improvement: {time1/time2:.1f}x faster")
    
    # Example 3: Display comprehensive metrics
    console.print("\n[bold]Example 3: API Performance Metrics[/bold]")
    
    metrics = client.get_metrics_summary()
    
    # Create metrics table
    metrics_table = Table(title="Census API Performance")
    metrics_table.add_column("Category", style="cyan")
    metrics_table.add_column("Metric", style="white")
    metrics_table.add_column("Value", style="green")
    
    # Add metrics rows
    metrics_table.add_row(
        "Requests",
        "Total",
        str(metrics["requests"]["total"])
    )
    metrics_table.add_row(
        "Requests",
        "Success Rate",
        metrics["requests"]["success_rate"]
    )
    metrics_table.add_row(
        "Performance",
        "Avg Response Time",
        metrics["performance"]["average_response_time"]
    )
    metrics_table.add_row(
        "Cache",
        "Hit Rate",
        metrics["cache"]["hit_rate"]
    )
    metrics_table.add_row(
        "Circuit Breaker",
        "State",
        metrics["circuit_breaker"]["state"]
    )
    metrics_table.add_row(
        "Circuit Breaker",
        "Failures",
        str(metrics["circuit_breaker"]["failure_count"])
    )
    
    console.print(metrics_table)
    
    # Example 4: Batch processing demonstration
    console.print("\n[bold]Example 4: Batch Processing[/bold]")
    
    # Get sample block group IDs from previous data
    sample_geoids = []
    if data1 and len(data1) > 1:
        for row in data1[1:11]:  # First 10 tracts
            if row[0]:  # GEO_ID
                geoid = row[0].split("US")[-1] if "US" in row[0] else row[0]
                # Convert tract to block group pattern
                sample_geoids.extend([f"{geoid}1", f"{geoid}2", f"{geoid}3"])
    
    if sample_geoids:
        console.print(f"Processing {len(sample_geoids)} block groups in batches...")
        
        batch_data = client.get_census_data_batch(
            geoids=sample_geoids[:15],  # First 15
            variables=["B01003_001E", "B19013_001E"],
            year=2022,
            dataset="acs/acs5",
            batch_size=5,
        )
        
        if batch_data:
            console.print(f"✓ Batch processing complete: {len(batch_data)} rows retrieved")
    
    # Final summary
    console.print("\n[bold]Session Summary[/bold]")
    final_metrics = client.get_metrics_summary()
    
    console.print(Panel(
        f"[green]Total API Calls:[/green] {final_metrics['requests']['total']}\n"
        f"[green]Cache Hit Rate:[/green] {final_metrics['cache']['hit_rate']}\n"
        f"[green]Average Response:[/green] {final_metrics['performance']['average_response_time']}\n"
        f"[green]Circuit Breaker:[/green] {final_metrics['circuit_breaker']['state']}\n"
        f"[green]Uptime:[/green] {final_metrics['uptime']}",
        title="Performance Summary",
        style="green",
    ))


def display_demographic_summary(console: Console, census_data: list):
    """Display demographic summary table."""
    table = Table(title="Sample Demographic Data")
    table.add_column("Block Group", style="cyan")
    table.add_column("Population", style="white", justify="right")
    table.add_column("Median Income", style="green", justify="right")
    
    for item in census_data:
        # Extract data safely
        geoid = item.get("GEO_ID", "").split("US")[-1] if item.get("GEO_ID") else "Unknown"
        population = item.get("B01003_001E", "N/A")
        income = item.get("B19013_001E", "N/A")
        
        # Format income
        if income not in ["N/A", None, "-666666666"]:
            try:
                income = f"${int(income):,}"
            except (ValueError, TypeError):
                income = "N/A"
        else:
            income = "N/A"
        
        # Format population
        if population not in ["N/A", None]:
            try:
                population = f"{int(population):,}"
            except (ValueError, TypeError):
                population = "N/A"
        
        table.add_row(geoid[-12:], population, income)
    
    console.print(table)


if __name__ == "__main__":
    main()