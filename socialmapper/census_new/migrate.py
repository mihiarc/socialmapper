#!/usr/bin/env python3
"""
Migration script for transitioning from old census module to new DuckDB-based system.

This script helps users:
1. Migrate existing cached data
2. Update their code to use the new API
3. Verify the migration was successful
4. Clean up old files
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.progress import get_progress_bar
from socialmapper.census_new import (
    get_census_database,
    migrate_from_old_cache,
    cleanup_old_cache,
    optimize_database,
    export_database_info,
    create_summary_views
)

logger = logging.getLogger(__name__)


def check_old_system() -> Dict[str, Any]:
    """
    Check what exists in the old census system.
    
    Returns:
        Dictionary with information about the old system
    """
    info = {
        "old_cache_exists": False,
        "old_cache_files": [],
        "old_module_exists": False,
        "cache_size_mb": 0
    }
    
    # Check for old cache directory
    cache_dir = Path("cache")
    if cache_dir.exists():
        info["old_cache_exists"] = True
        
        # Find block group cache files
        cache_files = list(cache_dir.glob("block_groups_*.geojson"))
        info["old_cache_files"] = [str(f) for f in cache_files]
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())
        info["cache_size_mb"] = round(total_size / (1024 * 1024), 2)
    
    # Check for old census module
    try:
        import socialmapper.census
        info["old_module_exists"] = True
    except ImportError:
        info["old_module_exists"] = False
    
    return info


def run_migration(
    force: bool = False,
    backup_old: bool = True,
    cleanup: bool = False
) -> Dict[str, Any]:
    """
    Run the complete migration process.
    
    Args:
        force: Whether to overwrite existing data
        backup_old: Whether to backup old cache before migration
        cleanup: Whether to clean up old files after migration
        
    Returns:
        Dictionary with migration results
    """
    results = {
        "migration_successful": False,
        "files_migrated": 0,
        "errors": [],
        "database_info": {}
    }
    
    get_progress_bar().write("=" * 60)
    get_progress_bar().write("SocialMapper Census Module Migration")
    get_progress_bar().write("=" * 60)
    
    # Step 1: Check old system
    get_progress_bar().write("\n1. Checking existing system...")
    old_info = check_old_system()
    
    if not old_info["old_cache_exists"]:
        get_progress_bar().write("No old cache found - nothing to migrate")
        results["migration_successful"] = True
        return results
    
    get_progress_bar().write(f"Found {len(old_info['old_cache_files'])} cache files ({old_info['cache_size_mb']} MB)")
    
    # Step 2: Create backup if requested
    if backup_old:
        get_progress_bar().write("\n2. Creating backup of old cache...")
        try:
            backup_dir = Path("cache_backup")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree("cache", backup_dir)
            get_progress_bar().write(f"Backup created at {backup_dir}")
        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            results["errors"].append(error_msg)
            get_progress_bar().write(f"Warning: {error_msg}")
    
    # Step 3: Run migration
    get_progress_bar().write("\n3. Migrating data to DuckDB...")
    try:
        migration_success = migrate_from_old_cache(force=force)
        if migration_success:
            results["migration_successful"] = True
            results["files_migrated"] = len(old_info["old_cache_files"])
            get_progress_bar().write("Migration completed successfully!")
        else:
            results["errors"].append("Migration failed - no files were migrated")
    except Exception as e:
        error_msg = f"Migration failed: {e}"
        results["errors"].append(error_msg)
        get_progress_bar().write(f"Error: {error_msg}")
        return results
    
    # Step 4: Optimize database
    get_progress_bar().write("\n4. Optimizing database...")
    try:
        optimization_results = optimize_database()
        get_progress_bar().write("Database optimization completed")
    except Exception as e:
        error_msg = f"Database optimization failed: {e}"
        results["errors"].append(error_msg)
        get_progress_bar().write(f"Warning: {error_msg}")
    
    # Step 5: Create summary views
    get_progress_bar().write("\n5. Creating summary views...")
    try:
        views_created = create_summary_views()
        get_progress_bar().write(f"Created {len(views_created)} summary views")
    except Exception as e:
        error_msg = f"Failed to create summary views: {e}"
        results["errors"].append(error_msg)
        get_progress_bar().write(f"Warning: {error_msg}")
    
    # Step 6: Export database info
    get_progress_bar().write("\n6. Generating database information...")
    try:
        db_info = export_database_info()
        results["database_info"] = db_info
        
        # Print summary
        get_progress_bar().write("\nDatabase Summary:")
        for table_name, table_info in db_info.get("tables", {}).items():
            count = table_info.get("row_count", 0)
            get_progress_bar().write(f"  {table_name}: {count:,} records")
        
    except Exception as e:
        error_msg = f"Failed to export database info: {e}"
        results["errors"].append(error_msg)
        get_progress_bar().write(f"Warning: {error_msg}")
    
    # Step 7: Clean up old files if requested
    if cleanup and results["migration_successful"]:
        get_progress_bar().write("\n7. Cleaning up old cache files...")
        try:
            cleanup_success = cleanup_old_cache(backup=False)  # Already backed up above
            if cleanup_success:
                get_progress_bar().write("Old cache files cleaned up")
            else:
                results["errors"].append("Failed to clean up old cache files")
        except Exception as e:
            error_msg = f"Cleanup failed: {e}"
            results["errors"].append(error_msg)
            get_progress_bar().write(f"Warning: {error_msg}")
    
    return results


def verify_migration() -> Dict[str, Any]:
    """
    Verify that the migration was successful.
    
    Returns:
        Dictionary with verification results
    """
    verification = {
        "database_accessible": False,
        "tables_exist": False,
        "data_present": False,
        "api_functional": False,
        "errors": []
    }
    
    get_progress_bar().write("\nVerifying migration...")
    
    try:
        # Test database access
        db = get_census_database()
        verification["database_accessible"] = True
        get_progress_bar().write("✓ Database accessible")
        
        # Check tables exist
        tables = ['states', 'counties', 'tracts', 'block_groups', 'census_data']
        for table in tables:
            count = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count > 0:
                verification["tables_exist"] = True
                verification["data_present"] = True
                break
        
        if verification["tables_exist"]:
            get_progress_bar().write("✓ Database tables exist")
        
        if verification["data_present"]:
            get_progress_bar().write("✓ Data present in database")
        
        # Test API functionality
        from socialmapper.census_new import get_census_block_groups
        
        # Try to get block groups for a small state (Delaware)
        test_gdf = get_census_block_groups(['10'], force_refresh=False)
        if not test_gdf.empty:
            verification["api_functional"] = True
            get_progress_bar().write("✓ API functional")
        
    except Exception as e:
        error_msg = f"Verification failed: {e}"
        verification["errors"].append(error_msg)
        get_progress_bar().write(f"✗ {error_msg}")
    
    return verification


def print_usage_examples():
    """Print examples of how to use the new API."""
    
    examples = """
