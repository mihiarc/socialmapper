"""Central I/O manager for tracking and organizing all file operations."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OutputFile:
    """Represents a generated output file."""

    path: Path
    file_type: str  # 'csv', 'map', 'isochrone', 'geojson', etc.
    category: str  # 'census_data', 'poi_data', 'maps', 'isochrones', etc.
    travel_mode: str | None = None
    travel_time: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        """Check if the file still exists."""
        return self.path.exists()

    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        if self.exists:
            return self.path.stat().st_size / (1024 * 1024)
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "file_type": self.file_type,
            "category": self.category,
            "travel_mode": self.travel_mode,
            "travel_time": self.travel_time,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "exists": self.exists,
            "size_mb": self.size_mb,
        }


class OutputTracker:
    """Tracks all generated output files for an analysis."""

    def __init__(self):
        self.files: list[OutputFile] = []
        self._categories: dict[str, list[OutputFile]] = {}

    def add_file(
        self,
        path: Path | str,
        file_type: str,
        category: str,
        travel_mode: str | None = None,
        travel_time: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OutputFile:
        """Add a file to the tracker."""
        output_file = OutputFile(
            path=Path(path),
            file_type=file_type,
            category=category,
            travel_mode=travel_mode,
            travel_time=travel_time,
            metadata=metadata or {},
        )

        self.files.append(output_file)

        # Update category index
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(output_file)

        logger.debug(f"Tracked output file: {output_file.path} ({category}/{file_type})")
        return output_file

    def get_by_category(self, category: str) -> list[OutputFile]:
        """Get all files in a category."""
        return self._categories.get(category, [])

    def get_by_type(self, file_type: str) -> list[OutputFile]:
        """Get all files of a specific type."""
        return [f for f in self.files if f.file_type == file_type]

    def get_by_travel_mode(self, travel_mode: str) -> list[OutputFile]:
        """Get all files for a specific travel mode."""
        return [f for f in self.files if f.travel_mode == travel_mode]

    def get_maps(self) -> list[OutputFile]:
        """Get all map files."""
        return self.get_by_category("maps")

    def get_existing_files(self) -> list[OutputFile]:
        """Get only files that still exist on disk."""
        return [f for f in self.files if f.exists]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "files": [f.to_dict() for f in self.files],
            "categories": list(self._categories.keys()),
            "total_files": len(self.files),
            "total_size_mb": sum(f.size_mb for f in self.files if f.exists),
        }

    def save_manifest(self, output_dir: Path | str) -> Path:
        """Save a manifest of all tracked files."""
        output_dir = Path(output_dir)
        manifest_path = output_dir / "output_manifest.json"

        with open(manifest_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        logger.info(f"Saved output manifest to {manifest_path}")
        return manifest_path

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of tracked files."""
        return {
            "total_files": len(self.files),
            "existing_files": len(self.get_existing_files()),
            "categories": {cat: len(files) for cat, files in self._categories.items()},
            "file_types": {
                file_type: len(self.get_by_type(file_type))
                for file_type in {f.file_type for f in self.files}
            },
            "travel_modes": {
                mode: len(self.get_by_travel_mode(mode))
                for mode in {f.travel_mode for f in self.files if f.travel_mode}
            },
            "total_size_mb": sum(f.size_mb for f in self.files if f.exists),
        }


