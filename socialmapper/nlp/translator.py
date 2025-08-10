"""Query translation from natural language to analysis configuration.

This module converts parsed entities and classified intents into
structured SocialMapper analysis configurations.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import logging

from ..api.builder import SocialMapperBuilder, GeographicLevel
from ..isochrone import TravelMode
from .entities import (
    ExtractedEntity, LocationEntity, POIEntity, TimeConstraintEntity,
    DistanceConstraintEntity, DemographicEntity, TravelModeEntity, EntityType
)
from .intents import QueryIntent, IntentClassification


logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result of translating NL query to analysis configuration."""
    
    config: Dict[str, Any]
    warnings: List[str]
    suggestions: List[str]
    confidence: float
    reasoning: str


class QueryTranslator:
    """Translates entities and intents into analysis configurations."""
    
    def __init__(self):
        self._setup_mappings()
    
    def _setup_mappings(self):
        """Setup mappings for translation."""
        
        # Travel mode mapping
        self.travel_mode_mapping = {
            'walk': TravelMode.WALK,
            'drive': TravelMode.DRIVE, 
            'bike': TravelMode.BIKE,
            'transit': TravelMode.DRIVE  # Fallback to drive for now
        }
        
        # Default census variables by demographic type
        self.demographic_census_vars = {
            'income': ['median_household_income', 'percent_poverty'],
            'age': ['median_age', 'total_population'],
            'race': ['white_population', 'black_population', 'hispanic_population'],
            'education': ['education_bachelors_plus'],
            'family': ['total_population'],
            'density': ['total_population']
        }
        
        # Default travel times by mode
        self.default_travel_times = {
            TravelMode.WALK: 15,
            TravelMode.BIKE: 20,
            TravelMode.DRIVE: 30
        }
    
    def translate(
        self, 
        entities: List[ExtractedEntity], 
        classification: IntentClassification
    ) -> TranslationResult:
        """Translate entities and intent to analysis configuration.
        
        Args:
            entities: Extracted entities from query
            classification: Classified intent
            
        Returns:
            TranslationResult with configuration and metadata
        """
        warnings = []
        suggestions = []
        
        # Initialize builder
        builder = SocialMapperBuilder()
        
        # Process entities by type
        location_entities = [e for e in entities if isinstance(e, LocationEntity)]
        poi_entities = [e for e in entities if isinstance(e, POIEntity)]
        time_entities = [e for e in entities if isinstance(e, TimeConstraintEntity)]
        distance_entities = [e for e in entities if isinstance(e, DistanceConstraintEntity)]
        demographic_entities = [e for e in entities if isinstance(e, DemographicEntity)]
        travel_mode_entities = [e for e in entities if isinstance(e, TravelModeEntity)]
        
        # Configure based on intent
        if classification.primary_intent == QueryIntent.POI_DISCOVERY:
            config = self._configure_poi_discovery(
                builder, location_entities, poi_entities, time_entities,
                distance_entities, travel_mode_entities, warnings
            )
        else:
            config = self._configure_standard_analysis(
                builder, location_entities, poi_entities, time_entities,
                distance_entities, demographic_entities, travel_mode_entities,
                classification, warnings
            )
        
        # Add suggestions based on missing or unclear entities
        suggestions.extend(self._generate_suggestions(entities, classification))
        
        return TranslationResult(
            config=config,
            warnings=warnings,
            suggestions=suggestions,
            confidence=classification.confidence,
            reasoning=classification.reasoning
        )
    
    def _configure_poi_discovery(
        self,
        builder: SocialMapperBuilder,
        location_entities: List[LocationEntity],
        poi_entities: List[POIEntity],
        time_entities: List[TimeConstraintEntity],
        distance_entities: List[DistanceConstraintEntity],
        travel_mode_entities: List[TravelModeEntity],
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Configure POI discovery analysis."""
        
        # Location is required
        if not location_entities:
            warnings.append("No location specified - using default location")
            location = "Boston, MA"  # Default fallback
        else:
            location_entity = location_entities[0]
            if location_entity.coordinates:
                location = location_entity.coordinates
            else:
                location = location_entity.location_name
        
        # Travel time - use specified or default
        travel_time = 15  # Default
        if time_entities:
            travel_time = time_entities[0].minutes
        elif distance_entities:
            # Convert distance to approximate time
            dist_entity = distance_entities[0]
            if dist_entity.unit == 'miles':
                # Rough conversion: 1 mile = 3 minutes walking, 1 minute driving
                travel_time = int(dist_entity.distance * 3)  # Assume walking
            warnings.append(f"Converted distance to approximate travel time: {travel_time} minutes")
        
        # Travel mode
        travel_mode = TravelMode.DRIVE  # Default
        if travel_mode_entities:
            mode_str = travel_mode_entities[0].mode
            travel_mode = self.travel_mode_mapping.get(mode_str, TravelMode.DRIVE)
        
        # POI categories - if specified, use them; otherwise discover all
        poi_categories = None
        if poi_entities:
            poi_categories = [poi.poi_category for poi in poi_entities]
            poi_categories = list(set(poi_categories))  # Remove duplicates
        
        # Configure POI discovery
        builder.with_nearby_poi_discovery(
            location=location,
            travel_time=travel_time,
            travel_mode=travel_mode,
            poi_categories=poi_categories
        )
        
        # Enable exports
        builder.with_export_options(csv=True, geojson=True, maps=True)
        
        return builder.build()
    
    def _configure_standard_analysis(
        self,
        builder: SocialMapperBuilder,
        location_entities: List[LocationEntity],
        poi_entities: List[POIEntity], 
        time_entities: List[TimeConstraintEntity],
        distance_entities: List[DistanceConstraintEntity],
        demographic_entities: List[DemographicEntity],
        travel_mode_entities: List[TravelModeEntity],
        classification: IntentClassification,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Configure standard accessibility analysis."""
        
        # Location - required for standard analysis
        if not location_entities:
            warnings.append("No location specified - analysis may fail")
        else:
            location_entity = location_entities[0]
            if location_entity.location_type == "city_state":
                # Parse "City, State" format
                parts = location_entity.location_name.split(", ")
                if len(parts) == 2:
                    builder.with_location(parts[0].strip(), parts[1].strip())
                else:
                    warnings.append(f"Could not parse location: {location_entity.location_name}")
            elif location_entity.coordinates:
                # Use coordinates directly 
                lat, lon = location_entity.coordinates
                builder.with_coordinates(lat, lon)
            else:
                # Try to parse as city name
                builder.with_location(location_entity.location_name, "")
                warnings.append("State not specified - geocoding may be ambiguous")
        
        # POI configuration - required for standard analysis
        if not poi_entities:
            warnings.append("No POI type specified - using default 'library'")
            builder.with_osm_pois("amenity", "library")
        else:
            poi_entity = poi_entities[0]  # Use first POI type
            if poi_entity.osm_type and poi_entity.osm_name:
                builder.with_osm_pois(poi_entity.osm_type, poi_entity.osm_name)
            else:
                # Try to map category to OSM tags
                osm_mapping = self._get_osm_mapping(poi_entity.poi_category)
                if osm_mapping:
                    builder.with_osm_pois(osm_mapping['type'], osm_mapping['name'])
                else:
                    warnings.append(f"Could not map POI category: {poi_entity.poi_category}")
        
        # Travel time
        travel_time = None
        if time_entities:
            travel_time = time_entities[0].minutes
        elif distance_entities:
            # Convert distance to time based on travel mode
            dist_entity = distance_entities[0]
            travel_mode = TravelMode.DRIVE
            if travel_mode_entities:
                mode_str = travel_mode_entities[0].mode
                travel_mode = self.travel_mode_mapping.get(mode_str, TravelMode.DRIVE)
            
            # Rough speed estimates: walk=3mph, bike=12mph, drive=30mph
            speeds = {TravelMode.WALK: 3, TravelMode.BIKE: 12, TravelMode.DRIVE: 30}
            speed = speeds[travel_mode]
            
            if dist_entity.unit == 'miles':
                travel_time = int((dist_entity.distance / speed) * 60)
            elif dist_entity.unit == 'km':
                travel_time = int((dist_entity.distance * 0.621371 / speed) * 60)
            
            warnings.append(f"Converted {dist_entity.distance} {dist_entity.unit} to {travel_time} minutes")
        
        if travel_time:
            builder.with_travel_time(travel_time)
        else:
            # Use default based on travel mode
            travel_mode = TravelMode.DRIVE
            if travel_mode_entities:
                mode_str = travel_mode_entities[0].mode
                travel_mode = self.travel_mode_mapping.get(mode_str, TravelMode.DRIVE)
            
            default_time = self.default_travel_times[travel_mode]
            builder.with_travel_time(default_time)
            warnings.append(f"Using default travel time: {default_time} minutes")
        
        # Travel mode
        if travel_mode_entities:
            mode_str = travel_mode_entities[0].mode
            travel_mode = self.travel_mode_mapping.get(mode_str, TravelMode.DRIVE)
            builder.with_travel_mode(travel_mode)
        
        # Census variables based on demographics mentioned
        census_vars = set()
        if demographic_entities:
            for demo_entity in demographic_entities:
                demo_type = demo_entity.demographic_type
                if demo_type in self.demographic_census_vars:
                    census_vars.update(self.demographic_census_vars[demo_type])
        
        # Add default variables for certain intents
        if classification.primary_intent in [QueryIntent.DEMOGRAPHIC_ANALYSIS, QueryIntent.EQUITY_ANALYSIS]:
            census_vars.update(['total_population', 'median_household_income'])
        
        if census_vars:
            builder.with_census_variables(*list(census_vars))
        
        # Geographic level based on intent
        if classification.primary_intent == QueryIntent.EQUITY_ANALYSIS:
            builder.with_geographic_level(GeographicLevel.BLOCK_GROUP)
        
        # Enable appropriate exports
        builder.with_exports(csv=True, isochrones=True)
        
        # Enable maps for certain intents
        if classification.primary_intent in [
            QueryIntent.DEMOGRAPHIC_ANALYSIS, 
            QueryIntent.EQUITY_ANALYSIS,
            QueryIntent.COVERAGE_ANALYSIS
        ]:
            builder.enable_isochrone_export()
        
        return builder.build()
    
    def _get_osm_mapping(self, poi_category: str) -> Optional[Dict[str, str]]:
        """Get OSM type/name mapping for POI category."""
        
        category_mappings = {
            'healthcare': {'type': 'amenity', 'name': 'hospital'},
            'education': {'type': 'amenity', 'name': 'school'},
            'recreation': {'type': 'leisure', 'name': 'park'},
            'food_and_drink': {'type': 'amenity', 'name': 'restaurant'},
            'transportation': {'type': 'highway', 'name': 'bus_stop'},
            'finance': {'type': 'amenity', 'name': 'bank'},
        }
        
        return category_mappings.get(poi_category)
    
    def _generate_suggestions(
        self, 
        entities: List[ExtractedEntity], 
        classification: IntentClassification
    ) -> List[str]:
        """Generate suggestions for improving the query."""
        
        suggestions = []
        
        # Check for missing entities
        entity_types = {e.entity_type for e in entities}
        
        if EntityType.LOCATION not in entity_types:
            suggestions.append("Consider specifying a location (city, state or coordinates)")
        
        if EntityType.POI_TYPE not in entity_types and classification.primary_intent != QueryIntent.POI_DISCOVERY:
            suggestions.append("Consider specifying what type of facility you're interested in")
        
        if EntityType.TIME_CONSTRAINT not in entity_types and EntityType.DISTANCE_CONSTRAINT not in entity_types:
            suggestions.append("Consider adding time or distance constraints (e.g., 'within 15 minutes')")
        
        if EntityType.TRAVEL_MODE not in entity_types:
            suggestions.append("Consider specifying travel mode (walking, driving, or biking)")
        
        # Intent-specific suggestions
        if classification.primary_intent == QueryIntent.EQUITY_ANALYSIS:
            if EntityType.DEMOGRAPHIC not in entity_types:
                suggestions.append("For equity analysis, consider specifying demographic groups to compare")
        
        if classification.primary_intent == QueryIntent.DEMOGRAPHIC_ANALYSIS:
            if EntityType.DEMOGRAPHIC not in entity_types:
                suggestions.append("Consider specifying which demographic variables to analyze")
        
        return suggestions[:3]  # Limit to top 3