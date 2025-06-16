"""Data repository implementations for census data persistence.

Provides multiple storage backends:
- SQLite for local persistence
- No-op repository for disabled persistence
- Future: PostgreSQL, DuckDB, etc.
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from ..domain.entities import BoundaryData, CensusDataPoint, CensusVariable, NeighborRelationship


class RepositoryError(Exception):
    """Base exception for repository errors."""


class SQLiteRepository:
    """SQLite-based repository for census data persistence.

    Provides local storage for census data, boundaries, and neighbor relationships
    with proper indexing for efficient queries.
    """

    def __init__(self, db_path: str | None = None, logger: logging.Logger | None = None):
        """Initialize SQLite repository.

        Args:
            db_path: Path to SQLite database file (None for in-memory)
            logger: Logger instance
        """
        self._db_path = db_path or ":memory:"
        self._logger = logger or logging.getLogger(__name__)

        # Ensure directory exists for file-based databases
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

    def save_census_data(self, data_points: list[CensusDataPoint]) -> None:
        """Persist census data points.

        Args:
            data_points: List of census data points to save
        """
        if not data_points:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Prepare data for bulk insert
            records = []
            for point in data_points:
                records.append(
                    (
                        point.geoid,
                        point.variable.code,
                        point.variable.name,
                        point.variable.description,
                        point.variable.unit,
                        point.value,
                        point.margin_of_error,
                        point.year,
                        point.dataset,
                        datetime.now().isoformat(),
                    )
                )

            # Use INSERT OR REPLACE to handle duplicates
            cursor.executemany(
                """
                INSERT OR REPLACE INTO census_data 
                (geoid, variable_code, variable_name, variable_description, variable_unit,
                 value, margin_of_error, year, dataset, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            self._logger.debug(f"Saved {len(data_points)} census data points")

    def get_census_data(
        self, geoids: list[str], variable_codes: list[str]
    ) -> list[CensusDataPoint]:
        """Retrieve stored census data.

        Args:
            geoids: List of geographic unit identifiers
            variable_codes: List of variable codes

        Returns:
            List of matching census data points
        """
        if not geoids or not variable_codes:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build parameterized query
            geoid_placeholders = ",".join("?" * len(geoids))
            var_placeholders = ",".join("?" * len(variable_codes))

            query = f"""
                SELECT geoid, variable_code, variable_name, variable_description, 
                       variable_unit, value, margin_of_error, year, dataset
                FROM census_data 
                WHERE geoid IN ({geoid_placeholders}) 
                AND variable_code IN ({var_placeholders})
            """

            cursor.execute(query, geoids + variable_codes)
            rows = cursor.fetchall()

            # Convert to domain entities
            data_points = []
            for row in rows:
                variable = CensusVariable(code=row[1], name=row[2], description=row[3], unit=row[4])

                data_point = CensusDataPoint(
                    geoid=row[0],
                    variable=variable,
                    value=row[5],
                    margin_of_error=row[6],
                    year=row[7],
                    dataset=row[8],
                )
                data_points.append(data_point)

            self._logger.debug(f"Retrieved {len(data_points)} census data points")
            return data_points

    def save_boundaries(self, boundaries: list[BoundaryData]) -> None:
        """Persist boundary data.

        Args:
            boundaries: List of boundary data to save
        """
        if not boundaries:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            records = []
            for boundary in boundaries:
                # Serialize geometry as JSON
                geometry_json = json.dumps(boundary.geometry) if boundary.geometry else None

                records.append(
                    (
                        boundary.geoid,
                        geometry_json,
                        boundary.area_land,
                        boundary.area_water,
                        datetime.now().isoformat(),
                    )
                )

            cursor.executemany(
                """
                INSERT OR REPLACE INTO boundaries 
                (geoid, geometry, area_land, area_water, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            self._logger.debug(f"Saved {len(boundaries)} boundary records")

    def get_boundaries(self, geoids: list[str]) -> list[BoundaryData]:
        """Retrieve stored boundary data.

        Args:
            geoids: List of geographic unit identifiers

        Returns:
            List of matching boundary data
        """
        if not geoids:
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            placeholders = ",".join("?" * len(geoids))
            query = f"""
                SELECT geoid, geometry, area_land, area_water
                FROM boundaries 
                WHERE geoid IN ({placeholders})
            """

            cursor.execute(query, geoids)
            rows = cursor.fetchall()

            boundaries = []
            for row in rows:
                # Deserialize geometry from JSON
                geometry = json.loads(row[1]) if row[1] else None

                boundary = BoundaryData(
                    geoid=row[0], geometry=geometry, area_land=row[2], area_water=row[3]
                )
                boundaries.append(boundary)

            self._logger.debug(f"Retrieved {len(boundaries)} boundary records")
            return boundaries

    def save_neighbor_relationships(self, relationships: list[NeighborRelationship]) -> None:
        """Persist neighbor relationships.

        Args:
            relationships: List of neighbor relationships to save
        """
        if not relationships:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            records = []
            for rel in relationships:
                records.append(
                    (
                        rel.source_geoid,
                        rel.neighbor_geoid,
                        rel.relationship_type,
                        rel.shared_boundary_length,
                        datetime.now().isoformat(),
                    )
                )

            cursor.executemany(
                """
                INSERT OR REPLACE INTO neighbor_relationships 
                (source_geoid, neighbor_geoid, relationship_type, shared_boundary_length, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            self._logger.debug(f"Saved {len(relationships)} neighbor relationships")

    def get_neighbors(self, geoid: str) -> list[NeighborRelationship]:
        """Get neighbor relationships for a geographic unit.

        Args:
            geoid: Geographic unit identifier

        Returns:
            List of neighbor relationships
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT source_geoid, neighbor_geoid, relationship_type, shared_boundary_length
                FROM neighbor_relationships 
                WHERE source_geoid = ?
            """,
                (geoid,),
            )

            rows = cursor.fetchall()

            relationships = []
            for row in rows:
                rel = NeighborRelationship(
                    source_geoid=row[0],
                    neighbor_geoid=row[1],
                    relationship_type=row[2],
                    shared_boundary_length=row[3],
                )
                relationships.append(rel)

            self._logger.debug(f"Retrieved {len(relationships)} neighbor relationships for {geoid}")
            return relationships

    def cleanup_old_data(self, days_old: int = 30) -> int:
        """Remove data older than specified days.

        Args:
            days_old: Remove data older than this many days

        Returns:
            Number of records removed
        """
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
        cutoff_iso = cutoff_date.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Clean up old census data
            cursor.execute("DELETE FROM census_data WHERE created_at < ?", (cutoff_iso,))
            census_removed = cursor.rowcount

            # Clean up old boundaries
            cursor.execute("DELETE FROM boundaries WHERE created_at < ?", (cutoff_iso,))
            boundary_removed = cursor.rowcount

            # Clean up old neighbor relationships
            cursor.execute("DELETE FROM neighbor_relationships WHERE created_at < ?", (cutoff_iso,))
            neighbor_removed = cursor.rowcount

            conn.commit()

            total_removed = census_removed + boundary_removed + neighbor_removed
            self._logger.info(f"Cleaned up {total_removed} old records")

            return total_removed

    def get_stats(self) -> dict[str, Any]:
        """Get repository statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Count records in each table
            cursor.execute("SELECT COUNT(*) FROM census_data")
            census_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM boundaries")
            boundary_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM neighbor_relationships")
            neighbor_count = cursor.fetchone()[0]

            # Get database size (for file-based databases)
            db_size = None
            if self._db_path != ":memory:":
                try:
                    db_size = Path(self._db_path).stat().st_size
                except OSError:
                    pass

            return {
                "census_data_count": census_count,
                "boundary_count": boundary_count,
                "neighbor_count": neighbor_count,
                "database_size_bytes": db_size,
                "database_path": self._db_path,
            }

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self._db_path)
        try:
            # Enable foreign keys and WAL mode for better performance
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Census data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS census_data (
                    geoid TEXT NOT NULL,
                    variable_code TEXT NOT NULL,
                    variable_name TEXT,
                    variable_description TEXT,
                    variable_unit TEXT,
                    value REAL,
                    margin_of_error REAL,
                    year INTEGER,
                    dataset TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (geoid, variable_code, year, dataset)
                )
            """)

            # Boundaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS boundaries (
                    geoid TEXT PRIMARY KEY,
                    geometry TEXT,
                    area_land REAL,
                    area_water REAL,
                    created_at TEXT NOT NULL
                )
            """)

            # Neighbor relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS neighbor_relationships (
                    source_geoid TEXT NOT NULL,
                    neighbor_geoid TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    shared_boundary_length REAL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source_geoid, neighbor_geoid, relationship_type)
                )
            """)

            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_census_geoid ON census_data(geoid)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_census_variable ON census_data(variable_code)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_census_year ON census_data(year)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_neighbor_source ON neighbor_relationships(source_geoid)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_neighbor_target ON neighbor_relationships(neighbor_geoid)"
            )

            conn.commit()
            self._logger.debug("Database schema initialized")


