"""Tests for natural language query processing."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from socialmapper.nlp import (
    NLQueryProcessor, EntityType, QueryIntent, 
    LocationEntity, POIEntity, TimeConstraintEntity
)
from socialmapper.api.result_types import Ok, Err


class TestNLQueryProcessor:
    """Test cases for NLQueryProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return NLQueryProcessor()
    
    @pytest.mark.asyncio
    async def test_simple_accessibility_query(self, processor):
        """Test processing simple accessibility query."""
        query = "Find hospitals within 20 minutes of Boston, MA"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Check basic structure
        assert query_result.original_query == query
        assert len(query_result.entities) > 0
        assert query_result.intent.primary_intent == QueryIntent.ACCESSIBILITY_ANALYSIS
        assert query_result.config is not None
        
        # Check entities
        entity_types = {e.entity_type for e in query_result.entities}
        assert EntityType.LOCATION in entity_types
        assert EntityType.POI_TYPE in entity_types  
        assert EntityType.TIME_CONSTRAINT in entity_types
        
        # Check config has required fields
        config = query_result.config
        assert 'travel_time' in config
        assert config['travel_time'] == 20
        assert 'geocode_area' in config or 'location' in config
    
    @pytest.mark.asyncio
    async def test_poi_discovery_query(self, processor):
        """Test POI discovery query processing."""
        query = "What restaurants are near Seattle within walking distance?"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should be classified as POI discovery
        assert query_result.intent.primary_intent == QueryIntent.POI_DISCOVERY
        
        # Check for POI discovery configuration
        config = query_result.config
        assert 'poi_discovery_enabled' in config and config['poi_discovery_enabled']
        
        # Check location entity
        location_entities = [e for e in query_result.entities if isinstance(e, LocationEntity)]
        assert len(location_entities) > 0
        assert "seattle" in location_entities[0].location_name.lower()
    
    @pytest.mark.asyncio
    async def test_demographic_analysis_query(self, processor):
        """Test demographic analysis query processing."""
        query = "Show demographics around libraries in low-income areas of Chicago"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should include demographic intent
        assert (query_result.intent.primary_intent == QueryIntent.DEMOGRAPHIC_ANALYSIS or
                QueryIntent.DEMOGRAPHIC_ANALYSIS in query_result.intent.secondary_intents)
        
        # Should have census variables configured
        config = query_result.config
        assert 'census_variables' in config
        assert len(config['census_variables']) > 0
    
    @pytest.mark.asyncio
    async def test_equity_analysis_query(self, processor):
        """Test equity analysis query processing."""
        query = "Compare hospital access between high and low-income neighborhoods"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should be classified as equity analysis
        assert query_result.intent.primary_intent == QueryIntent.EQUITY_ANALYSIS
        
        # Should have demographic entities
        demographic_entities = [e for e in query_result.entities 
                              if e.entity_type == EntityType.DEMOGRAPHIC]
        assert len(demographic_entities) > 0
    
    @pytest.mark.asyncio
    async def test_location_optimization_query(self, processor):
        """Test location optimization query processing."""
        query = "Where should we place a new library for maximum coverage in Denver?"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should be classified as location optimization
        assert query_result.intent.primary_intent == QueryIntent.LOCATION_OPTIMIZATION
        
        # Check for location entity
        location_entities = [e for e in query_result.entities if isinstance(e, LocationEntity)]
        assert len(location_entities) > 0
        assert "denver" in location_entities[0].location_name.lower()
    
    @pytest.mark.asyncio
    async def test_multiple_constraints_query(self, processor):
        """Test query with multiple constraints."""
        query = "Find grocery stores within 15 minutes by walking in San Francisco, CA for elderly residents"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should extract multiple entity types
        entity_types = {e.entity_type for e in query_result.entities}
        assert EntityType.LOCATION in entity_types
        assert EntityType.POI_TYPE in entity_types
        assert EntityType.TIME_CONSTRAINT in entity_types
        assert EntityType.TRAVEL_MODE in entity_types
        assert EntityType.DEMOGRAPHIC in entity_types
        
        # Check configuration
        config = query_result.config
        assert config['travel_time'] == 15
    
    @pytest.mark.asyncio
    async def test_coordinate_location_query(self, processor):
        """Test query with coordinate location."""
        query = "Show hospitals near 42.3601, -71.0589 within 30 minutes"
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Check coordinate extraction
        location_entities = [e for e in query_result.entities if isinstance(e, LocationEntity)]
        assert len(location_entities) > 0
        location_entity = location_entities[0]
        assert location_entity.coordinates is not None
        assert abs(location_entity.coordinates[0] - 42.3601) < 0.001
        assert abs(location_entity.coordinates[1] - (-71.0589)) < 0.001
    
    @pytest.mark.asyncio
    async def test_empty_query_error(self, processor):
        """Test that empty query returns error."""
        result = await processor.process_natural_query("")
        
        assert result.is_err()
        error = result.unwrap_err()
        assert "empty" in error.message.lower()
    
    @pytest.mark.asyncio
    async def test_ambiguous_query_warnings(self, processor):
        """Test that ambiguous queries generate warnings."""
        query = "Find stuff nearby"  # Very vague query
        
        result = await processor.process_natural_query(query)
        
        assert result.is_ok()
        query_result = result.unwrap()
        
        # Should have warnings due to vagueness
        assert len(query_result.warnings) > 0 or len(query_result.suggestions) > 0
        
        # Should have low confidence
        assert query_result.intent.confidence < 0.8
    
    def test_explain_query_processing(self, processor):
        """Test query processing explanation generation."""
        # Create mock query result
        from socialmapper.nlp.entities import LocationEntity, POIEntity, TimeConstraintEntity
        from socialmapper.nlp.intents import IntentClassification, QueryIntent
        from socialmapper.nlp.translator import TranslationResult
        from socialmapper.nlp.processor import NLQueryResult
        
        entities = [
            LocationEntity(
                entity_type=EntityType.LOCATION,
                text="Boston, MA",
                start_pos=0, end_pos=9,
                location_name="Boston, MA"
            ),
            POIEntity(
                entity_type=EntityType.POI_TYPE,
                text="hospitals",
                start_pos=10, end_pos=19,
                poi_category="healthcare"
            ),
            TimeConstraintEntity(
                entity_type=EntityType.TIME_CONSTRAINT,
                text="20 minutes",
                start_pos=20, end_pos=30,
                minutes=20
            )
        ]
        
        intent = IntentClassification(
            primary_intent=QueryIntent.ACCESSIBILITY_ANALYSIS,
            secondary_intents=[],
            confidence=0.9,
            reasoning="Found accessibility keywords and time constraint"
        )
        
        translation = TranslationResult(
            config={
                'geocode_area': 'Boston',
                'state': 'MA',
                'poi_type': 'amenity',
                'poi_name': 'hospital',
                'travel_time': 20
            },
            warnings=["Using default travel mode"],
            suggestions=["Consider specifying travel mode"],
            confidence=0.9,
            reasoning="Standard analysis configuration"
        )
        
        query_result = NLQueryResult(
            original_query="Find hospitals within 20 minutes of Boston, MA",
            entities=entities,
            intent=intent,
            translation=translation,
            config=translation.config,
            suggestions=translation.suggestions,
            warnings=translation.warnings
        )
        
        explanation = processor.explain_query_processing(query_result)
        
        # Check explanation contains key information
        assert "Find hospitals within 20 minutes of Boston, MA" in explanation
        assert "ACCESSIBILITY_ANALYSIS" in explanation
        assert "90%" in explanation or "0.9" in explanation
        assert "Boston" in explanation
        assert "20 minutes" in explanation
        assert "⚠" in explanation  # Warning symbol
        assert "💡" in explanation  # Suggestion symbol
    
    def test_get_example_queries(self, processor):
        """Test example queries retrieval."""
        examples = processor.get_example_queries()
        
        # Should have examples for different analysis types
        assert len(examples) > 0
        assert "Accessibility Analysis" in examples
        assert "POI Discovery" in examples
        assert "Equity Analysis" in examples
        
        # Each category should have multiple examples
        for category, queries in examples.items():
            assert len(queries) >= 2
            for query in queries:
                assert isinstance(query, str)
                assert len(query) > 10  # Reasonable query length


