"""Entity extraction for natural language queries.

This module defines entity types and extraction logic for identifying
key components in natural language spatial analysis queries.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto


class EntityType(Enum):
    """Types of entities that can be extracted from queries."""

    LOCATION = auto()
    POI_TYPE = auto()
    TIME_CONSTRAINT = auto()
    DISTANCE_CONSTRAINT = auto()
    DEMOGRAPHIC = auto()
    TRAVEL_MODE = auto()
    ANALYSIS_TYPE = auto()


@dataclass
class ExtractedEntity:
    """Base class for extracted entities."""

    entity_type: EntityType
    text: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0


@dataclass
class LocationEntity(ExtractedEntity):
    """Location entity with geographic information."""

    location_name: str = ""
    location_type: str = "city"  # city, state, address, coordinates
    coordinates: tuple[float, float] | None = None

    def __post_init__(self):
        self.entity_type = EntityType.LOCATION


@dataclass
class POIEntity(ExtractedEntity):
    """Point of Interest entity."""

    poi_category: str = ""
    osm_type: str | None = None
    osm_name: str | None = None

    def __post_init__(self):
        self.entity_type = EntityType.POI_TYPE


@dataclass
class TimeConstraintEntity(ExtractedEntity):
    """Time-based constraint entity."""

    minutes: int = 0
    constraint_type: str = "within"  # within, under, maximum, etc.

    def __post_init__(self):
        self.entity_type = EntityType.TIME_CONSTRAINT


@dataclass
class DistanceConstraintEntity(ExtractedEntity):
    """Distance-based constraint entity."""

    distance: float = 0.0
    unit: str = "km"  # miles, km, meters
    constraint_type: str = "within"

    def __post_init__(self):
        self.entity_type = EntityType.DISTANCE_CONSTRAINT


@dataclass
class DemographicEntity(ExtractedEntity):
    """Demographic constraint entity."""

    demographic_type: str = ""
    value_type: str = "categorical"  # categorical, numeric, range
    value: str | float | tuple[float, float] = None

    def __post_init__(self):
        self.entity_type = EntityType.DEMOGRAPHIC


@dataclass
class TravelModeEntity(ExtractedEntity):
    """Travel mode entity."""

    mode: str = "drive"  # walk, drive, bike, transit

    def __post_init__(self):
        self.entity_type = EntityType.TRAVEL_MODE


class EntityExtractor:
    """Extracts entities from natural language queries."""

    def __init__(self):
        self._setup_patterns()

    def _setup_patterns(self):
        """Setup regex patterns for entity extraction."""
        # POI patterns - map common terms to OSM categories
        self.poi_patterns = {
            r'\b(?:hospitals?|medical centers?|clinics?)\b': {
                'category': 'healthcare', 'osm_type': 'amenity', 'osm_name': 'hospital'
            },
            r'\b(?:libraries?|public libraries?)\b': {
                'category': 'education', 'osm_type': 'amenity', 'osm_name': 'library'
            },
            r'\b(?:schools?|elementary schools?|high schools?)\b': {
                'category': 'education', 'osm_type': 'amenity', 'osm_name': 'school'
            },
            r'\b(?:parks?|public parks?|green spaces?)\b': {
                'category': 'recreation', 'osm_type': 'leisure', 'osm_name': 'park'
            },
            r'\b(?:grocery stores?|supermarkets?|food stores?)\b': {
                'category': 'food_and_drink', 'osm_type': 'shop', 'osm_name': 'supermarket'
            },
            r'\b(?:pharmacies?|drug stores?)\b': {
                'category': 'healthcare', 'osm_type': 'amenity', 'osm_name': 'pharmacy'
            },
            r'\b(?:restaurants?|cafes?|food)\b': {
                'category': 'food_and_drink', 'osm_type': 'amenity', 'osm_name': 'restaurant'
            },
            r'\b(?:transit stops?|bus stops?|subway stations?)\b': {
                'category': 'transportation', 'osm_type': 'highway', 'osm_name': 'bus_stop'
            },
            r'\b(?:banks?|atms?)\b': {
                'category': 'finance', 'osm_type': 'amenity', 'osm_name': 'bank'
            },
            r'\b(?:gas stations?|fuel stations?)\b': {
                'category': 'transportation', 'osm_type': 'amenity', 'osm_name': 'fuel'
            },
        }

        # Time constraint patterns
        self.time_patterns = [
            r'\b(?:within|under|less than|maximum of|max)\s+(\d+)\s+minutes?\b',
            r'\b(\d+)\s+minutes?\s+(?:walk|drive|bike|away)\b',
            r'\b(\d+)[-\s]?min(?:ute)?s?\b',
        ]

        # Distance constraint patterns
        self.distance_patterns = [
            r'\b(?:within|under|less than)\s+(\d+(?:\.\d+)?)\s+(miles?|km|kilometers?|meters?)\b',
            r'\b(\d+(?:\.\d+)?)\s+(miles?|km|kilometers?|meters?)\s+(?:away|radius)\b',
        ]

        # Demographic patterns
        self.demographic_patterns = {
            r'\b(?:low-income|low income|poor)\b': {
                'type': 'income', 'value': 'low', 'census_var': 'median_household_income'
            },
            r'\b(?:high-income|high income|wealthy|affluent)\b': {
                'type': 'income', 'value': 'high', 'census_var': 'median_household_income'
            },
            r'\b(?:elderly|seniors?|older adults?)\b': {
                'type': 'age', 'value': 'elderly', 'census_var': 'median_age'
            },
            r'\b(?:young families?|families with children)\b': {
                'type': 'family', 'value': 'young_families', 'census_var': 'total_population'
            },
            r'\b(?:minority|diverse|non-white)\s+(?:areas?|neighborhoods?|communities?)\b': {
                'type': 'race', 'value': 'minority', 'census_var': 'white_population'
            },
            r'\b(?:rural|suburban|urban)\s+(?:areas?|communities?)\b': {
                'type': 'density', 'value': '$1', 'census_var': 'total_population'
            },
        }

        # Travel mode patterns
        self.travel_mode_patterns = {
            r'\b(?:walk|walking|on foot)\b': 'walk',
            r'\b(?:drive|driving|by car|car)\b': 'drive',
            r'\b(?:bike|biking|bicycle|cycling)\b': 'bike',
            r'\b(?:transit|public transit|bus|train)\b': 'transit',
        }

        # Location patterns - US cities and states
        self.location_patterns = [
            # City, State format
            r'\b([A-Z][a-zA-Z\s]+),\s*([A-Z]{2}|[A-Z][a-zA-Z\s]+)\b',
            # Just city names (common ones)
            r'\b(Boston|New York|San Francisco|Los Angeles|Chicago|Seattle|Denver|Miami|Atlanta)\b',
            # Coordinate patterns
            r'\b(-?\d+\.\d+),\s*(-?\d+\.\d+)\b',
        ]

    def extract_entities(self, query: str) -> list[ExtractedEntity]:
        """Extract all entities from a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            List of extracted entities
        """
        entities = []
        query_lower = query.lower()

        # Extract POI entities
        entities.extend(self._extract_poi_entities(query, query_lower))

        # Extract time constraints
        entities.extend(self._extract_time_constraints(query, query_lower))

        # Extract distance constraints
        entities.extend(self._extract_distance_constraints(query, query_lower))

        # Extract demographic entities
        entities.extend(self._extract_demographic_entities(query, query_lower))

        # Extract travel mode entities
        entities.extend(self._extract_travel_mode_entities(query, query_lower))

        # Extract location entities
        entities.extend(self._extract_location_entities(query))

        return entities

    def _extract_poi_entities(self, query: str, query_lower: str) -> list[POIEntity]:
        """Extract POI entities from query."""
        entities = []

        for pattern, poi_info in self.poi_patterns.items():
            for match in re.finditer(pattern, query_lower):
                entity = POIEntity(
                    entity_type=EntityType.POI_TYPE,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    poi_category=poi_info['category'],
                    osm_type=poi_info['osm_type'],
                    osm_name=poi_info['osm_name']
                )
                entities.append(entity)

        return entities

    def _extract_time_constraints(self, query: str, query_lower: str) -> list[TimeConstraintEntity]:
        """Extract time constraint entities from query."""
        entities = []

        for pattern in self.time_patterns:
            for match in re.finditer(pattern, query_lower):
                minutes = int(match.group(1))
                constraint_type = "within"

                # Determine constraint type from context
                if "under" in match.group(0) or "less than" in match.group(0):
                    constraint_type = "under"
                elif "maximum" in match.group(0) or "max" in match.group(0):
                    constraint_type = "maximum"

                entity = TimeConstraintEntity(
                    entity_type=EntityType.TIME_CONSTRAINT,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    minutes=minutes,
                    constraint_type=constraint_type
                )
                entities.append(entity)

        return entities

    def _extract_distance_constraints(self, query: str, query_lower: str) -> list[DistanceConstraintEntity]:
        """Extract distance constraint entities from query."""
        entities = []

        for pattern in self.distance_patterns:
            for match in re.finditer(pattern, query_lower):
                distance = float(match.group(1))
                unit = match.group(2).lower()

                # Normalize units
                if unit.startswith('km') or unit.startswith('kilometer'):
                    unit = 'km'
                elif unit.startswith('mile'):
                    unit = 'miles'
                elif unit.startswith('meter'):
                    unit = 'meters'

                entity = DistanceConstraintEntity(
                    entity_type=EntityType.DISTANCE_CONSTRAINT,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    distance=distance,
                    unit=unit
                )
                entities.append(entity)

        return entities

    def _extract_demographic_entities(self, query: str, query_lower: str) -> list[DemographicEntity]:
        """Extract demographic entities from query."""
        entities = []

        for pattern, demo_info in self.demographic_patterns.items():
            for match in re.finditer(pattern, query_lower):
                entity = DemographicEntity(
                    entity_type=EntityType.DEMOGRAPHIC,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    demographic_type=demo_info['type'],
                    value=demo_info['value']
                )
                entities.append(entity)

        return entities

    def _extract_travel_mode_entities(self, query: str, query_lower: str) -> list[TravelModeEntity]:
        """Extract travel mode entities from query."""
        entities = []

        for pattern, mode in self.travel_mode_patterns.items():
            for match in re.finditer(pattern, query_lower):
                entity = TravelModeEntity(
                    entity_type=EntityType.TRAVEL_MODE,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    mode=mode
                )
                entities.append(entity)

        return entities

    def _extract_location_entities(self, query: str) -> list[LocationEntity]:
        """Extract location entities from query."""
        entities = []

        for pattern in self.location_patterns:
            for match in re.finditer(pattern, query):
                if len(match.groups()) == 2:
                    # City, State format
                    city, state = match.groups()
                    location_name = f"{city.strip()}, {state.strip()}"
                    location_type = "city_state"
                    coordinates = None

                    # Check if it's coordinates
                    try:
                        lat, lon = float(match.group(1)), float(match.group(2))
                        location_name = f"{lat}, {lon}"
                        location_type = "coordinates"
                        coordinates = (lat, lon)
                    except (ValueError, IndexError):
                        pass

                elif len(match.groups()) == 1:
                    # Single city name
                    location_name = match.group(1).strip()
                    location_type = "city"
                    coordinates = None
                else:
                    # Full match
                    location_name = match.group(0).strip()
                    location_type = "unknown"
                    coordinates = None

                entity = LocationEntity(
                    entity_type=EntityType.LOCATION,
                    text=match.group(0),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    location_name=location_name,
                    location_type=location_type,
                    coordinates=coordinates
                )
                entities.append(entity)

        return entities
