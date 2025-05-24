#!/usr/bin/env python3
"""Export neighbor data in multiple formats for distribution."""

import json
import gzip
import tempfile
import os
import shutil
import duckdb
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from .neighbors import get_neighbor_manager

logger = logging.getLogger(__name__)

class NeighborExporter:
    """Export neighbor data in multiple formats for distribution."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the exporter.
        
        Args:
            output_dir: Directory to save exported files. Defaults to current directory.
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export_all_formats(self, 
                          include_states: bool = True,
                          include_counties: bool = True,
                          state_fips_list: Optional[List[str]] = None) -> Dict[str, Path]:
        """Export neighbor data in all formats.
        
        Args:
            include_states: Whether to include state neighbor data
            include_counties: Whether to include county neighbor data  
            state_fips_list: List of state FIPS codes to include. If None, includes all.
            
        Returns:
            Dictionary mapping format names to file paths
        """
        logger.info("Starting neighbor data export...")
        
        # Get the data
        data = self._extract_neighbor_data(include_states, include_counties, state_fips_list)
        
        # Export in all formats
        exported_files = {}
        
        # JSON formats
        exported_files['json'] = self._export_json(data, compressed=False, compact=False)
        exported_files['json_compact'] = self._export_json(data, compressed=False, compact=True)
        exported_files['json_gz'] = self._export_json(data, compressed=True, compact=False)
        exported_files['json_gz_compact'] = self._export_json(data, compressed=True, compact=True)
        
        # Database formats
        exported_files['duckdb'] = self._export_duckdb(data)
        exported_files['sqlite'] = self._export_sqlite(data)
        
        # Create summary
        self._create_export_summary(exported_files, data)
        
        logger.info(f"Export completed. Files saved to: {self.output_dir}")
        return exported_files
    
    def export_production_formats(self,
                                 include_states: bool = True,
                                 include_counties: bool = True,
                                 state_fips_list: Optional[List[str]] = None) -> Dict[str, Path]:
        """Export only the recommended production formats.
        
        Returns:
            Dictionary with 'json_gz_compact' and 'duckdb' file paths
        """
        logger.info("Exporting production formats (compressed JSON + DuckDB)...")
        
        # Get the data
        data = self._extract_neighbor_data(include_states, include_counties, state_fips_list)
        
        # Export production formats
        exported_files = {}
        exported_files['json_gz_compact'] = self._export_json(data, compressed=True, compact=True)
        exported_files['duckdb'] = self._export_duckdb(data)
        
        # Create summary
        self._create_export_summary(exported_files, data)
        
        logger.info("Production export completed.")
        return exported_files
    
    def _extract_neighbor_data(self, 
                              include_states: bool,
                              include_counties: bool,
                              state_fips_list: Optional[List[str]]) -> Dict:
        """Extract neighbor data from the dedicated neighbor database."""
        logger.info("Extracting neighbor data from dedicated neighbor database...")
        
        manager = get_neighbor_manager()
        
        data = {
            "metadata": {
                "description": "Pre-computed neighbor relationships for SocialMapper",
                "version": "1.0",
                "generated_by": "SocialMapper neighbor optimization system",
                "data_source": "US Census Bureau TIGER/Line Shapefiles",
                "computation_method": "Spatial analysis using DuckDB and GeoPandas",
                "database_type": "dedicated_neighbor_database"
            },
            "state_neighbors": {},
            "county_neighbors": {}
        }
        
        # Extract state neighbors
        if include_states:
            logger.info("Extracting state neighbor relationships...")
            state_data = manager.db.conn.execute("""
                SELECT state_fips, neighbor_state_fips, relationship_type
                FROM state_neighbors
                ORDER BY state_fips, neighbor_state_fips
            """).fetchall()
            
            for state_fips, neighbor_state, rel_type in state_data:
                if state_fips not in data["state_neighbors"]:
                    data["state_neighbors"][state_fips] = []
                data["state_neighbors"][state_fips].append({
                    "neighbor_state": neighbor_state,
                    "relationship_type": rel_type
                })
            
            data["metadata"]["state_relationships"] = len(state_data)
            logger.info(f"Extracted {len(state_data)} state relationships")
        
        # Extract county neighbors
        if include_counties:
            logger.info("Extracting county neighbor relationships...")
            
            # Build query with optional state filtering
            query = """
                SELECT state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, 
                       relationship_type, shared_boundary_length
                FROM county_neighbors
            """
            
            if state_fips_list:
                placeholders = ','.join(['?' for _ in state_fips_list])
                query += f" WHERE state_fips IN ({placeholders})"
                county_data = manager.db.conn.execute(query, state_fips_list).fetchall()
            else:
                county_data = manager.db.conn.execute(query).fetchall()
            
            for state_fips, county_fips, neighbor_state, neighbor_county, rel_type, boundary_length in county_data:
                county_key = f"{state_fips}{county_fips}"
                
                if county_key not in data["county_neighbors"]:
                    data["county_neighbors"][county_key] = {
                        "state_fips": state_fips,
                        "county_fips": county_fips,
                        "neighbors": []
                    }
                
                data["county_neighbors"][county_key]["neighbors"].append({
                    "state_fips": neighbor_state,
                    "county_fips": neighbor_county,
                    "shared_boundary_length": round(boundary_length, 6) if boundary_length else None,
                    "relationship_type": rel_type
                })
            
            data["metadata"]["county_relationships"] = len(county_data)
            data["metadata"]["counties_with_data"] = len(data["county_neighbors"])
            logger.info(f"Extracted {len(county_data)} county relationships for {len(data['county_neighbors'])} counties")
        
        # Add filtering info to metadata
        if state_fips_list:
            data["metadata"]["filtered_states"] = state_fips_list
            data["metadata"]["scope"] = f"Filtered to {len(state_fips_list)} states"
        else:
            data["metadata"]["scope"] = "Full United States"
        
        return data
    
    def _export_json(self, data: Dict, compressed: bool, compact: bool) -> Path:
        """Export data as JSON."""
        # Determine filename
        suffix = ""
        if compact:
            suffix += "_compact"
        if compressed:
            suffix += ".json.gz"
        else:
            suffix += ".json"
        
        filename = f"neighbor_data{suffix}"
        filepath = self.output_dir / filename
        
        logger.info(f"Exporting JSON: {filename}")
        
        # Write JSON
        if compressed:
            # Write to temporary file first, then compress
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                if compact:
                    json.dump(data, tmp_file, separators=(',', ':'))
                else:
                    json.dump(data, tmp_file, indent=2)
                tmp_path = tmp_file.name
            
            # Compress the file
            with open(tmp_path, 'rb') as f_in:
                with gzip.open(filepath, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Clean up temp file
            os.unlink(tmp_path)
        else:
            # Write directly
            with open(filepath, 'w') as f:
                if compact:
                    json.dump(data, f, separators=(',', ':'))
                else:
                    json.dump(data, f, indent=2)
        
        file_size = filepath.stat().st_size
        logger.info(f"JSON export complete: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return filepath
    
    def _export_duckdb(self, data: Dict) -> Path:
        """Export data as DuckDB database."""
        filepath = self.output_dir / "neighbor_data.duckdb"
        
        logger.info("Exporting DuckDB database...")
        
        # Remove existing file
        if filepath.exists():
            filepath.unlink()
        
        # Create new database
        conn = duckdb.connect(str(filepath))
        
        try:
            # Create state neighbors table
            conn.execute("""
                CREATE TABLE state_neighbors (
                    state_fips VARCHAR(2) NOT NULL,
                    neighbor_state_fips VARCHAR(2) NOT NULL,
                    relationship_type VARCHAR(20) DEFAULT 'adjacent',
                    PRIMARY KEY(state_fips, neighbor_state_fips)
                );
            """)
            
            # Create county neighbors table
            conn.execute("""
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
            
            # Create metadata table
            conn.execute("""
                CREATE TABLE export_metadata (
                    key VARCHAR NOT NULL PRIMARY KEY,
                    value VARCHAR NOT NULL
                );
            """)
            
            # Insert state data
            if data["state_neighbors"]:
                state_rows = []
                for state_fips, neighbors in data["state_neighbors"].items():
                    for neighbor in neighbors:
                        state_rows.append((
                            state_fips,
                            neighbor["neighbor_state"],
                            neighbor["relationship_type"]
                        ))
                
                conn.executemany(
                    "INSERT INTO state_neighbors (state_fips, neighbor_state_fips, relationship_type) VALUES (?, ?, ?)",
                    state_rows
                )
                logger.info(f"Inserted {len(state_rows)} state relationships")
            
            # Insert county data
            if data["county_neighbors"]:
                county_rows = []
                for county_key, county_info in data["county_neighbors"].items():
                    state_fips = county_info["state_fips"]
                    county_fips = county_info["county_fips"]
                    
                    for neighbor in county_info["neighbors"]:
                        county_rows.append((
                            state_fips,
                            county_fips,
                            neighbor["state_fips"],
                            neighbor["county_fips"],
                            neighbor["relationship_type"],
                            neighbor["shared_boundary_length"]
                        ))
                
                conn.executemany("""
                    INSERT INTO county_neighbors 
                    (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, county_rows)
                logger.info(f"Inserted {len(county_rows)} county relationships")
            
            # Insert metadata
            metadata_rows = [(k, str(v)) for k, v in data["metadata"].items()]
            conn.executemany(
                "INSERT INTO export_metadata (key, value) VALUES (?, ?)",
                metadata_rows
            )
            
            # Create indexes for performance
            conn.execute("CREATE INDEX idx_state_neighbors_state ON state_neighbors(state_fips);")
            conn.execute("CREATE INDEX idx_county_neighbors_county ON county_neighbors(state_fips, county_fips);")
            conn.execute("CREATE INDEX idx_county_neighbors_neighbor ON county_neighbors(neighbor_state_fips, neighbor_county_fips);")
            
        finally:
            conn.close()
        
        file_size = filepath.stat().st_size
        logger.info(f"DuckDB export complete: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)")
        
        return filepath
    
    def _export_sqlite(self, data: Dict) -> Path:
        """Export data as SQLite database."""
        import sqlite3
        
        filepath = self.output_dir / "neighbor_data.sqlite"
        
        logger.info("Exporting SQLite database...")
        
        # Remove existing file
        if filepath.exists():
            filepath.unlink()
        
        # Create new database
        conn = sqlite3.connect(str(filepath))
        
        try:
            # Create tables
            conn.execute("""
                CREATE TABLE state_neighbors (
                    state_fips TEXT NOT NULL,
                    neighbor_state_fips TEXT NOT NULL,
                    relationship_type TEXT DEFAULT 'adjacent',
                    PRIMARY KEY(state_fips, neighbor_state_fips)
                );
            """)
            
            conn.execute("""
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
            
            conn.execute("""
                CREATE TABLE export_metadata (
                    key TEXT NOT NULL PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            
            # Insert data (same logic as DuckDB)
            if data["state_neighbors"]:
                state_rows = []
                for state_fips, neighbors in data["state_neighbors"].items():
                    for neighbor in neighbors:
                        state_rows.append((
                            state_fips,
                            neighbor["neighbor_state"],
                            neighbor["relationship_type"]
                        ))
                
                conn.executemany(
                    "INSERT INTO state_neighbors (state_fips, neighbor_state_fips, relationship_type) VALUES (?, ?, ?)",
                    state_rows
                )
            
            if data["county_neighbors"]:
                county_rows = []
                for county_key, county_info in data["county_neighbors"].items():
                    state_fips = county_info["state_fips"]
                    county_fips = county_info["county_fips"]
                    
                    for neighbor in county_info["neighbors"]:
                        county_rows.append((
                            state_fips,
                            county_fips,
                            neighbor["state_fips"],
                            neighbor["county_fips"],
                            neighbor["relationship_type"],
                            neighbor["shared_boundary_length"]
                        ))
                
                conn.executemany("""
                    INSERT INTO county_neighbors 
                    (state_fips, county_fips, neighbor_state_fips, neighbor_county_fips, relationship_type, shared_boundary_length)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, county_rows)
            
            # Insert metadata
            metadata_rows = [(k, str(v)) for k, v in data["metadata"].items()]
            conn.executemany(
                "INSERT INTO export_metadata (key, value) VALUES (?, ?)",
                metadata_rows
            )
            
            # Create indexes
            conn.execute("CREATE INDEX idx_state_neighbors_state ON state_neighbors(state_fips);")
            conn.execute("CREATE INDEX idx_county_neighbors_county ON county_neighbors(state_fips, county_fips);")
            
            conn.commit()
            
        finally:
            conn.close()
        
        file_size = filepath.stat().st_size
        logger.info(f"SQLite export complete: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)")
        
        return filepath
    
    def _create_export_summary(self, exported_files: Dict[str, Path], data: Dict):
        """Create a summary of the export."""
        summary_path = self.output_dir / "export_summary.txt"
        
        with open(summary_path, 'w') as f:
            f.write("NEIGHBOR DATA EXPORT SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            # Metadata
            f.write("Data Information:\n")
            for key, value in data["metadata"].items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            # File sizes
            f.write("Exported Files:\n")
            for format_name, filepath in exported_files.items():
                if filepath.exists():
                    size = filepath.stat().st_size
                    f.write(f"  {format_name}: {filepath.name}\n")
                    f.write(f"    Size: {size:,} bytes ({size/1024:.1f} KB")
                    if size > 1024*1024:
                        f.write(f", {size/(1024*1024):.2f} MB")
                    f.write(")\n")
            f.write("\n")
            
            # Recommendations
            f.write("Usage Recommendations:\n")
            f.write("  • For maximum performance: Use neighbor_data.duckdb\n")
            f.write("  • For smallest size: Use neighbor_data_compact.json.gz\n")
            f.write("  • For human readability: Use neighbor_data.json\n")
            f.write("  • For compatibility: Use neighbor_data.sqlite\n")
        
        logger.info(f"Export summary saved to: {summary_path}")


def export_neighbor_data(output_dir: Optional[Path] = None,
                        formats: List[str] = None,
                        state_fips_list: Optional[List[str]] = None) -> Dict[str, Path]:
    """Export neighbor data in specified formats.
    
    Args:
        output_dir: Directory to save files
        formats: List of formats to export. Options: 'json', 'json_compact', 'json_gz', 
                'json_gz_compact', 'duckdb', 'sqlite', 'production'
        state_fips_list: List of state FIPS codes to include. If None, includes all.
        
    Returns:
        Dictionary mapping format names to file paths
    """
    if formats is None:
        formats = ['production']  # Default to production formats
    
    exporter = NeighborExporter(output_dir)
    
    if 'production' in formats:
        return exporter.export_production_formats(state_fips_list=state_fips_list)
    else:
        # Export specific formats
        all_files = exporter.export_all_formats(state_fips_list=state_fips_list)
        return {fmt: path for fmt, path in all_files.items() if fmt in formats}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export neighbor data for distribution")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--formats", nargs="+", 
                       choices=['json', 'json_compact', 'json_gz', 'json_gz_compact', 'duckdb', 'sqlite', 'production', 'all'],
                       default=['production'],
                       help="Formats to export")
    parser.add_argument("--states", nargs="+", help="State FIPS codes to include (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Handle 'all' format
    if 'all' in args.formats:
        args.formats = ['json', 'json_compact', 'json_gz', 'json_gz_compact', 'duckdb', 'sqlite']
    
    # Export
    exported_files = export_neighbor_data(
        output_dir=args.output_dir,
        formats=args.formats,
        state_fips_list=args.states
    )
    
    print("Export completed!")
    for format_name, filepath in exported_files.items():
        size = filepath.stat().st_size
        print(f"  {format_name}: {filepath} ({size:,} bytes)") 