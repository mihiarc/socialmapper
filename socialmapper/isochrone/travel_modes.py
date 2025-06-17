#!/usr/bin/env python3
"""Travel mode configurations for isochrone generation.

This module defines travel modes (walk, bike, drive) with their specific
network types and travel speeds for accurate isochrone calculation.
"""

from dataclasses import dataclass
from enum import Enum


class TravelMode(str, Enum):
    """Supported travel modes for isochrone generation."""

    WALK = "walk"
    BIKE = "bike"
    DRIVE = "drive"

    @classmethod
    def from_string(cls, value: str) -> "TravelMode":
        """Create TravelMode from string, case-insensitive."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(
                f"Invalid travel mode: {value}. "
                f"Supported modes: {', '.join([m.value for m in cls])}"
            ) from None


@dataclass
class TravelModeConfig:
    """Configuration for a specific travel mode."""

    mode: TravelMode
    network_type: str  # OSMnx network type
    default_speed_kmh: float  # Default speed in km/h
    max_speed_kmh: float  # Maximum allowed speed
    min_speed_kmh: float  # Minimum allowed speed

    def validate_speed(self, speed: float) -> float:
        """Validate and constrain speed to mode limits."""
        return max(self.min_speed_kmh, min(speed, self.max_speed_kmh))


# Travel mode configurations
TRAVEL_MODE_CONFIGS: dict[TravelMode, TravelModeConfig] = {
    TravelMode.WALK: TravelModeConfig(
        mode=TravelMode.WALK,
        network_type="walk",
        default_speed_kmh=5.0,  # Average walking speed
        max_speed_kmh=7.0,  # Fast walking
        min_speed_kmh=3.0,  # Slow walking
    ),
    TravelMode.BIKE: TravelModeConfig(
        mode=TravelMode.BIKE,
        network_type="bike",
        default_speed_kmh=15.0,  # Average cycling speed
        max_speed_kmh=30.0,  # Fast cycling
        min_speed_kmh=8.0,  # Slow cycling
    ),
    TravelMode.DRIVE: TravelModeConfig(
        mode=TravelMode.DRIVE,
        network_type="drive",
        default_speed_kmh=50.0,  # Default driving speed (city/suburban)
        max_speed_kmh=130.0,  # Highway speed limit
        min_speed_kmh=20.0,  # Congested traffic
    ),
}


def get_travel_mode_config(mode: TravelMode) -> TravelModeConfig:
    """Get configuration for a travel mode."""
    return TRAVEL_MODE_CONFIGS[mode]


def get_network_type(mode: TravelMode) -> str:
    """Get OSMnx network type for a travel mode."""
    return TRAVEL_MODE_CONFIGS[mode].network_type


def get_default_speed(mode: TravelMode) -> float:
    """Get default speed in km/h for a travel mode."""
    return TRAVEL_MODE_CONFIGS[mode].default_speed_kmh


def get_highway_speeds(mode: TravelMode) -> dict[str, float]:
    """Get highway-type-specific speeds for OSMnx routing.

    These speeds are used by OSMnx's add_edge_speeds function to assign
    speeds to edges based on their highway type when maxspeed data is missing.

    Args:
        mode: Travel mode (walk, bike, or drive)

    Returns:
        Dictionary mapping highway types to speeds in km/h
    """
    if mode == TravelMode.WALK:
        # Walking speeds for different path types
        return {
            "footway": 5.0,  # Dedicated pedestrian paths
            "path": 4.5,  # General paths (may be rougher)
            "pedestrian": 5.0,  # Pedestrian areas
            "steps": 1.5,  # Stairs are very slow
            "sidewalk": 5.0,  # Sidewalks
            "residential": 4.8,  # Residential streets (may lack sidewalks)
            "living_street": 4.5,  # Shared spaces, need caution
            "service": 4.5,  # Service roads
            "primary": 4.5,  # Busy roads may slow walking
            "secondary": 4.5,  # Busy roads
            "tertiary": 4.8,  # Less busy roads
            "trunk": 4.0,  # Very busy roads, often no sidewalk
            "motorway": 3.0,  # Highways (rarely walkable)
        }
    elif mode == TravelMode.BIKE:
        # Cycling speeds for different road types
        return {
            "cycleway": 18.0,  # Dedicated bike lanes
            "path": 12.0,  # Shared paths
            "footway": 8.0,  # Shared with pedestrians (slow)
            "pedestrian": 8.0,  # Pedestrian areas (slow cycling)
            "residential": 15.0,  # Residential streets
            "living_street": 10.0,  # Shared spaces
            "service": 12.0,  # Service roads
            "tertiary": 16.0,  # Light traffic
            "secondary": 18.0,  # Moderate traffic
            "primary": 20.0,  # Good roads, higher speeds
            "trunk": 15.0,  # May be dangerous/restricted
            "motorway": 10.0,  # Highways (if allowed at all)
        }
    else:  # DRIVE
        # Driving speeds based on typical speed limits
        # These align with common speed limits in many countries
        return {
            "motorway": 110.0,  # Highways/freeways
            "motorway_link": 70.0,  # Highway ramps
            "trunk": 90.0,  # Major roads
            "trunk_link": 50.0,  # Major road ramps
            "primary": 65.0,  # Primary roads
            "primary_link": 40.0,  # Primary road connectors
            "secondary": 55.0,  # Secondary roads
            "secondary_link": 35.0,  # Secondary road connectors
            "tertiary": 45.0,  # Tertiary roads
            "tertiary_link": 30.0,  # Tertiary road connectors
            "residential": 30.0,  # Residential streets
            "living_street": 20.0,  # Shared residential areas
            "service": 25.0,  # Service roads
            "unclassified": 40.0,  # Unclassified roads
            "road": 40.0,  # Unknown road types
        }