=== New API Usage Examples ===

1. Get block groups for states:
   from socialmapper.census_new import get_census_block_groups
   gdf = get_census_block_groups(['06', '36'])  # CA and NY

2. Find intersecting block groups:
   from socialmapper.census_new import isochrone_to_block_groups
   result = isochrone_to_block_groups(isochrone_gdf, ['06'])

3. Get census data:
   from socialmapper.census_new import get_census_data_for_block_groups
   census_gdf = get_census_data_for_block_groups(
       block_groups_gdf, 
       ['total_population', 'median_income']
   )

4. Database management:
   from socialmapper.census_new import get_census_database, optimize_database
   db = get_census_database()
   optimize_database()

5. Create custom views:
   from socialmapper.census_new import CensusDataManager
   data_manager = CensusDataManager(db)
   view_name = data_manager.create_census_view(geoids, variables)

=== Migration completed! ===
Your old cache files have been migrated to a DuckDB database.
The new system provides better performance and more features.
"""
    
    get_progress_bar().write(examples)


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate SocialMapper census module to DuckDB-based system"
    )
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force migration even if data already exists"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true", 
        help="Skip creating backup of old cache"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old cache files after migration"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing migration, don't migrate"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples for the new API"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.examples:
        print_usage_examples()
        return
    
    if args.verify_only:
        verification = verify_migration()
        if all([
            verification["database_accessible"],
            verification["tables_exist"], 
            verification["data_present"],
            verification["api_functional"]
        ]):
            get_progress_bar().write("\n✓ Migration verification successful!")
            sys.exit(0)
        else:
            get_progress_bar().write("\n✗ Migration verification failed!")
            for error in verification["errors"]:
                get_progress_bar().write(f"  Error: {error}")
            sys.exit(1)
    
    # Run migration
    results = run_migration(
        force=args.force,
        backup_old=not args.no_backup,
        cleanup=args.cleanup
    )
    
    # Print results
    if results["migration_successful"]:
        get_progress_bar().write(f"\n✓ Migration successful! Migrated {results['files_migrated']} files")
        
        # Run verification
        verification = verify_migration()
        
        if verification["api_functional"]:
            print_usage_examples()
        
        if results["errors"]:
            get_progress_bar().write("\nWarnings during migration:")
            for error in results["errors"]:
                get_progress_bar().write(f"  - {error}")
    else:
        get_progress_bar().write("\n✗ Migration failed!")
        for error in results["errors"]:
            get_progress_bar().write(f"  Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main() 