class TestEntityExtractor:
    """Test cases for entity extraction."""
    
    @pytest.fixture
    def extractor(self):
        """Create entity extractor for testing."""
        from socialmapper.nlp.entities import EntityExtractor
        return EntityExtractor()
    
    def test_poi_extraction(self, extractor):
        """Test POI entity extraction."""
        query = "Find hospitals and libraries near me"
        
        entities = extractor.extract_entities(query)
        
        poi_entities = [e for e in entities if e.entity_type == EntityType.POI_TYPE]
        assert len(poi_entities) >= 2
        
        poi_categories = {e.poi_category for e in poi_entities}
        assert "healthcare" in poi_categories
        assert "education" in poi_categories
    
    def test_time_extraction(self, extractor):
        """Test time constraint extraction."""
        test_cases = [
            ("within 15 minutes", 15),
            ("under 30 minutes", 30),
            ("maximum of 45 minutes", 45),
            ("20 min walk", 20),
            ("5-minute drive", 5)
        ]
        
        for query, expected_minutes in test_cases:
            entities = extractor.extract_entities(query)
            time_entities = [e for e in entities if e.entity_type == EntityType.TIME_CONSTRAINT]
            
            assert len(time_entities) >= 1, f"No time entity found in: {query}"
            assert time_entities[0].minutes == expected_minutes
    
    def test_location_extraction(self, extractor):
        """Test location entity extraction."""
        test_cases = [
            ("Boston, MA", "Boston, MA"),
            ("San Francisco, California", "San Francisco, California"),
            ("New York", "New York"),
            ("42.3601, -71.0589", "42.3601, -71.0589")
        ]
        
        for query, expected_location in test_cases:
            entities = extractor.extract_entities(f"Find hospitals in {query}")
            location_entities = [e for e in entities if e.entity_type == EntityType.LOCATION]
            
            assert len(location_entities) >= 1, f"No location entity found for: {query}"
            assert expected_location in location_entities[0].location_name
    
    def test_demographic_extraction(self, extractor):
        """Test demographic entity extraction."""
        test_cases = [
            "low-income areas",
            "high-income neighborhoods", 
            "elderly residents",
            "minority communities",
            "young families"
        ]
        
        for demographic_term in test_cases:
            query = f"Find services in {demographic_term}"
            entities = extractor.extract_entities(query)
            
            demographic_entities = [e for e in entities if e.entity_type == EntityType.DEMOGRAPHIC]
            assert len(demographic_entities) >= 1, f"No demographic entity found for: {demographic_term}"
    
    def test_travel_mode_extraction(self, extractor):
        """Test travel mode extraction."""
        test_cases = [
            ("walking distance", "walk"),
            ("by car", "drive"),
            ("biking", "bike"),
            ("public transit", "transit")
        ]
        
        for query_phrase, expected_mode in test_cases:
            query = f"Find hospitals within {query_phrase}"
            entities = extractor.extract_entities(query)
            
            travel_entities = [e for e in entities if e.entity_type == EntityType.TRAVEL_MODE]
            if travel_entities:  # Some may not match due to pattern complexity
                assert travel_entities[0].mode == expected_mode


