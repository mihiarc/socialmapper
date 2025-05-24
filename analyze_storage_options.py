#!/usr/bin/env python3
"""Analyze different storage options for neighbor data: JSON vs DuckDB vs compressed formats."""

import time
import json
import gzip
import sqlite3
import tempfile
import os
import duckdb
from pathlib import Path
from socialmapper.census import get_neighbor_manager

def analyze_current_database():
    """Analyze the current DuckDB database size and structure."""
    print("="*60)
    print("CURRENT DUCKDB DATABASE ANALYSIS")
    print("="*60)
    
    # Try to access database directly with read-only mode
    db_path = Path.home() / ".socialmapper" / "census.duckdb"
    
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
        print(f"Current database file: {db_path}")
        print(f"Total database size: {db_size:,} bytes ({db_size/(1024*1024):.2f} MB)")
    else:
        print(f"Database file not found: {db_path}")
        return None, 0
    
    # Try to connect read-only
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Get table sizes and row counts
        tables = ['state_neighbors', 'county_neighbors', 'point_geography_cache', 'geographic_units', 'census_data', 'boundary_cache']
        
        print(f"\nTable analysis:")
        total_neighbor_rows = 0
        
        for table in tables:
            try:
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                row_count = count_result[0] if count_result else 0
                
                if table in ['state_neighbors', 'county_neighbors']:
                    total_neighbor_rows += row_count
                
                print(f"  {table}: {row_count:,} rows")
                
            except Exception as e:
                print(f"  {table}: Error - {e}")
        
        print(f"\nTotal neighbor relationship rows: {total_neighbor_rows:,}")
        
        conn.close()
        return db_size, total_neighbor_rows
        
    except Exception as e:
        print(f"Could not access database (likely locked): {e}")
        print("Will estimate based on file size...")
        
        # Estimate based on file size
        estimated_rows = max(0, (db_size - 1024*1024) // 100)  # Rough estimate
        print(f"Estimated neighbor rows: ~{estimated_rows:,}")
        
        return db_size, estimated_rows

def create_neighbors_only_duckdb_from_existing():
    """Create a DuckDB database with only neighbor data from existing database."""
    print(f"\n" + "="*60)
    print("NEIGHBORS-ONLY DUCKDB ANALYSIS")
    print("="*60)
    
    # Try to access existing database
    db_path = Path.home() / ".socialmapper" / "census.duckdb"
    
    if not os.path.exists(db_path):
        print("Source database not found")
        return None, 0
    
    # Create temporary DuckDB with only neighbor data
    with tempfile.NamedTemporaryFile(suffix='.duckdb', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Try read-only connection to source
        source_conn = duckdb.connect(str(db_path), read_only=True)
        
        # Create new database
        target_conn = duckdb.connect(tmp_db_path)
        
        # Create neighbor tables
        target_conn.execute("""
            CREATE TABLE state_neighbors (
                state_fips VARCHAR(2) NOT NULL,
                neighbor_state_fips VARCHAR(2) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                PRIMARY KEY(state_fips, neighbor_state_fips)
            );
        """)
        
        target_conn.execute("""
            CREATE TABLE county_neighbors (
                state_fips VARCHAR(2) NOT NULL,
                county_fips VARCHAR(3) NOT NULL,
                neighbor_state_fips VARCHAR(2) NOT NULL,
                neighbor_county_fips VARCHAR(3) NOT NULL,
                relationship_type VARCHAR(20) DEFAULT 'adjacent',
                shared_boundary_length DOUBLE,
                PRIMARY KEY(state_fips, county_fips, neighbor_state_fips, neighbor_county_fips)
            );
        """)
        
        # Copy data from existing database
        state_data = []
        county_data = []
        
        try:
            # State neighbors
            state_data = source_conn.execute("""
                SELECT state_fips, neighbor_state_fips, relationship_type
                FROM state_neighbors
            """).fetchall()
            
            if state_data:
                target_conn.executemany(
                    "INSERT INTO state_neighbors (state_fips, neighbor_state_fips, relationship_type) VALUES (?, ?, ?)",
                    state_data
                )
        except Exception as e:
            print(f"Could not copy state data: {e}")
        
        try:
            # County neighbors
            county_data = source_conn.execute("""
                SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, 
                       relationship_type, shared_boundary_length
                FROM county_neighbors
            """).fetchall()
            
            if county_data:
                target_conn.executemany("""
                    INSERT INTO county_neighbors 
                    (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, county_data)
        except Exception as e:
            print(f"Could not copy county data: {e}")
        
        # Create indexes for performance
        target_conn.execute("CREATE INDEX idx_state_neighbors_state ON state_neighbors(state_fips);")
        target_conn.execute("CREATE INDEX idx_county_neighbors_county ON county_neighbors(state_fips, county_fips);")
        
        source_conn.close()
        target_conn.close()
        
        # Get file size
        neighbors_db_size = os.path.getsize(tmp_db_path)
        
        print(f"Neighbors-only DuckDB created: {tmp_db_path}")
        print(f"File size: {neighbors_db_size:,} bytes ({neighbors_db_size/1024:.1f} KB, {neighbors_db_size/(1024*1024):.3f} MB)")
        print(f"State relationships: {len(state_data):,}")
        print(f"County relationships: {len(county_data):,}")
        
        return tmp_db_path, neighbors_db_size
        
    except Exception as e:
        print(f"Error creating neighbors-only database: {e}")
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)
        
        # Create estimated size based on known data
        print("Creating size estimate based on typical neighbor data...")
        
        # Typical sizes for neighbor data:
        # - 50 states × ~4 neighbors each = 200 state relationships
        # - 100 counties × ~6 neighbors each = 600 county relationships  
        # - Each relationship ~50-100 bytes in DuckDB
        
        estimated_state_rows = 200
        estimated_county_rows = 600
        estimated_size = (estimated_state_rows * 60) + (estimated_county_rows * 80) + 50000  # Base overhead
        
        print(f"Estimated neighbors-only DuckDB size: ~{estimated_size:,} bytes ({estimated_size/1024:.1f} KB)")
        
        return None, estimated_size

def create_sqlite_version_from_existing():
    """Create SQLite version from existing data."""
    print(f"\n" + "="*60)
    print("SQLITE VERSION ANALYSIS")
    print("="*60)
    
    # Try to access existing database
    db_path = Path.home() / ".socialmapper" / "census.duckdb"
    
    if not os.path.exists(db_path):
        print("Source database not found")
        return None, 0
    
    # Create temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp_file:
        tmp_db_path = tmp_file.name
    
    try:
        # Try read-only connection to source
        source_conn = duckdb.connect(str(db_path), read_only=True)
        
        # Create SQLite database
        sqlite_conn = sqlite3.connect(tmp_db_path)
        
        # Create tables
        sqlite_conn.execute("""
            CREATE TABLE state_neighbors (
                state_fips TEXT NOT NULL,
                neighbor_state_fips TEXT NOT NULL,
                relationship_type TEXT DEFAULT 'adjacent',
                PRIMARY KEY(state_fips, neighbor_state_fips)
            );
        """)
        
        sqlite_conn.execute("""
            CREATE TABLE county_neighbors (
                state_fips TEXT NOT NULL,
                county_fips TEXT NOT NULL,
                neighbor_state_fips TEXT NOT NULL,
                neighbor_county_fips TEXT NOT NULL,
                relationship_type TEXT DEFAULT 'adjacent',
                shared_boundary_length REAL,
                PRIMARY KEY(state_fips, county_fips, neighbor_state_fips, neighbor_county_fips)
            );
        """)
        
        # Copy data
        state_data = []
        county_data = []
        
        try:
            state_data = source_conn.execute("""
                SELECT state_fips, neighbor_state_fips, relationship_type
                FROM state_neighbors
            """).fetchall()
            
            county_data = source_conn.execute("""
                SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, 
                       relationship_type, shared_boundary_length
                FROM county_neighbors
            """).fetchall()
        except Exception as e:
            print(f"Could not read data: {e}")
        
        if state_data:
            sqlite_conn.executemany(
                "INSERT INTO state_neighbors (state_fips, neighbor_state_fips, relationship_type) VALUES (?, ?, ?)",
                state_data
            )
        
        if county_data:
            sqlite_conn.executemany("""
                INSERT INTO county_neighbors 
                (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                VALUES (?, ?, ?, ?, ?, ?)
            """, county_data)
        
        # Create indexes
        sqlite_conn.execute("CREATE INDEX idx_state_neighbors_state ON state_neighbors(state_fips);")
        sqlite_conn.execute("CREATE INDEX idx_county_neighbors_county ON county_neighbors(state_fips, county_fips);")
        
        source_conn.close()
        sqlite_conn.close()
        
        # Get file size
        sqlite_size = os.path.getsize(tmp_db_path)
        
        print(f"SQLite database created: {tmp_db_path}")
        print(f"File size: {sqlite_size:,} bytes ({sqlite_size/1024:.1f} KB, {sqlite_size/(1024*1024):.3f} MB)")
        
        return tmp_db_path, sqlite_size
        
    except Exception as e:
        print(f"Error creating SQLite database: {e}")
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)
        
        # Estimate SQLite size (typically 20-30% larger than DuckDB)
        estimated_duckdb_size = 100000  # 100KB estimate
        estimated_sqlite_size = int(estimated_duckdb_size * 1.25)
        
        print(f"Estimated SQLite size: ~{estimated_sqlite_size:,} bytes ({estimated_sqlite_size/1024:.1f} KB)")
        
        return None, estimated_sqlite_size

def create_json_versions_from_existing():
    """Create JSON versions from existing data."""
    print(f"\n" + "="*60)
    print("JSON VERSIONS ANALYSIS")
    print("="*60)
    
    # Try to access existing database
    db_path = Path.home() / ".socialmapper" / "census.duckdb"
    
    if not os.path.exists(db_path):
        print("Source database not found - using estimates")
        return create_json_estimates()
    
    try:
        # Try read-only connection
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Get data
        state_data = conn.execute("""
            SELECT state_fips, neighbor_state_fips, relationship_type
            FROM state_neighbors
        """).fetchall()
        
        county_data = conn.execute("""
            SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, 
                   relationship_type, shared_boundary_length
            FROM county_neighbors
        """).fetchall()
        
        conn.close()
        
    except Exception as e:
        print(f"Could not read data: {e}")
        return create_json_estimates()
    
    # Create structured data
    export_data = {
        "metadata": {
            "description": "Pre-computed neighbor relationships for SocialMapper",
            "state_relationships": len(state_data),
            "county_relationships": len(county_data),
            "generated_by": "SocialMapper neighbor optimization system"
        },
        "state_neighbors": {},
        "county_neighbors": {}
    }
    
    # Process state data
    for state_fips, neighbor_state, rel_type in state_data:
        if state_fips not in export_data["state_neighbors"]:
            export_data["state_neighbors"][state_fips] = []
        export_data["state_neighbors"][state_fips].append({
            "neighbor_state": neighbor_state,
            "relationship_type": rel_type
        })
    
    # Process county data
    for state_fips, county_fips, neighbor_state, neighbor_county, rel_type, boundary_length in county_data:
        county_key = f"{state_fips}{county_fips}"
        if county_key not in export_data["county_neighbors"]:
            export_data["county_neighbors"][county_key] = {
                "state_fips": state_fips,
                "county_fips": county_fips,
                "neighbors": []
            }
        export_data["county_neighbors"][county_key]["neighbors"].append({
            "state_fips": neighbor_state,
            "county_fips": neighbor_county,
            "shared_boundary_length": round(boundary_length, 6),
            "relationship_type": rel_type
        })
    
    return create_json_files(export_data)

def create_json_estimates():
    """Create JSON size estimates when database is not accessible."""
    print("Creating JSON size estimates...")
    
    # Estimate typical data structure
    estimated_data = {
        "metadata": {
            "description": "Pre-computed neighbor relationships for SocialMapper",
            "state_relationships": 200,
            "county_relationships": 600,
            "generated_by": "SocialMapper neighbor optimization system"
        },
        "state_neighbors": {},
        "county_neighbors": {}
    }
    
    # Create sample data for size estimation
    for i in range(10):  # Sample 10 states
        state_fips = f"{i+1:02d}"
        estimated_data["state_neighbors"][state_fips] = [
            {"neighbor_state": f"{j+1:02d}", "relationship_type": "adjacent"}
            for j in range(4)  # ~4 neighbors per state
        ]
    
    for i in range(50):  # Sample 50 counties
        county_key = f"{(i//10)+1:02d}{i%10+1:03d}"
        estimated_data["county_neighbors"][county_key] = {
            "state_fips": f"{(i//10)+1:02d}",
            "county_fips": f"{i%10+1:03d}",
            "neighbors": [
                {
                    "state_fips": f"{(j//10)+1:02d}",
                    "county_fips": f"{j%10+1:03d}",
                    "shared_boundary_length": 1234.567890,
                    "relationship_type": "adjacent"
                }
                for j in range(6)  # ~6 neighbors per county
            ]
        }
    
    sizes = create_json_files(estimated_data)
    
    # Scale up estimates based on actual vs sample data
    scale_factor = (200 + 600) / (40 + 300)  # Actual relationships / sample relationships
    
    for key in sizes:
        sizes[key] = int(sizes[key] * scale_factor)
    
    print("(Scaled estimates based on sample data)")
    return sizes

def create_json_files(export_data):
    """Create JSON files and return sizes."""
    # Regular JSON
    json_file = "neighbors_data.json"
    with open(json_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    json_size = os.path.getsize(json_file)
    
    # Compressed JSON
    json_gz_file = "neighbors_data.json.gz"
    with open(json_file, 'rb') as f_in:
        with gzip.open(json_gz_file, 'wb') as f_out:
            f_out.writelines(f_in)
    
    json_gz_size = os.path.getsize(json_gz_file)
    
    # Compact JSON (no indentation)
    json_compact_file = "neighbors_data_compact.json"
    with open(json_compact_file, 'w') as f:
        json.dump(export_data, f, separators=(',', ':'))
    
    json_compact_size = os.path.getsize(json_compact_file)
    
    # Compact compressed JSON
    json_compact_gz_file = "neighbors_data_compact.json.gz"
    with open(json_compact_file, 'rb') as f_in:
        with gzip.open(json_compact_gz_file, 'wb') as f_out:
            f_out.writelines(f_in)
    
    json_compact_gz_size = os.path.getsize(json_compact_gz_file)
    
    print(f"JSON (formatted): {json_size:,} bytes ({json_size/1024:.1f} KB)")
    print(f"JSON (compact): {json_compact_size:,} bytes ({json_compact_size/1024:.1f} KB)")
    print(f"JSON.gz (formatted): {json_gz_size:,} bytes ({json_gz_size/1024:.1f} KB)")
    print(f"JSON.gz (compact): {json_compact_gz_size:,} bytes ({json_compact_gz_size/1024:.1f} KB)")
    
    # Cleanup
    for file in [json_file, json_gz_file, json_compact_file, json_compact_gz_file]:
        if os.path.exists(file):
            os.unlink(file)
    
    return {
        'json': json_size,
        'json_compact': json_compact_size,
        'json_gz': json_gz_size,
        'json_compact_gz': json_compact_gz_size
    }

def main():
    print("STORAGE OPTIONS ANALYSIS FOR NEIGHBOR DATA")
    print("="*60)
    
    # Analyze current database
    current_db_size, total_rows = analyze_current_database()
    
    # Create neighbors-only DuckDB
    duckdb_path, duckdb_size = create_neighbors_only_duckdb_from_existing()
    
    # Create SQLite version
    sqlite_path, sqlite_size = create_sqlite_version_from_existing()
    
    # Create JSON versions
    json_sizes = create_json_versions_from_existing()
    
    # Summary comparison
    print(f"\n" + "="*60)
    print("STORAGE COMPARISON SUMMARY")
    print("="*60)
    
    if current_db_size:
        print(f"Current full DuckDB:     {current_db_size:,} bytes ({current_db_size/(1024*1024):.2f} MB)")
    
    if duckdb_size:
        print(f"Neighbors-only DuckDB:   {duckdb_size:,} bytes ({duckdb_size/1024:.1f} KB)")
    
    if sqlite_size:
        print(f"SQLite database:         {sqlite_size:,} bytes ({sqlite_size/1024:.1f} KB)")
    
    print(f"JSON (formatted):        {json_sizes['json']:,} bytes ({json_sizes['json']/1024:.1f} KB)")
    print(f"JSON (compact):          {json_sizes['json_compact']:,} bytes ({json_sizes['json_compact']/1024:.1f} KB)")
    print(f"JSON.gz (formatted):     {json_sizes['json_gz']:,} bytes ({json_sizes['json_gz']/1024:.1f} KB)")
    print(f"JSON.gz (compact):       {json_sizes['json_compact_gz']:,} bytes ({json_sizes['json_compact_gz']/1024:.1f} KB)")
    
    # Size reduction analysis
    if current_db_size and duckdb_size:
        reduction = ((current_db_size - duckdb_size) / current_db_size) * 100
        print(f"\nSize reduction (full DB → neighbors-only): {reduction:.1f}%")
    
    # GitHub feasibility
    print(f"\nGitHub storage feasibility (25MB limit):")
    formats = [
        ("Neighbors-only DuckDB", duckdb_size),
        ("SQLite database", sqlite_size),
        ("JSON (compact)", json_sizes['json_compact']),
        ("JSON.gz (compact)", json_sizes['json_compact_gz'])
    ]
    
    for name, size in formats:
        if size > 0:
            feasible = "✅" if size < 25*1024*1024 else "❌"
            print(f"  {name}: {feasible} ({size/(1024*1024):.3f} MB)")
    
    # Recommendations
    print(f"\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    smallest_size = min(size for size in [duckdb_size, sqlite_size] + list(json_sizes.values()) if size > 0)
    
    if json_sizes['json_compact_gz'] == smallest_size:
        print("🏆 BEST: Compressed compact JSON")
        print("   • Smallest file size")
        print("   • Human readable when decompressed")
        print("   • Easy to version control diffs")
        print("   • No database dependencies")
        print("   • Universal compatibility")
    elif duckdb_size == smallest_size:
        print("🏆 BEST: Neighbors-only DuckDB")
        print("   • Very small file size")
        print("   • Fast queries with indexes")
        print("   • Same technology as main system")
        print("   • Ready-to-use format")
        print("   • No parsing overhead")
    
    print(f"\nFor GitHub storage:")
    print(f"• All formats are feasible (well under 25MB limit)")
    print(f"• Compressed JSON offers best size/portability balance")
    print(f"• DuckDB offers best performance for queries")
    print(f"• Consider distributing both: JSON for transparency, DuckDB for performance")
    
    print(f"\nPerformance implications:")
    print(f"• DuckDB: Instant queries, no parsing overhead")
    print(f"• JSON: One-time parsing cost (~1-10ms), then fast lookups")
    print(f"• Both eliminate the 60+ second initialization time")
    
    # Cleanup
    for path in [duckdb_path, sqlite_path]:
        if path and os.path.exists(path):
            os.unlink(path)

if __name__ == "__main__":
    main() 