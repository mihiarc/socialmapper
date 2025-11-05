#!/usr/bin/env python3
"""Cache management utilities for SocialMapper.

This module provides functions to manage, monitor, and clear
various caches used by SocialMapper including geocoding cache,
network cache, and census cache.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from socialmapper.isochrone import clear_network_cache
from socialmapper.isochrone import get_cache_stats as get_network_stats

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache management system for SocialMapper.

    Provides unified interface for managing multiple cache types
    including geocoding, network routing, and census data caches.
    Supports statistics gathering, selective clearing, and cleanup
    operations across all cache systems.

    Attributes
    ----------
    cache_base_dir : pathlib.Path
        Root directory for all cache storage.
    geocoding_cache_dir : pathlib.Path
        Directory for geocoding cache storage.
    network_cache_dir : pathlib.Path
        Directory for network routing cache storage.
    census_cache_dir : pathlib.Path
        Directory for census data cache storage.

    Examples
    --------
    >>> manager = CacheManager()
    >>> stats = manager.get_cache_statistics()
    >>> print(f"Total: {stats['summary']['total_size_mb']:.1f} MB")
    Total: 45.3 MB
    """

    def __init__(self):
        """
        Initialize cache manager with default directory structure.

        Sets up cache directory paths for all subsystems (geocoding,
        network, census, general). Directories are created as needed
        during cache operations.
        """
        self.cache_base_dir = Path("cache")
        self.geocoding_cache_dir = self.cache_base_dir / "geocoding"
        self.network_cache_dir = self.cache_base_dir / "networks"
        self.census_cache_dir = self.cache_base_dir / "census"

    def get_cache_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics for all cache subsystems.

        Collects size, item count, and status information from
        all cache types and aggregates into summary totals.

        Returns
        -------
        dict
            Nested dictionary with keys 'summary',
            'network_cache', 'geocoding_cache', 'census_cache',
            'general_cache'. Summary contains 'total_size_mb',
            'total_items', 'last_updated'. Each cache type
            contains 'size_mb', 'item_count', 'status',
            'location'.

        Examples
        --------
        >>> manager = CacheManager()
        >>> stats = manager.get_cache_statistics()
        >>> stats['summary']['total_size_mb']
        45.3
        >>> stats['network_cache']['item_count']
        127
        """
        stats = {
            "summary": {
                "total_size_mb": 0,
                "total_items": 0,
                "last_updated": datetime.now().isoformat(),
            },
            "network_cache": self._get_network_cache_stats(),
            "geocoding_cache": self._get_geocoding_cache_stats(),
            "census_cache": self._get_census_cache_stats(),
            "general_cache": self._get_general_cache_stats(),
        }

        # Calculate totals
        for cache_type in ["network_cache", "geocoding_cache", "census_cache", "general_cache"]:
            cache_stats = stats[cache_type]
            stats["summary"]["total_size_mb"] += cache_stats.get("size_mb", 0)
            stats["summary"]["total_items"] += cache_stats.get("item_count", 0)

        return stats

    def _get_network_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics for network routing cache.

        Returns
        -------
        dict
            Dictionary with keys 'size_mb', 'item_count', 'status',
            'location'. Status is 'active', 'empty', or 'error'.
        """
        try:
            # Get stats from the simplified cache
            cache_stats = get_network_stats()

            return {
                "size_mb": cache_stats.get("size_mb", 0),
                "item_count": cache_stats.get("count", 0),
                "status": "active" if cache_stats.get("count", 0) > 0 else "empty",
                "location": str(self.network_cache_dir),
            }
        except Exception as e:
            logger.error(f"Failed to get network cache stats: {e}")
            return {"size_mb": 0, "item_count": 0, "status": "error", "error": str(e)}

    def _get_geocoding_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics for geocoding cache.

        Returns
        -------
        dict
            Dictionary with keys 'size_mb', 'item_count', 'status',
            'location'. Status is 'active', 'empty', or 'error'.
        """
        try:
            # Get size of geocoding cache directory (diskcache format)
            if self.geocoding_cache_dir.exists():
                total_size = sum(
                    f.stat().st_size
                    for f in self.geocoding_cache_dir.rglob("*")
                    if f.is_file()
                )
                file_count = len(list(self.geocoding_cache_dir.rglob("*")))

                return {
                    "size_mb": total_size / (1024 * 1024),
                    "item_count": file_count,
                    "status": "active" if file_count > 0 else "empty",
                    "location": str(self.geocoding_cache_dir),
                }
            else:
                return {
                    "size_mb": 0,
                    "item_count": 0,
                    "status": "empty",
                    "location": str(self.geocoding_cache_dir),
                }
        except Exception as e:
            logger.error(f"Failed to get geocoding cache stats: {e}")
            return {"size_mb": 0, "item_count": 0, "status": "error", "error": str(e)}

    def _get_census_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics for census data cache.

        Returns
        -------
        dict
            Dictionary with keys 'size_mb', 'item_count', 'status',
            'location'. Status is 'active', 'empty', or 'error'.
        """
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
                "location": str(self.census_cache_dir),
            }
        except Exception as e:
            logger.error(f"Failed to get census cache stats: {e}")
            return {"size_mb": 0, "item_count": 0, "status": "error", "error": str(e)}

    def _get_general_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics for general cache files.

        Analyzes JSON cache files stored in root cache directory.

        Returns
        -------
        dict
            Dictionary with keys 'size_mb', 'item_count', 'status',
            'location', 'oldest_entry', 'newest_entry'. Status is
            'active', 'empty', or 'error'.
        """
        try:
            json_files = (
                list(self.cache_base_dir.glob("*.json")) if self.cache_base_dir.exists() else []
            )
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
                "newest_entry": newest.isoformat() if newest else None,
            }
        except Exception as e:
            logger.error(f"Failed to get general cache stats: {e}")
            return {"size_mb": 0, "item_count": 0, "status": "error", "error": str(e)}

    def clear_network_cache(self) -> dict[str, Any]:
        """
        Clear the network routing cache.

        Removes all cached network graphs and routing data.

        Returns
        -------
        dict
            Dictionary with keys 'success' (bool), 'message'
            (str), 'cleared_size_mb' (float).

        Examples
        --------
        >>> manager = CacheManager()
        >>> result = manager.clear_network_cache()
        >>> result['success']
        True
        """
        try:
            # Use the built-in clear function
            clear_network_cache()

            return {
                "success": True,
                "message": "Network cache cleared successfully",
                "cleared_size_mb": self._get_network_cache_stats()["size_mb"],
            }
        except Exception as e:
            logger.error(f"Failed to clear network cache: {e}")
            return {"success": False, "error": str(e)}

    def clear_geocoding_cache(self) -> dict[str, Any]:
        """
        Clear the geocoding address cache.

        Removes all cached geocoding results and address lookups.

        Returns
        -------
        dict
            Dictionary with keys 'success' (bool), 'message'
            (str), 'cleared_size_mb' (float), 'cleared_items'
            (int).

        Examples
        --------
        >>> manager = CacheManager()
        >>> result = manager.clear_geocoding_cache()
        >>> result['success']
        True
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
                "cleared_items": stats_before["item_count"],
            }
        except Exception as e:
            logger.error(f"Failed to clear geocoding cache: {e}")
            return {"success": False, "error": str(e)}

    def clear_census_cache(self) -> dict[str, Any]:
        """
        Clear the census data cache.

        Removes all cached census API responses and demographic
        data.

        Returns
        -------
        dict
            Dictionary with keys 'success' (bool), 'message'
            (str), 'cleared_size_mb' (float), 'cleared_items'
            (int).

        Examples
        --------
        >>> manager = CacheManager()
        >>> result = manager.clear_census_cache()
        >>> result['success']
        True
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
                "cleared_items": stats_before["item_count"],
            }
        except Exception as e:
            logger.error(f"Failed to clear census cache: {e}")
            return {"success": False, "error": str(e)}

    def clear_all_caches(self) -> dict[str, Any]:
        """
        Clear all cache subsystems.

        Removes all cached data from network, geocoding, census,
        and general caches in a single operation.

        Returns
        -------
        dict
            Nested dictionary with keys for each cache type
            ('network', 'geocoding', 'census', 'general') plus
            'summary'. Summary contains 'success' (bool),
            'total_cleared_mb' (float), 'timestamp' (str).

        Examples
        --------
        >>> manager = CacheManager()
        >>> result = manager.clear_all_caches()
        >>> result['summary']['success']
        True
        >>> result['summary']['total_cleared_mb']
        45.3
        """
        results = {
            "network": self.clear_network_cache(),
            "geocoding": self.clear_geocoding_cache(),
            "census": self.clear_census_cache(),
            "general": self._clear_general_cache(),
        }

        # Calculate totals
        total_cleared_mb = sum(result.get("cleared_size_mb", 0) for result in results.values())

        all_successful = all(result.get("success", False) for result in results.values())

        results["summary"] = {
            "success": all_successful,
            "total_cleared_mb": total_cleared_mb,
            "timestamp": datetime.now().isoformat(),
        }

        return results

    def _clear_general_cache(self) -> dict[str, Any]:
        """
        Clear general cache files in root directory.

        Removes JSON cache files stored in main cache directory.

        Returns
        -------
        dict
            Dictionary with keys 'success' (bool), 'message'
            (str), 'cleared_size_mb' (float), 'cleared_items'
            (int).
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
                "cleared_items": stats_before["item_count"],
            }
        except Exception as e:
            logger.error(f"Failed to clear general cache: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_expired_entries(self) -> dict[str, Any]:
        """
        Remove expired entries from all caches.

        Performs cleanup of stale data based on cache-specific
        expiration policies. Some caches use LRU eviction.

        Returns
        -------
        dict
            Dictionary with status for each cache type
            ('census', 'network', 'geocoding'). Each entry
            contains 'success' (bool) and 'message' (str).

        Notes
        -----
        Not all caches support explicit expiration. Network cache
        uses LRU eviction, and geocoding cache handles cleanup
        on load.
        """
        results = {}

        # Census cache doesn't have built-in expiration for file-based cache
        results["census"] = {
            "success": True,
            "message": "Census file cache doesn't have automatic expiration",
        }

        # Network cache doesn't have built-in expiration
        results["network"] = {
            "success": True,
            "message": "Network cache uses LRU eviction, no expiration cleanup needed",
        }

        # Geocoding cache cleanup handled by AddressCache on load
        results["geocoding"] = {
            "success": True,
            "message": "Geocoding cache cleans expired entries on load",
        }

        return results


# Convenience functions for direct use
def get_cache_statistics() -> dict[str, Any]:
    """
    Get comprehensive statistics for all caches.

    Convenience function that creates a manager and collects all
    cache statistics in one call.

    Returns
    -------
    dict
        Nested dictionary with 'summary' and individual cache
        type statistics. See CacheManager.get_cache_statistics()
        for details.

    Examples
    --------
    >>> stats = get_cache_statistics()
    >>> total_mb = stats['summary']['total_size_mb']
    >>> total_mb >= 0
    True
    """
    manager = CacheManager()
    return manager.get_cache_statistics()


def clear_all_caches() -> dict[str, Any]:
    """
    Clear all SocialMapper cache subsystems.

    Convenience function for removing all cached data in one
    call.

    Returns
    -------
    dict
        Dictionary with results for each cache type plus
        summary. See CacheManager.clear_all_caches() for details.

    Examples
    --------
    >>> result = clear_all_caches()
    >>> result['summary']['success']
    True
    """
    manager = CacheManager()
    return manager.clear_all_caches()


def clear_geocoding_cache() -> dict[str, Any]:
    """
    Clear the geocoding address cache.

    Convenience function for clearing only geocoding cache data.

    Returns
    -------
    dict
        Dictionary with 'success', 'message',
        'cleared_size_mb', 'cleared_items'.

    Examples
    --------
    >>> result = clear_geocoding_cache()
    >>> result['success']
    True
    """
    manager = CacheManager()
    return manager.clear_geocoding_cache()


def clear_census_cache() -> dict[str, Any]:
    """
    Clear the census data cache.

    Convenience function for clearing only census API cache
    data.

    Returns
    -------
    dict
        Dictionary with 'success', 'message',
        'cleared_size_mb', 'cleared_items'.

    Examples
    --------
    >>> result = clear_census_cache()
    >>> result['success']
    True
    """
    manager = CacheManager()
    return manager.clear_census_cache()


def cleanup_expired_cache_entries() -> dict[str, Any]:
    """
    Clean up expired entries from all caches.

    Convenience function for removing stale data from all cache
    subsystems.

    Returns
    -------
    dict
        Dictionary with status for each cache type. See
        CacheManager.cleanup_expired_entries() for details.

    Examples
    --------
    >>> result = cleanup_expired_cache_entries()
    >>> result['network']['success']
    True
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
            str(cache_stats.get("item_count", 0)),
            cache_stats.get("status", "unknown"),
        )

    table.add_section()
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{stats['summary']['total_size_mb']:.2f}[/bold]",
        f"[bold]{stats['summary']['total_items']}[/bold]",
        "",
    )

    console.print(table)

    # Show detailed stats as JSON
    console.print("\n[bold cyan]Detailed Statistics:[/bold cyan]")
    console.print(JSON.from_data(stats))
