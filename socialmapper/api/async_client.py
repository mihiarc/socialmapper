"""
Async client for SocialMapper with modern context manager support.

Provides asynchronous operations for network I/O with proper resource management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from ..pipeline import PipelineConfig
from .builder import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class POIResult:
    """Result from POI extraction."""

    id: str
    name: str
    type: str
    latitude: float
    longitude: float
    tags: Dict[str, str]


@dataclass
class IsochroneResult:
    """Result from isochrone generation."""

    poi_id: str
    travel_time: int
    geometry: Any  # GeoDataFrame geometry
    area_sq_km: float


class AsyncSocialMapper:
    """
    Asynchronous client for SocialMapper operations.

    Example:
        ```python
        async with AsyncSocialMapper(config) as mapper:
            # Stream POIs as they're found
            async for poi in mapper.stream_pois():
                print(f"Found: {poi.name}")

            # Generate isochrones with progress
            async for progress in mapper.generate_isochrones_with_progress():
                print(f"Progress: {progress.completed}/{progress.total}")
        ```
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration from builder."""
        self.config = PipelineConfig(**config)
        self.session: Optional[aiohttp.ClientSession] = None
        self._results: Dict[str, Any] = {}

    async def __aenter__(self):
        """Set up async resources."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async resources."""
        if self.session:
            await self.session.close()

    async def stream_pois(self) -> AsyncIterator[POIResult]:
        """
        Stream POIs as they're discovered.

        Yields:
            POIResult objects as they're found
        """
        # Simulate async POI extraction
        await asyncio.sleep(0.1)  # Network delay

        # In real implementation, this would query OSM API asynchronously
        mock_pois = [
            POIResult(
                id=f"poi_{i}",
                name=f"Library {i}",
                type="amenity",
                latitude=37.7749 + i * 0.01,
                longitude=-122.4194 + i * 0.01,
                tags={"amenity": "library"},
            )
            for i in range(3)
        ]

        for poi in mock_pois:
            await asyncio.sleep(0.05)  # Simulate processing time
            yield poi

    async def generate_isochrones_with_progress(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate isochrones with progress updates.

        Yields:
            Progress updates with completed/total counts
        """
        total_pois = 3  # Would come from actual POI count

        for i in range(total_pois):
            await asyncio.sleep(0.2)  # Simulate isochrone calculation
            yield {
                "completed": i + 1,
                "total": total_pois,
                "current_poi": f"Library {i}",
                "percent": (i + 1) / total_pois * 100,
            }

    async def run_analysis(self) -> AnalysisResult:
        """
        Run the complete analysis asynchronously.

        Returns:
            AnalysisResult with summary information
        """
        # Track results
        poi_count = 0
        isochrone_count = 0

        # Extract POIs
        logger.info("Starting POI extraction...")
        async for poi in self.stream_pois():
            poi_count += 1
            logger.debug(f"Extracted POI: {poi.name}")

        # Generate isochrones
        logger.info("Generating isochrones...")
        async for progress in self.generate_isochrones_with_progress():
            if progress["completed"] == progress["total"]:
                isochrone_count = progress["total"]

        # In real implementation, would integrate census data here
        await asyncio.sleep(0.3)  # Simulate census integration

        return AnalysisResult(
            poi_count=poi_count,
            isochrone_count=isochrone_count,
            census_units_analyzed=150,  # Mock value
            files_generated={
                "census_data": self.config.output_dir / "census_data.csv",
                "map": self.config.output_dir / "map.html",
            },
            metadata={
                "travel_time": self.config.travel_time,
                "geographic_level": self.config.geographic_level,
            },
        )

    @asynccontextmanager
    async def batch_operations(self, size: int = 10):
        """
        Context manager for batched operations.

        Example:
            ```python
            async with mapper.batch_operations(size=20) as batch:
                await batch.add_poi(poi1)
                await batch.add_poi(poi2)
                # Automatically processes when size reached or context exits
            ```
        """
        batch = []

        class BatchProcessor:
            async def add_poi(self, poi: POIResult):
                batch.append(poi)
                if len(batch) >= size:
                    await self._process_batch(batch)
                    batch.clear()

            async def _process_batch(self, items: List[POIResult]):
                logger.info(f"Processing batch of {len(items)} POIs")
                await asyncio.sleep(0.1)  # Simulate processing

        processor = BatchProcessor()
        try:
            yield processor
        finally:
            # Process remaining items
            if batch:
                await processor._process_batch(batch)


async def run_async_analysis(config: Dict[str, Any]) -> AnalysisResult:
    """
    Convenience function to run analysis asynchronously.

    Args:
        config: Configuration from SocialMapperBuilder

    Returns:
        AnalysisResult with analysis summary

    Example:
        ```python
        config = (SocialMapperBuilder()
            .with_location("San Francisco", "CA")
            .with_osm_pois("amenity", "library")
            .build()
        )

        result = await run_async_analysis(config)
        print(f"Analyzed {result.poi_count} POIs")
        ```
    """
    async with AsyncSocialMapper(config) as mapper:
        return await mapper.run_analysis()
