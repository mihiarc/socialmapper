#!/usr/bin/env python3
"""
OSMnx 2.0+ Features Demo for SocialMapper
========================================

Showcasing cutting-edge geospatial capabilities with OSMnx 2.0.3
- Faster performance & memory efficiency  
- Enhanced geometries module
- Improved intersection consolidation
- Better type annotations & error handling
- Advanced network analysis features

Author: SocialMapper Team
Date: June 2025
"""

import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track
from rich import print as rprint

console = Console()

def print_header(title: str, emoji: str = "🚀"):
    """Print a beautiful header using Rich."""
    console.print(Panel(f"{emoji} {title}", style="bold blue"))

def print_demo_step(step: int, total: int, description: str):
    """Print demo step with progress."""
    console.print(f"\n[bold green]Step {step}/{total}:[/bold green] {description}")

def benchmark_function(func, *args, **kwargs):
    """Benchmark a function and return result with timing."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def demo_osmnx_performance():
    """Demo OSMnx 2.0 performance improvements."""
    print_demo_step(1, 8, "🚀 Performance & Memory Efficiency")
    
    # Test with a medium-sized city
    place_name = "Corvallis, Oregon, USA"
    
    console.print(f"[yellow]Testing with {place_name}...[/yellow]")
    
    # Benchmark graph download and creation
    console.print("⏱️ Downloading and creating graph...")
    graph, download_time = benchmark_function(
        ox.graph_from_place, 
        place_name, 
        network_type="drive",
        simplify=True  # OSMnx 2.0 has improved simplification
    )
    
    console.print(f"✅ Graph created in {download_time:.2f}s")
    console.print(f"📊 Nodes: {graph.number_of_nodes():,}, Edges: {graph.number_of_edges():,}")
    
    # Test intersection consolidation (major OSMnx 2.0 feature)
    console.print("\n🔗 Testing intersection consolidation...")
    try:
        consolidated_graph, consolidation_time = benchmark_function(
            ox.consolidate_intersections,
            graph,
            tolerance=2,  # 2-meter tolerance for grouping nearby intersections
            rebuild_graph=True
        )
        
        console.print(f"✅ Consolidation completed in {consolidation_time:.2f}s")
        node_reduction = graph.number_of_nodes() - consolidated_graph.number_of_nodes()
        if node_reduction > 0:
            console.print(f"📉 Reduced from {graph.number_of_nodes():,} to {consolidated_graph.number_of_nodes():,} nodes ({node_reduction:,} consolidated)")
        else:
            console.print(f"📊 Network already well-simplified: {graph.number_of_nodes():,} nodes")
            consolidated_graph = graph  # Use original if no consolidation occurred
    except Exception as e:
        console.print(f"⚠️ Consolidation skipped: {e}")
        consolidated_graph = graph
    
    return graph, consolidated_graph

def demo_geometries_module():
    """Demo the powerful new geometries module."""
    print_demo_step(2, 8, "🗺️ Enhanced Geometries Module")
    
    place_name = "Corvallis, Oregon, USA"
    
    # Get multiple types of geometries in one go (OSMnx 2.0 feature)
    console.print("📦 Downloading multiple geometry types...")
    
    # Download POIs (amenities)
    pois, poi_time = benchmark_function(
        ox.features_from_place,
        place_name,
        tags={'amenity': ['library', 'school', 'hospital', 'restaurant']}
    )
    
    # Download building footprints  
    buildings, building_time = benchmark_function(
        ox.features_from_place,
        place_name,
        tags={'building': True}
    )
    
    # Download parks and green spaces
    parks, parks_time = benchmark_function(
        ox.features_from_place,
        place_name,
        tags={'leisure': ['park', 'playground'], 'landuse': 'recreation_ground'}
    )
    
    # Create summary table
    table = Table(title="🏗️ Downloaded Geometries")
    table.add_column("Feature Type", style="cyan")
    table.add_column("Count", style="magenta", justify="right")
    table.add_column("Download Time", style="green", justify="right")
    
    table.add_row("POIs (Amenities)", f"{len(pois):,}", f"{poi_time:.2f}s")
    table.add_row("Building Footprints", f"{len(buildings):,}", f"{building_time:.2f}s") 
    table.add_row("Parks & Green Spaces", f"{len(parks):,}", f"{parks_time:.2f}s")
    
    console.print(table)
    
    return pois, buildings, parks

def demo_network_analysis():
    """Demo advanced network analysis features.""" 
    print_demo_step(3, 8, "🧮 Advanced Network Analysis")
    
    place_name = "Corvallis, Oregon, USA"
    
    # Get a pedestrian network (OSMnx 2.0 has better network type handling)
    console.print("🚶 Creating pedestrian network...")
    G_walk = ox.graph_from_place(place_name, network_type="walk")
    
    # Calculate advanced centrality measures
    console.print("📊 Calculating network centralities...")
    
    # Betweenness centrality (identifies important connector nodes)
    betweenness, bet_time = benchmark_function(
        nx.betweenness_centrality, G_walk, k=100  # Sample for speed
    )
    
    # Closeness centrality (identifies accessible nodes)
    closeness, close_time = benchmark_function(
        nx.closeness_centrality, G_walk
    )
    
    # Calculate street orientation entropy (OSMnx specialty) 
    console.print("🧭 Calculating street orientation entropy...")
    try:
        G_walk_with_bearings = ox.bearing.add_edge_bearings(G_walk)
        # Check what attributes are available
        edge_attrs = list(G_walk_with_bearings.edges(data=True))[0][2].keys() if G_walk_with_bearings.edges() else []
        console.print(f"   Available edge attributes: {list(edge_attrs)}")
        
        # Use available bearing attribute or fallback
        if 'bearing' in edge_attrs:
            bearings = [data['bearing'] for u, v, data in G_walk_with_bearings.edges(data=True) if 'bearing' in data]
            orientation_entropy = ox.bearing.orientation_entropy(bearings) if bearings else 0.0
        else:
            orientation_entropy = 0.0  # Fallback if bearing calculation fails
    except Exception as e:
        console.print(f"   [yellow]Bearing calculation skipped: {e}[/yellow]")
        orientation_entropy = 0.0
    
    console.print(f"📈 Network Analysis Results:")
    console.print(f"   • Nodes: {G_walk.number_of_nodes():,}")
    console.print(f"   • Edges: {G_walk.number_of_edges():,}")
    console.print(f"   • Orientation Entropy: {orientation_entropy:.4f}")
    console.print(f"   • Betweenness calculation: {bet_time:.2f}s")
    console.print(f"   • Closeness calculation: {close_time:.2f}s")
    
    return G_walk, betweenness, closeness, orientation_entropy

def demo_routing_features():
    """Demo enhanced routing capabilities."""
    print_demo_step(4, 8, "🗺️ Enhanced Routing Features")
    
    place_name = "Corvallis, Oregon, USA"
    G = ox.graph_from_place(place_name, network_type="drive")
    
    # Get some random nodes for routing demo
    nodes = list(G.nodes())
    origin = nodes[0]
    destination = nodes[len(nodes)//2]
    
    console.print(f"🎯 Routing from node {origin} to {destination}...")
    
    # Multiple routing algorithms
    routing_methods = [
        ("Shortest Path (Length)", nx.shortest_path, {"weight": "length"}),
        ("Fastest Path (Time)", nx.shortest_path, {"weight": "travel_time"}),
        ("Dijkstra", nx.dijkstra_path, {"weight": "length"})
    ]
    
    routes = {}
    
    # Add travel times to edges (OSMnx 2.0 makes this easier)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    for name, func, kwargs in routing_methods:
        try:
            route, route_time = benchmark_function(func, G, origin, destination, **kwargs)
            routes[name] = {"path": route, "time": route_time}
            console.print(f"   • {name}: {len(route)} nodes, calculated in {route_time:.4f}s")
        except nx.NetworkXNoPath:
            console.print(f"   • {name}: No path found")
    
    return G, routes

def demo_spatial_analysis():
    """Demo spatial analysis capabilities."""
    print_demo_step(5, 8, "📍 Spatial Analysis & Isochrones")
    
    place_name = "Corvallis, Oregon, USA"
    
    # Get POIs for isochrone analysis
    pois = ox.features_from_place(place_name, tags={'amenity': 'library'})
    
    if len(pois) > 0:
        # Get the first library
        library = pois.iloc[0]
        
        if hasattr(library.geometry, 'centroid'):
            library_point = library.geometry.centroid
        else:
            library_point = library.geometry
            
        console.print(f"📚 Analyzing accessibility from library: {library.get('name', 'Unknown')}")
        
        # Create isochrones (15-minute walk)
        G_walk = ox.graph_from_place(place_name, network_type="walk")
        
        # Find nearest node to library
        library_node = ox.distance.nearest_nodes(
            G_walk, 
            library_point.x, 
            library_point.y
        )
        
        # Calculate 15-minute isochrone
        console.print("⏱️ Calculating 15-minute walking isochrone...")
        
        # Add walking speeds and times
        G_walk = ox.add_edge_speeds(G_walk)
        G_walk = ox.add_edge_travel_times(G_walk)
        
        # Get subgraph within 15 minutes (900 seconds)
        isochrone_graph = nx.ego_graph(
            G_walk, 
            library_node, 
            radius=900, 
            distance="travel_time"
        )
        
        console.print(f"🎯 Isochrone Results:")
        console.print(f"   • Reachable nodes: {isochrone_graph.number_of_nodes():,}")
        console.print(f"   • Coverage area: ~{isochrone_graph.number_of_nodes() / G_walk.number_of_nodes() * 100:.1f}% of network")
        
        return isochrone_graph, library_point
    else:
        console.print("[yellow]No libraries found for isochrone analysis[/yellow]")
        return None, None

def demo_visualization():
    """Demo enhanced visualization capabilities."""
    print_demo_step(6, 8, "🎨 Enhanced Visualization")
    
    place_name = "Corvallis, Oregon, USA"
    
    # Create a simple drive network
    G = ox.graph_from_place(place_name, network_type="drive")
    
    console.print("🖼️ Creating network visualizations...")
    
    # Modern figure-ground style plot (OSMnx specialty)
    fig, ax = plt.subplots(1, 1, figsize=(12, 12), facecolor='black')
    
    # Plot with modern styling
    ox.plot_graph(
        G, 
        ax=ax,
        bgcolor='black',
        node_color='none',
        edge_color='white',
        edge_linewidth=0.5,
        show=False,
        close=False
    )
    
    ax.set_title(f"OSMnx 2.0+ Network Visualization\n{place_name}", 
                color='white', fontsize=16, pad=20)
    
    # Save the plot
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    plot_path = output_dir / "osmnx_2_network_demo.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='black')
    plt.close()
    
    console.print(f"✅ Visualization saved to {plot_path}")
    
    return str(plot_path)

def demo_type_annotations():
    """Demo OSMnx 2.0's improved type annotations."""
    print_demo_step(7, 8, "🏷️ Type Annotations & Error Handling")
    
    console.print("📝 OSMnx 2.0+ Features:")
    
    # Show some type hints (this would be caught by mypy)
    features = [
        "✨ Full type annotations for better IDE support",
        "🛡️ Improved error handling and validation", 
        "⚡ Better memory management and performance",
        "🔧 Streamlined API with consistent naming",
        "📊 Enhanced graph simplification algorithms",
        "🗺️ Better integration with GeoPandas/Shapely 2.0",
        "🚀 Optimized caching and network requests",
        "📈 Improved algorithms for intersection consolidation"
    ]
    
    for feature in features:
        console.print(f"   {feature}")

