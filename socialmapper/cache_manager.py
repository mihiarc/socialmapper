#!/usr/bin/env python3
"""Cache management utilities for SocialMapper.

This module provides functions to manage, monitor, and clear various caches
used by SocialMapper including geocoding cache, network cache, and census cache.
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from socialmapper.console import get_logger
from socialmapper.isochrone import clear_network_cache
from socialmapper.isochrone import get_global_cache as get_network_cache

logger = get_logger(__name__)


class CacheManager:
    """Centralized cache management for SocialMapper."""

    def __init__(self):
        """Initialize cache manager."""
        self.cache_base_dir = Path("cache")
        self.geocoding_cache_dir = self.cache_base_dir / "geocoding"
        self.network_cache_dir = self.cache_base_dir / "networks"
        self.census_cache_dir = self.cache_base_dir / "census"

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get comprehensive cache statistics for all caches.
        
        Returns:
            Dict containing cache statistics for each cache type
        """
        stats = {
            "summary": {
                "total_size_mb": 0,
                "total_items": 0,
                "last_updated": datetime.now().isoformat()
            },
            "network_cache": self._get_network_cache_stats(),
            "geocoding_cache": self._get_geocoding_cache_stats(),
            "census_cache": self._get_census_cache_stats(),
            "general_cache": self._get_general_cache_stats()
        }

        # Calculate totals
        for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
            cache_stats = stats[cache_type]
            stats["summary"]["total_size_mb"] += cache_stats.get("size_mb", 0)
            stats["summary"]["total_items"] += cache_stats.get("item_count", 0)

        return stats

    def _get_network_cache_stats(self) -> dict[str, Any]:
        """Get network cache statistics."""
        try:
            # Get stats from the network cache
            network_cache = get_network_cache()
            cache_stats = network_cache.get_cache_stats()

            # Count files in network cache directory
            network_files = list(self.network_cache_dir.glob("*.pkl.gz")) if self.network_cache_dir.exists() else []

            # Get database info
            db_stats = {}
            db_path = self.network_cache_dir / "cache_index.db"
            if db_path.exists():
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM networks")
                        db_count = cursor.fetchone()[0]

                        cursor = conn.execute("""
                            SELECT MIN(created_at), MAX(created_at), 
                                   SUM(node_count), SUM(edge_count)
                            FROM networks
                        """)
                        min_created, max_created, total_nodes, total_edges = cursor.fetchone()

                        db_stats = {
                            "indexed_networks": db_count,
                            "oldest_entry": datetime.fromtimestamp(min_created).isoformat() if min_created else None,
                            "newest_entry": datetime.fromtimestamp(max_created).isoformat() if max_created else None,
                            "total_nodes": total_nodes or 0,
                            "total_edges": total_edges or 0
                        }
                except Exception as e:
                    logger.warning(f"Failed to read network cache database: {e}")

            return {
                "size_mb": cache_stats.total_size_mb,
                "item_count": len(network_files),
                "cache_hits": cache_stats.cache_hits,
                "cache_misses": cache_stats.cache_misses,
                "hit_rate_percent": (cache_stats.cache_hits / cache_stats.total_requests * 100) if cache_stats.total_requests > 0 else 0,
                "avg_retrieval_time_ms": cache_stats.avg_retrieval_time_ms,
                "compression_ratio": cache_stats.compression_ratio,
                "status": "active" if network_files else "empty",
                "location": str(self.network_cache_dir),
                **db_stats
            }
        except Exception as e:
            logger.error(f"Failed to get network cache stats: {e}")
            return {
                "size_mb": 0,
                "item_count": 0,
                "status": "error",
                "error": str(e)
            }

    def _get_geocoding_cache_stats(self) -> dict[str, Any]:
        """Get geocoding cache statistics."""
        try:
            # Check if geocoding cache file exists
            cache_file = self.geocoding_cache_dir / "address_cache.parquet"

            if cache_file.exists():
                file_size_mb = cache_file.stat().st_size / (1024 * 1024)

                # Try to load and count entries
                try:
                    import pandas as pd
                    df = pd.read_parquet(cache_file)
                    item_count = len(df)

                    # Get age statistics
                    if 'timestamp' in df.columns:
                        timestamps = pd.to_datetime(df['timestamp'])
                        oldest = timestamps.min()
                        newest = timestamps.max()
                    else:
                        oldest = newest = None

                except Exception as e:
                    logger.warning(f"Failed to read geocoding cache file: {e}")
                    item_count = 0
                    oldest = newest = None

                return {
                    "size_mb": file_size_mb,
                    "item_count": item_count,
                    "status": "active",
                    "location": str(self.geocoding_cache_dir),
                    "oldest_entry": oldest.isoformat() if oldest else None,
                    "newest_entry": newest.isoformat() if newest else None
                }
            else:
                return {
                    "size_mb": 0,
                    "item_count": 0,
                    "status": "empty",
                    "location": str(self.geocoding_cache_dir)
                }
        except Exception as e:
            logger.error(f"Failed to get geocoding cache stats: {e}")
            return {
                "size_mb": 0,
                "item_count": 0,
                "status": "error",
                "error": str(e)
            }

    def _get_census_cache_stats(self) -> dict[str, Any]:
        """Get census cache statistics."""
        try:
            # Check file-based census cache in multiple possible locations
            census_cache_size = 0
            census_cache_files = 0

            # Check main census cache directory
            if self.census_cache_dir.exists():
                for cache_file in self.census_cache_dir.glob("*.cache"):
                    census_cache_size += cache_file.stat().st_size
                    census_cache_files += 1

            # Check .census_cache directory (default location)
            alt_census_dir = Path(".census_cache")
            if alt_census_dir.exists():
                for cache_file in alt_census_dir.glob("*.cache"):
                    census_cache_size += cache_file.stat().st_size
                    census_cache_files += 1

            return {
                "size_mb": census_cache_size / (1024 * 1024),
                "item_count": census_cache_files,
                "status": "active" if census_cache_files > 0 else "empty",
                "location": str(self.census_cache_dir)
            }
        except Exception as e:
            logger.error(f"Failed to get census cache stats: {e}")
            return {
                "size_mb": 0,
                "item_count": 0,
                "status": "error",
                "error": str(e)
            }

    def _get_general_cache_stats(self) -> dict[str, Any]:
        """Get general cache statistics (JSON files in cache root)."""
        try:
            json_files = list(self.cache_base_dir.glob("*.json")) if self.cache_base_dir.exists() else []
            total_size = sum(f.stat().st_size for f in json_files)

            # Get age of files
            if json_files:
                oldest_mtime = min(f.stat().st_mtime for f in json_files)
                newest_mtime = max(f.stat().st_mtime for f in json_files)
                oldest = datetime.fromtimestamp(oldest_mtime)
                newest = datetime.fromtimestamp(newest_mtime)
            else:
                oldest = newest = None

            return {
                "size_mb": total_size / (1024 * 1024),
                "item_count": len(json_files),
                "status": "active" if json_files else "empty",
                "location": str(self.cache_base_dir),
                "oldest_entry": oldest.isoformat() if oldest else None,
                "newest_entry": newest.isoformat() if newest else None
            }
        except Exception as e:
            logger.error(f"Failed to get general cache stats: {e}")
            return {
                "size_mb": 0,
                "item_count": 0,
                "status": "error",
                "error": str(e)
            }

    def clear_network_cache(self) -> dict[str, Any]:
        """Clear the network cache.
        
        Returns:
            Dict with operation status and details
        """
        try:
            # Use the built-in clear function
            clear_network_cache()

            return {
                "success": True,
                "message": "Network cache cleared successfully",
                "cleared_size_mb": self._get_network_cache_stats()["size_mb"]
            }
        except Exception as e:
            logger.error(f"Failed to clear network cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def clear_geocoding_cache(self) -> dict[str, Any]:
        """Clear the geocoding cache.
        
        Returns:
            Dict with operation status and details
        """
        try:
            stats_before = self._get_geocoding_cache_stats()

            # Clear geocoding cache directory
            if self.geocoding_cache_dir.exists():
                shutil.rmtree(self.geocoding_cache_dir)
                self.geocoding_cache_dir.mkdir(parents=True, exist_ok=True)

            return {
                "success": True,
                "message": "Geocoding cache cleared successfully",
                "cleared_size_mb": stats_before["size_mb"],
                "cleared_items": stats_before["item_count"]
            }
        except Exception as e:
            logger.error(f"Failed to clear geocoding cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def clear_census_cache(self) -> dict[str, Any]:
        """Clear the census cache.
        
        Returns:
            Dict with operation status and details
        """
        try:
            stats_before = self._get_census_cache_stats()

            # Clear file-based census cache in both locations
            if self.census_cache_dir.exists():
                shutil.rmtree(self.census_cache_dir)
                self.census_cache_dir.mkdir(parents=True, exist_ok=True)

            # Also clear default .census_cache directory
            alt_census_dir = Path(".census_cache")
            if alt_census_dir.exists():
                shutil.rmtree(alt_census_dir)

            return {
                "success": True,
                "message": "Census cache cleared successfully",
                "cleared_size_mb": stats_before["size_mb"],
                "cleared_items": stats_before["item_count"]
            }
        except Exception as e:
            logger.error(f"Failed to clear census cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def clear_all_caches(self) -> dict[str, Any]:
        """Clear all caches.
        
        Returns:
            Dict with operation status and details for each cache
        """
        results = {
            "network": self.clear_network_cache(),
            "geocoding": self.clear_geocoding_cache(),
            "census": self.clear_census_cache(),
            "general": self._clear_general_cache()
        }

        # Calculate totals
        total_cleared_mb = sum(
            result.get("cleared_size_mb", 0)
            for result in results.values()
        )

        all_successful = all(
            result.get("success", False)
            for result in results.values()
        )

        results["summary"] = {
            "success": all_successful,
            "total_cleared_mb": total_cleared_mb,
            "timestamp": datetime.now().isoformat()
        }

        return results

    def _clear_general_cache(self) -> dict[str, Any]:
        """Clear general cache files (JSON files in cache root).
        
        Returns:
            Dict with operation status and details
        """
        try:
            stats_before = self._get_general_cache_stats()

            # Remove JSON files in cache root
            if self.cache_base_dir.exists():
                json_files = list(self.cache_base_dir.glob("*.json"))
                for json_file in json_files:
                    json_file.unlink()

            return {
                "success": True,
                "message": "General cache cleared successfully",
                "cleared_size_mb": stats_before["size_mb"],
                "cleared_items": stats_before["item_count"]
            }
        except Exception as e:
            logger.error(f"Failed to clear general cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def cleanup_expired_entries(self) -> dict[str, Any]:
        """Clean up expired entries from all caches.
        
        Returns:
            Dict with cleanup statistics
        """
        results = {}

        # Census cache doesn't have built-in expiration for file-based cache
        results["census"] = {
            "success": True,
            "message": "Census file cache doesn't have automatic expiration"
        }

        # Network cache doesn't have built-in expiration
        results["network"] = {
            "success": True,
            "message": "Network cache uses LRU eviction, no expiration cleanup needed"
        }

        # Geocoding cache cleanup handled by AddressCache on load
        results["geocoding"] = {
            "success": True,
            "message": "Geocoding cache cleans expired entries on load"
        }

        return results


# Convenience functions for direct use
def get_cache_statistics() -> dict[str, Any]:
    """Get comprehensive cache statistics.
    
    Returns:
        Dict containing cache statistics for all cache types
    """
    manager = CacheManager()
    return manager.get_cache_statistics()


def clear_all_caches() -> dict[str, Any]:
    """Clear all SocialMapper caches.
    
    Returns:
        Dict with operation status and details
    """
    manager = CacheManager()
    return manager.clear_all_caches()


def clear_geocoding_cache() -> dict[str, Any]:
    """Clear the geocoding cache.
    
    Returns:
        Dict with operation status and details
    """
    manager = CacheManager()
    return manager.clear_geocoding_cache()


def clear_census_cache() -> dict[str, Any]:
    """Clear the census cache.
    
    Returns:
        Dict with operation status and details
    """
    manager = CacheManager()
    return manager.clear_census_cache()


def cleanup_expired_cache_entries() -> dict[str, Any]:
    """Clean up expired entries from all caches.
    
    Returns:
        Dict with cleanup statistics
    """
    manager = CacheManager()
    return manager.cleanup_expired_entries()


if __name__ == "__main__":
    # Example usage
    from rich.console import Console
    from rich.json import JSON
    from rich.table import Table

    console = Console()

    # Get cache statistics
    stats = get_cache_statistics()

    # Display summary
    console.print("\n[bold cyan]SocialMapper Cache Statistics[/bold cyan]\n")

    table = Table(title="Cache Summary")
    table.add_column("Cache Type", style="cyan")
    table.add_column("Size (MB)", justify="right", style="green")
    table.add_column("Items", justify="right", style="yellow")
    table.add_column("Status", style="magenta")

    for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
        cache_stats = stats[cache_type]
        table.add_row(
            cache_type.replace("_", " ").title(),
            f"{cache_stats.get('size_mb', 0):.2f}",
            str(cache_stats.get('item_count', 0)),
            cache_stats.get('status', 'unknown')
        )

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{stats['summary']['total_size_mb']:.2f}[/bold]",
        f"[bold]{stats['summary']['total_items']}[/bold]",
        ""
    )

    console.print(table)

    # Show detailed stats as JSON
    console.print("\n[bold cyan]Detailed Statistics:[/bold cyan]")
    console.print(JSON.from_data(stats))
