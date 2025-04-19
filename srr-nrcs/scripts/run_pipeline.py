#!/usr/bin/env python3
import importlib
import sys
from pathlib import Path
from scripts.core.config import Config  # Use absolute import

def run_module(module_name: str, description: str):
    """Import and run a module function and handle any errors."""
    print(f"\n{description}")
    try:
        module = importlib.import_module(module_name)
        # Assuming each module has a main function
        if hasattr(module, 'main'):
            module.main()
        elif hasattr(module, 'migrate_data'):  # Special case for migrate_data
            module.migrate_data()
        else:
            print(f"Error: Module {module_name} has no main/migrate_data function")
            return 1
        return 0
    except Exception as e:
        print(f"Error running {module_name}: {e}")
        return 1

def main():
    """Run the complete analysis pipeline."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    print("Running NRCS Conservation Study Area Analysis pipeline...")
    
    # Run the pipeline steps
    steps = [
        {
            'module': 'scripts.core.migrate_data',
            'description': 'Migrating data to new directory structure...'
        },
        {
            'module': 'scripts.core.fetch_county_boundaries',
            'description': '1. Fetching county boundaries...'
        },
        {
            'module': 'scripts.core.fetch_walmart_locations',
            'description': '2. Fetching Walmart locations...'
        },
        {
            'module': 'scripts.core.process_walmart_locations',
            'description': '3. Processing Walmart locations...'
        },
        {
            'module': 'scripts.core.create_maps',
            'description': '4. Creating maps...'
        }
    ]
    
    for step in steps:
        result = run_module(step['module'], step['description'])
        if result != 0:
            sys.exit(result)
    
    print("\nPipeline complete!")

if __name__ == "__main__":
    main() 