def demo_integration_with_socialmapper():
    """Demo how OSMnx 2.0 integrates with SocialMapper."""
    print_demo_step(8, 8, "🔗 Integration with SocialMapper")
    
    console.print("🏘️ OSMnx 2.0 enhances SocialMapper with:")
    
    improvements = [
        ("Performance", "Faster POI discovery and network creation"),
        ("Accuracy", "Better intersection consolidation for precise demographics"),
        ("Memory", "More efficient for large-scale community analysis"),
        ("Reliability", "Improved error handling for robust batch processing"),
        ("Features", "Enhanced geometry handling for complex spatial queries"),
        ("Integration", "Better compatibility with modern geospatial stack")
    ]
    
    table = Table(title="🚀 SocialMapper + OSMnx 2.0 Benefits")
    table.add_column("Enhancement", style="cyan")
    table.add_column("Benefit", style="green")
    
    for enhancement, benefit in improvements:
        table.add_row(enhancement, benefit)
    
    console.print(table)

def main():
    """Main demo function."""
    print_header("OSMnx 2.0+ Features Demo", "🌟")
    
    console.print(f"[bold]OSMnx Version:[/bold] {ox.__version__}")
    console.print(f"[bold]NetworkX Version:[/bold] {nx.__version__}")
    console.print("")
    
    try:
        # Run all demos
        graph, consolidated_graph = demo_osmnx_performance()
        pois, buildings, parks = demo_geometries_module()
        walk_graph, betweenness, closeness, entropy = demo_network_analysis()
        drive_graph, routes = demo_routing_features()
        isochrone, library_point = demo_spatial_analysis()
        plot_path = demo_visualization()
        demo_type_annotations()
        demo_integration_with_socialmapper()
        
        # Summary
        print_header("Demo Complete! 🎉", "✅")
        
        console.print("[bold green]OSMnx 2.0+ successfully demonstrated![/bold green]")
        console.print(f"📁 Visualization saved: {plot_path}")
        console.print(f"🔗 Ready for integration with SocialMapper v0.5.0")
        console.print("")
        console.print("[dim]OSMnx 2.0+ brings cutting-edge geospatial capabilities to SocialMapper,[/dim]")
        console.print("[dim]enabling faster, more accurate community analysis than ever before![/dim]")
        
    except Exception as e:
        console.print(f"[red]Error in demo: {e}[/red]")
        raise

if __name__ == "__main__":
    main() 