class NoOpRepository:
    """No-operation repository for disabled persistence.

    Implements the repository interface but doesn't actually store anything.
    Useful when persistence is disabled or for testing.
    """

    def save_census_data(self, data_points: list[CensusDataPoint]) -> None:
        """Does nothing (no persistence)."""

    def get_census_data(
        self, geoids: list[str], variable_codes: list[str]
    ) -> list[CensusDataPoint]:
        """Always returns empty list (no stored data)."""
        return []

    def save_boundaries(self, boundaries: list[BoundaryData]) -> None:
        """Does nothing (no persistence)."""

    def get_boundaries(self, geoids: list[str]) -> list[BoundaryData]:
        """Always returns empty list (no stored data)."""
        return []

    def save_neighbor_relationships(self, relationships: list[NeighborRelationship]) -> None:
        """Does nothing (no persistence)."""

    def get_neighbors(self, geoid: str) -> list[NeighborRelationship]:
        """Always returns empty list (no stored data)."""
        return []


class InMemoryRepository:
    """In-memory repository for testing and development.

    Stores data in memory dictionaries. Data is lost when the process ends.
    Useful for testing and development where persistence isn't needed.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._census_data: dict[str, CensusDataPoint] = {}
        self._boundaries: dict[str, BoundaryData] = {}
        self._neighbors: dict[str, list[NeighborRelationship]] = {}

    def save_census_data(self, data_points: list[CensusDataPoint]) -> None:
        """Store census data in memory."""
        for point in data_points:
            # Create composite key
            key = f"{point.geoid}:{point.variable.code}:{point.year}:{point.dataset}"
            self._census_data[key] = point

    def get_census_data(
        self, geoids: list[str], variable_codes: list[str]
    ) -> list[CensusDataPoint]:
        """Retrieve census data from memory."""
        results = []

        for point in self._census_data.values():
            if point.geoid in geoids and point.variable.code in variable_codes:
                results.append(point)

        return results

    def save_boundaries(self, boundaries: list[BoundaryData]) -> None:
        """Store boundaries in memory."""
        for boundary in boundaries:
            self._boundaries[boundary.geoid] = boundary

    def get_boundaries(self, geoids: list[str]) -> list[BoundaryData]:
        """Retrieve boundaries from memory."""
        results = []

        for geoid in geoids:
            if geoid in self._boundaries:
                results.append(self._boundaries[geoid])

        return results

    def save_neighbor_relationships(self, relationships: list[NeighborRelationship]) -> None:
        """Store neighbor relationships in memory."""
        for rel in relationships:
            if rel.source_geoid not in self._neighbors:
                self._neighbors[rel.source_geoid] = []
            self._neighbors[rel.source_geoid].append(rel)

    def get_neighbors(self, geoid: str) -> list[NeighborRelationship]:
        """Retrieve neighbor relationships from memory."""
        return self._neighbors.get(geoid, [])
