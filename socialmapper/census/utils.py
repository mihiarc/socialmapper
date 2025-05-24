#!/usr/bin/env python3
"""
Utility functions for the new census module.

This module provides:
- Migration utilities from old census module
- Database maintenance functions
- Administrative tools
- Performance optimization helpers
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import geopandas as gpd

from socialmapper.progress import get_progress_bar
from . import get_census_database, CensusDatabase

logger = logging.getLogger(__name__)


# Note: Migration functions have been removed as they are no longer needed.
# The new system uses DuckDB from the start and doesn't require migration.


def optimize_database(db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Optimize the census database for better performance.
    
    Args:
        db_path: Path to the DuckDB database
        
    Returns:
        Dictionary with optimization results
    """
    db = get_census_database(db_path)
    
    results = {}
    
    # Analyze tables
    get_progress_bar().write("Analyzing database tables...")
    
    tables = ['states', 'counties', 'tracts', 'block_groups', 'census_data']
    for table in tables:
        try:
            count = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            results[f"{table}_count"] = count
            get_progress_bar().write(f"  {table}: {count:,} records")
        except Exception as e:
            results[f"{table}_error"] = str(e)
    
    # Vacuum database
    get_progress_bar().write("Optimizing database...")
    try:
        db.conn.execute("VACUUM;")
        results["vacuum"] = "success"
    except Exception as e:
        results["vacuum"] = f"error: {e}"
    
    # Update statistics
    try:
        db.conn.execute("ANALYZE;")
        results["analyze"] = "success"
    except Exception as e:
        results["analyze"] = f"error: {e}"
    
    # Get database size
    try:
        size_bytes = db.db_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        results["database_size_mb"] = round(size_mb, 2)
        get_progress_bar().write(f"Database size: {size_mb:.2f} MB")
    except Exception as e:
        results["size_error"] = str(e)
    
    return results