class IOManager:
    """Central manager for all I/O operations."""

    def __init__(self, base_output_dir: Path | str = "output"):
        self.base_output_dir = Path(base_output_dir)
        self.output_tracker = OutputTracker()
        self._directories: dict[str, Path] = {}

        # Standard directory structure - only directories actually used
        self.standard_dirs = {
            "base": self.base_output_dir,
            "maps": self.base_output_dir / "maps",
            "isochrones": self.base_output_dir / "isochrones",
            "census_data": self.base_output_dir / "census_data",
        }

    def setup_directories(self, create_all: bool = True) -> dict[str, Path]:
        """Set up output directory structure."""
        if create_all:
            for name, path in self.standard_dirs.items():
                path.mkdir(parents=True, exist_ok=True)
                self._directories[name] = path
                logger.debug(f"Created directory: {path}")
        else:
            # Just create base directory
            self.base_output_dir.mkdir(parents=True, exist_ok=True)
            self._directories["base"] = self.base_output_dir

        return self._directories

    def get_directory(self, category: str) -> Path:
        """Get a directory path, creating it if needed."""
        if category not in self._directories:
            if category in self.standard_dirs:
                path = self.standard_dirs[category]
            else:
                path = self.base_output_dir / category

            path.mkdir(parents=True, exist_ok=True)
            self._directories[category] = path

        return self._directories[category]

    def generate_filename(
        self,
        base_name: str,
        file_type: str,
        travel_mode: str | None = None,
        travel_time: int | None = None,
        suffix: str | None = None,
    ) -> str:
        """Generate a consistent filename."""
        parts = [base_name]

        if travel_time is not None:
            parts.append(f"{travel_time}min")

        if travel_mode:
            parts.append(travel_mode)

        if suffix:
            parts.append(suffix)

        # Add file type description
        if file_type == "csv":
            parts.append("data")
        elif file_type == "map":
            parts.append("map")
        elif file_type == "isochrone":
            parts.append("isochrones")

        filename = "_".join(parts)

        # Add extension
        extensions = {
            "csv": ".csv",
            "map": ".png",
            "isochrone": ".geoparquet",
            "geoparquet": ".geoparquet",
            "geojson": ".geojson",
            "parquet": ".parquet",
            "json": ".json",
            "html": ".html",
        }

        return filename + extensions.get(file_type, "")

    def save_file(
        self,
        content: Any,
        category: str,
        file_type: str,
        base_name: str,
        travel_mode: str | None = None,
        travel_time: int | None = None,
        suffix: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OutputFile:
        """Save a file and track it."""
        from .writers import WRITERS

        # Get appropriate writer
        writer = WRITERS.get(file_type)
        if not writer:
            raise ValueError(f"No writer available for file type: {file_type}")

        # Generate filename and path
        filename = self.generate_filename(base_name, file_type, travel_mode, travel_time, suffix)
        directory = self.get_directory(category)
        filepath = directory / filename

        # Write the file
        writer(content, filepath, metadata)

        # Track the file
        return self.output_tracker.add_file(
            path=filepath,
            file_type=file_type,
            category=category,
            travel_mode=travel_mode,
            travel_time=travel_time,
            metadata=metadata,
        )

    def get_output_summary(self) -> dict[str, Any]:
        """Get a summary of all outputs."""
        return {
            "directories": {k: str(v) for k, v in self._directories.items()},
            "files": self.output_tracker.get_summary(),
        }

    def get_files_for_ui(self) -> dict[str, Any]:
        """Get file information formatted for UI display."""
        files_by_category = {}

        for category, files in self.output_tracker._categories.items():
            files_by_category[category] = [
                {
                    "filename": f.path.name,
                    "path": str(f.path),
                    "type": f.file_type,
                    "travel_mode": f.travel_mode,
                    "size_mb": f.size_mb,
                    "exists": f.exists,
                }
                for f in files
            ]

        return files_by_category

    def cleanup_old_files(self, keep_latest_n: int = 10) -> int:
        """Remove old files, keeping the latest N."""
        # Group files by type and category
        file_groups = {}
        for f in self.output_tracker.files:
            key = (f.category, f.file_type)
            if key not in file_groups:
                file_groups[key] = []
            file_groups[key].append(f)

        removed_count = 0

        # Sort each group by creation time and remove old files
        for _key, files in file_groups.items():
            sorted_files = sorted(files, key=lambda f: f.created_at, reverse=True)

            for f in sorted_files[keep_latest_n:]:
                if f.exists:
                    f.path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old file: {f.path}")

        return removed_count
