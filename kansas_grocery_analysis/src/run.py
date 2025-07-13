#!/usr/bin/env python3
"""
Main runner script for Kansas Grocery Analysis.
Provides a simple interface to run the various analysis steps.
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def show_menu():
    """Display the available analysis options."""
    console.print("\n[bold]Kansas Grocery Analysis Runner[/bold]")
    console.print("=" * 50)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=10)
    table.add_column("Script", style="green")
    table.add_column("Description", style="yellow")
    
    table.add_row("1", "data_prep/prepare_data.py", "Fetch and prepare store data from OpenStreetMap")
    table.add_row("2", "data_prep/clean_walmart_data.py", "Clean Walmart data (remove duplicates)")
    table.add_row("3", "analysis/analyze_access.py", "Run the main food access analysis")
    table.add_row("4", "visualization/create_census_map.py", "Create census demographic maps")
    table.add_row("5", "analysis/identify_problem_stores.py", "Identify stores with isochrone issues")
    table.add_row("6", "visualization/visualize_problem_isochrones.py", "Visualize problematic isochrones")
    table.add_row("7", "analysis/generate_report.py", "Generate final analysis report")
    
    console.print(table)
    console.print("\n[dim]Note: Run options 1-3 in sequence for a complete analysis[/dim]")

def run_script(script_path: str):
    """Run a Python script."""
    import subprocess
    
    console.print(f"\n[cyan]Running {script_path}...[/cyan]\n")
    
    # Get the absolute path
    src_dir = Path(__file__).parent
    full_path = src_dir / script_path
    
    if not full_path.exists():
        console.print(f"[red]Error: Script not found at {full_path}[/red]")
        return
    
    # Run the script
    result = subprocess.run([sys.executable, str(full_path)], cwd=src_dir.parent)
    
    if result.returncode == 0:
        console.print(f"\n[green]✓ {script_path} completed successfully[/green]")
    else:
        console.print(f"\n[red]✗ {script_path} failed with exit code {result.returncode}[/red]")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        # Direct script execution
        option = sys.argv[1]
    else:
        # Interactive mode
        show_menu()
        option = console.input("\n[bold]Enter option number (or 'q' to quit): [/bold]")
    
    if option.lower() == 'q':
        console.print("[yellow]Exiting...[/yellow]")
        return
    
    # Map options to scripts
    scripts = {
        '1': 'data_prep/prepare_data.py',
        '2': 'data_prep/clean_walmart_data.py',
        '3': 'analysis/analyze_access.py',
        '4': 'visualization/create_census_map.py',
        '5': 'analysis/identify_problem_stores.py',
        '6': 'visualization/visualize_problem_isochrones.py',
        '7': 'analysis/generate_report.py'
    }
    
    if option in scripts:
        run_script(scripts[option])
    else:
        console.print(f"[red]Invalid option: {option}[/red]")

if __name__ == "__main__":
    main()