def export_database_info(
    db_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Export information about the census database.
    
    Args:
        db_path: Path to the DuckDB database
        output_path: Path to save the info (optional)
        
    Returns:
        Dictionary with database information
    """
    db = get_census_database(db_path)
    
    info = {
        "database_path": str(db.db_path),
        "tables": {},
        "views": [],
        "indexes": []
    }
    
    # Get table information
    tables_query = """
        SELECT table_name, estimated_size 
        FROM duckdb_tables() 
        WHERE schema_name = 'main'
    """
    
    try:
        tables_df = db.conn.execute(tables_query).df()
        for _, row in tables_df.iterrows():
            table_name = row['table_name']
            
            # Get column info
            columns_query = f"DESCRIBE {table_name}"
            columns_df = db.conn.execute(columns_query).df()
            
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count = db.conn.execute(count_query).fetchone()[0]
            
            info["tables"][table_name] = {
                "row_count": count,
                "estimated_size": row.get('estimated_size'),
                "columns": columns_df.to_dict('records')
            }
    except Exception as e:
        info["tables_error"] = str(e)
    
    # Get views
    try:
        views_query = "SELECT view_name FROM duckdb_views() WHERE schema_name = 'main'"
        views_df = db.conn.execute(views_query).df()
        info["views"] = views_df['view_name'].tolist() if not views_df.empty else []
    except Exception as e:
        info["views_error"] = str(e)
    
    # Save to file if requested
    if output_path:
        import json
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2, default=str)
        
        get_progress_bar().write(f"Database info saved to {output_path}")
    
    return info


def create_summary_views(db_path: Optional[Union[str, Path]] = None) -> List[str]:
    """
    Create useful summary views for analysis.
    
    Args:
        db_path: Path to the DuckDB database
        
    Returns:
        List of created view names
    """
    db = get_census_database(db_path)
    
    views_created = []
    
    # State summary view
    try:
        db.conn.execute("""
            CREATE OR REPLACE VIEW state_summary AS
            SELECT 
                s.fips_code,
                s.name as state_name,
                s.abbreviation,
                COUNT(DISTINCT bg.geoid) as block_group_count,
                COUNT(DISTINCT bg.county_fips) as county_count,
                COUNT(DISTINCT cd.variable_code) as variables_available,
                MAX(cd.year) as latest_data_year
            FROM states s
            LEFT JOIN block_groups bg ON s.fips_code = bg.state_fips
            LEFT JOIN census_data cd ON bg.geoid = cd.geoid
            GROUP BY s.fips_code, s.name, s.abbreviation
            ORDER BY s.name
        """)
        views_created.append("state_summary")
    except Exception as e:
        logger.error(f"Failed to create state_summary view: {e}")
    
    # Variable summary view
    try:
        db.conn.execute("""
            CREATE OR REPLACE VIEW variable_summary AS
            SELECT 
                variable_code,
                variable_name,
                COUNT(DISTINCT geoid) as block_groups_with_data,
                COUNT(DISTINCT LEFT(geoid, 2)) as states_with_data,
                MIN(year) as earliest_year,
                MAX(year) as latest_year,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value
            FROM census_data
            WHERE value IS NOT NULL
            GROUP BY variable_code, variable_name
            ORDER BY variable_code
        """)
        views_created.append("variable_summary")
    except Exception as e:
        logger.error(f"Failed to create variable_summary view: {e}")
    
    # Data coverage view
    try:
        db.conn.execute("""
            CREATE OR REPLACE VIEW data_coverage AS
            SELECT 
                LEFT(bg.geoid, 2) as state_fips,
                s.name as state_name,
                COUNT(DISTINCT bg.geoid) as total_block_groups,
                COUNT(DISTINCT cd.geoid) as block_groups_with_data,
                ROUND(
                    COUNT(DISTINCT cd.geoid) * 100.0 / COUNT(DISTINCT bg.geoid), 
                    2
                ) as coverage_percentage,
                COUNT(DISTINCT cd.variable_code) as variables_available
            FROM block_groups bg
            LEFT JOIN states s ON bg.state_fips = s.fips_code
            LEFT JOIN census_data cd ON bg.geoid = cd.geoid
            GROUP BY LEFT(bg.geoid, 2), s.name
            ORDER BY coverage_percentage DESC
        """)
        views_created.append("data_coverage")
    except Exception as e:
        logger.error(f"Failed to create data_coverage view: {e}")
    
    get_progress_bar().write(f"Created {len(views_created)} summary views: {', '.join(views_created)}")
    return views_created


def backup_database(
    db_path: Optional[Union[str, Path]] = None,
    backup_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Create a backup of the census database.
    
    Args:
        db_path: Path to the source database
        backup_path: Path for the backup (optional)
        
    Returns:
        Path to the backup file
    """
    db = get_census_database(db_path)
    
    if backup_path is None:
        backup_dir = db.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"census_backup_{timestamp}.duckdb"
    else:
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup using DuckDB's EXPORT/IMPORT or simple file copy
    try:
        # Close the connection temporarily
        db.close()
        
        # Copy the database file
        shutil.copy2(db.db_path, backup_path)
        
        # Reconnect
        db._initialize_database()
        
        get_progress_bar().write(f"Database backed up to {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        # Ensure we reconnect even if backup fails
        if not db.conn:
            db._initialize_database()
        raise


def restore_database(
    backup_path: Union[str, Path],
    db_path: Optional[Union[str, Path]] = None,
    force: bool = False
) -> bool:
    """
    Restore the census database from a backup.
    
    Args:
        backup_path: Path to the backup file
        db_path: Path to restore to (optional)
        force: Whether to overwrite existing database
        
    Returns:
        True if restore was successful
    """
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    if db_path is None:
        from . import DEFAULT_DB_PATH
        db_path = DEFAULT_DB_PATH
    else:
        db_path = Path(db_path)
    
    if db_path.exists() and not force:
        raise FileExistsError(
            f"Database already exists at {db_path}. Use force=True to overwrite."
        )
    
    try:
        # Ensure target directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy backup to target location
        shutil.copy2(backup_path, db_path)
        
        # Test the restored database
        test_db = get_census_database(db_path)
        test_db.close()
        
        get_progress_bar().write(f"Database restored from {backup_path} to {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def clear_cache(
    db_path: Optional[Union[str, Path]] = None,
    tables: Optional[List[str]] = None,
    confirm: bool = False
) -> Dict[str, int]:
    """
    Clear cached data from the database.
    
    Args:
        db_path: Path to the database
        tables: List of tables to clear (default: all data tables)
        confirm: Whether to proceed without confirmation
        
    Returns:
        Dictionary with counts of deleted records
    """
    if not confirm:
        raise ValueError("This operation will delete data. Set confirm=True to proceed.")
    
    db = get_census_database(db_path)
    
    if tables is None:
        tables = ['census_data', 'block_groups', 'tracts', 'counties']
    
    deleted_counts = {}
    
    for table in tables:
        try:
            # Get count before deletion
            count_before = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            
            # Delete all records
            db.conn.execute(f"DELETE FROM {table}")
            
            deleted_counts[table] = count_before
            get_progress_bar().write(f"Cleared {count_before:,} records from {table}")
            
        except Exception as e:
            logger.error(f"Failed to clear {table}: {e}")
            deleted_counts[table] = -1
    
    # Vacuum after clearing
    try:
        db.conn.execute("VACUUM;")
    except Exception as e:
        logger.warning(f"Failed to vacuum after clearing: {e}")
    
    return deleted_counts 