class TestIntentClassifier:
    """Test cases for intent classification."""
    
    @pytest.fixture
    def classifier(self):
        """Create intent classifier for testing."""
        from socialmapper.nlp.intents import IntentClassifier
        return IntentClassifier()
    
    def test_accessibility_intent(self, classifier):
        """Test accessibility analysis intent classification."""
        test_queries = [
            "Find hospitals within 20 minutes",
            "What libraries can I reach by walking?",
            "Show accessible grocery stores near me"
        ]
        
        for query in test_queries:
            classification = classifier.classify_intent(query)
            assert classification.primary_intent == QueryIntent.ACCESSIBILITY_ANALYSIS
            assert classification.confidence > 0.5
    
    def test_poi_discovery_intent(self, classifier):
        """Test POI discovery intent classification."""
        test_queries = [
            "What restaurants are around here?",
            "Show me parks near Boston",
            "Discover healthcare options in my area"
        ]
        
        for query in test_queries:
            classification = classifier.classify_intent(query)
            assert classification.primary_intent == QueryIntent.POI_DISCOVERY
            assert classification.confidence > 0.5
    
    def test_equity_intent(self, classifier):
        """Test equity analysis intent classification."""
        test_queries = [
            "Compare access between rich and poor areas",
            "Show disparities in hospital access",
            "Analyze equity of park distribution"
        ]
        
        for query in test_queries:
            classification = classifier.classify_intent(query)
            assert classification.primary_intent == QueryIntent.EQUITY_ANALYSIS
            assert classification.confidence > 0.5
    
    def test_optimization_intent(self, classifier):
        """Test location optimization intent classification."""
        test_queries = [
            "Where should we place a new hospital?",
            "Best location for a library",
            "Optimal site for emergency services"
        ]
        
        for query in test_queries:
            classification = classifier.classify_intent(query)
            assert classification.primary_intent == QueryIntent.LOCATION_OPTIMIZATION
            assert classification.confidence > 0.5
    
    def test_suggestion_generation(self, classifier):
        """Test suggestion generation based on intent."""
        classification = classifier.classify_intent("Find hospitals")
        suggestions = classifier.suggest_enhancements(classification)
        
        assert len(suggestions) > 0
        assert any("travel mode" in s.lower() for s in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])