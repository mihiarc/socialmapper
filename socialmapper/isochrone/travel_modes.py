#!/usr/bin/env python3
"""
Travel mode configurations for isochrone generation.

This module defines travel modes (walk, bike, drive) with their specific
network types and travel speeds for accurate isochrone calculation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


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
            )


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
TRAVEL_MODE_CONFIGS: Dict[TravelMode, TravelModeConfig] = {
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


def adjust_speed_for_road_type(
    mode: TravelMode, 
    highway_type: Optional[str] = None,
    base_speed: Optional[float] = None
) -> float:
    """
    Adjust speed based on travel mode and road type.
    
    Args:
        mode: Travel mode
        highway_type: OSM highway type (e.g., 'residential', 'primary', 'footway')
        base_speed: Base speed to adjust (uses mode default if None)
        
    Returns:
        Adjusted speed in km/h
    """
    config = TRAVEL_MODE_CONFIGS[mode]
    speed = base_speed or config.default_speed_kmh
    
    if highway_type is None:
        return speed
    
    # Speed adjustments based on road type
    if mode == TravelMode.WALK:
        # Walking speeds vary less by road type
        adjustments = {
            "footway": 1.0,
            "path": 0.9,
            "pedestrian": 1.0,
            "steps": 0.3,  # Stairs are slow
            "residential": 0.95,
            "primary": 0.9,  # Busy roads may slow walking
            "trunk": 0.8,  # Very busy roads
        }
    elif mode == TravelMode.BIKE:
        # Cycling speeds vary significantly by road type
        adjustments = {
            "cycleway": 1.1,  # Dedicated bike lanes
            "path": 0.8,
            "footway": 0.6,  # Shared with pedestrians
            "residential": 1.0,
            "tertiary": 1.05,
            "secondary": 1.1,
            "primary": 1.15,
            "trunk": 0.9,  # May be dangerous/restricted
        }
    else:  # DRIVE
        # Driving speeds based on typical speed limits
        adjustments = {
            "motorway": 2.2,  # Highway speeds
            "trunk": 1.8,
            "primary": 1.3,
            "secondary": 1.1,
            "tertiary": 0.9,
            "residential": 0.6,
            "living_street": 0.4,
            "service": 0.5,
        }
    
    adjustment = adjustments.get(highway_type, 1.0)
    adjusted_speed = speed * adjustment
    
    # Ensure speed stays within mode limits
    return config.validate_speed(adjusted_speed)