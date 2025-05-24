#!/usr/bin/env python3
"""
Create a pre-computed neighbor database for packaging with SocialMapper.

This script creates a complete neighbor database with all US county relationships
pre-computed, so end users don't need local shapefiles or to run spatial computations.
The resulting database can be included in the Python package distribution.
"""

import os
import shutil
import asyncio
from pathlib import Path
from socialmapper.census import get_neighbor_manager

def create_package_neighbor_database():
    """
    Create a complete neighbor database for package distribution.
    
    This will:
    1. Create a clean neighbor database
    2. Initialize all state neighbors
    3. Use the existing populated county neighbor data
    4. Create a package-ready database file
    """
    print("=" * 60)
    print("Creating Package Neighbor Database")
    print("=" * 60)
    
    # Paths
    current_db_path = Path.home() / ".socialmapper" / "neighbors.duckdb"
    package_db_path = Path("socialmapper/data/neighbors.duckdb")
    
    # Create data directory
    package_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if current database exists and is populated
    if not current_db_path.exists():
        print(f"❌ Current neighbor database not found at {current_db_path}")
        print("Please run the neighbor population script first.")
        return False
    
    # Get statistics from current database
    manager = get_neighbor_manager()
    stats = manager.get_neighbor_statistics()
    
    print(f"Current database statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Check if database is sufficiently populated
    if stats['county_relationships'] < 15000:  # Should have ~18,560
        print(f"❌ Database appears incomplete (only {stats['county_relationships']} county relationships)")
        print("Please run the full neighbor population script first.")
        return False
    
    if stats['states_with_county_data'] < 50:  # Should have 51 (including DC)
        print(f"❌ Database missing state data (only {stats['states_with_county_data']} states)")
        print("Please run the full neighbor population script first.")
        return False
    
    print(f"✅ Database appears complete and ready for packaging")
    
    # Copy the database to package location
    print(f"\nCopying database to package location...")
    print(f"  From: {current_db_path}")
    print(f"  To: {package_db_path}")
    
    try:
        shutil.copy2(current_db_path, package_db_path)
        print(f"✅ Database copied successfully")
    except Exception as e:
        print(f"❌ Failed to copy database: {e}")
        return False
    
    # Verify the copied database
    print(f"\nVerifying copied database...")
    
    # Test the copied database
    test_manager = get_neighbor_manager(package_db_path)
    test_stats = test_manager.get_neighbor_statistics()
    
    print(f"Package database statistics:")
    for key, value in test_stats.items():
        print(f"  {key}: {value}")
    
    # Test some basic functionality
    print(f"\nTesting basic functionality...")
    
    # Test state neighbors
    nc_neighbors = test_manager.get_neighboring_states('37')  # North Carolina
    print(f"  NC neighboring states: {len(nc_neighbors)} states")
    
    # Test county neighbors
    wake_neighbors = test_manager.get_neighboring_counties('37', '183')  # Wake County, NC
    print(f"  Wake County neighbors: {len(wake_neighbors)} counties")
    
    # Get file size
    file_size_mb = package_db_path.stat().st_size / (1024 * 1024)
    print(f"  Package database size: {file_size_mb:.1f} MB")
    
    print(f"\n✅ Package neighbor database created successfully!")
    print(f"📁 Location: {package_db_path}")
    print(f"📊 Size: {file_size_mb:.1f} MB")
    print(f"🏛️  States: {test_stats['states_with_county_data']}")
    print(f"🏘️  County relationships: {test_stats['county_relationships']:,}")
    print(f"🌉 Cross-state relationships: {test_stats['cross_state_county_relationships']:,}")
    
    return True

def update_neighbor_manager_for_package():
    """
    Update the NeighborManager to use the packaged database by default.
    """
    print("\n" + "=" * 60)
    print("Updating NeighborManager for Package Distribution")
    print("=" * 60)
    
    # The database path should be relative to the package
    package_db_path = Path("socialmapper/data/neighbors.duckdb")
    
    if not package_db_path.exists():
        print(f"❌ Package database not found at {package_db_path}")
        print("Please run create_package_neighbor_database() first.")
        return False
    
    print(f"✅ Package database found at {package_db_path}")
    print(f"📝 Next steps:")
    print(f"   1. Update DEFAULT_NEIGHBOR_DB_PATH in neighbors.py")
    print(f"   2. Add the database file to MANIFEST.in")
    print(f"   3. Update setup.py to include data files")
    print(f"   4. Test the package installation")
    
    return True

def create_manifest_entry():
    """
    Create the MANIFEST.in entry for the neighbor database.
    """
    manifest_entry = "include socialmapper/data/neighbors.duckdb"
    
    manifest_path = Path("MANIFEST.in")
    
    # Read existing MANIFEST.in if it exists
    existing_content = ""
    if manifest_path.exists():
        existing_content = manifest_path.read_text()
    
    # Check if entry already exists
    if manifest_entry in existing_content:
        print(f"✅ MANIFEST.in already includes neighbor database")
        return True
    
    # Add the entry
    with open(manifest_path, 'a') as f:
        if existing_content and not existing_content.endswith('\n'):
            f.write('\n')
        f.write(manifest_entry + '\n')
    
    print(f"✅ Added neighbor database to MANIFEST.in")
    return True

def main():
    """Main function to create package-ready neighbor database."""
    
    # Step 1: Create the package database
    success = create_package_neighbor_database()
    if not success:
        return
    
    # Step 2: Create MANIFEST.in entry
    create_manifest_entry()
    
    # Step 3: Provide next steps
    update_neighbor_manager_for_package()
    
    print(f"\n🎉 Package preparation complete!")
    print(f"\n📋 Final checklist:")
    print(f"   ✅ Pre-computed neighbor database created")
    print(f"   ✅ MANIFEST.in updated")
    print(f"   🔲 Update DEFAULT_NEIGHBOR_DB_PATH in neighbors.py")
    print(f"   🔲 Update setup.py to include package_data")
    print(f"   🔲 Test package installation")
    print(f"   🔲 Remove development scripts from package")

if __name__ == "__main__":
    main() 