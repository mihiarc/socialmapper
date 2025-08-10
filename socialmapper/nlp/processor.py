"""Main natural language query processor for SocialMapper.

This module provides the primary interface for processing natural language
queries and converting them to analysis configurations.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from ..api.builder import SocialMapperBuilder
from ..api.result_types import Result, Ok, Err, Error, ErrorType
from .entities import EntityExtractor, ExtractedEntity
from .intents import IntentClassifier, IntentClassification, QueryIntent
from .translator import QueryTranslator, TranslationResult


logger = logging.getLogger(__name__)


@dataclass
class NLQueryResult:
    """Result of processing a natural language query."""
    
    original_query: str
    entities: List[ExtractedEntity]
    intent: IntentClassification
    translation: TranslationResult
    config: Dict[str, Any]
    suggestions: List[str]
    warnings: List[str]


class NLQueryProcessor:
    """Process natural language queries into SocialMapper analysis configurations.
    
    This class provides the main interface for the natural language processing
    capabilities of SocialMapper. It combines entity extraction, intent classification,
    and query translation to convert plain English queries into structured analysis
    configurations.
    
    Example:
        ```python
        processor = NLQueryProcessor()
        
        # Simple query
        result = await processor.process_natural_query(
            "Find hospitals within 20 minutes of low-income areas in Boston"
        )
        
        if result.is_ok():
            query_result = result.unwrap()
            config = query_result.config
            # Use config with SocialMapperClient...
        ```
    """
    
    def __init__(self):
        """Initialize the natural language query processor."""
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier()
        self.query_translator = QueryTranslator()
        
        logger.info("NLQueryProcessor initialized")
    
    async def process_natural_query(self, query: str) -> Result[NLQueryResult, Error]:
        """Process a natural language query into analysis configuration.
        
        This is the main entry point for natural language processing. It performs
        the complete pipeline: entity extraction, intent classification, and
        translation to analysis configuration.
        
        Args:
            query: Natural language query string
            
        Returns:
            Result containing NLQueryResult or Error
            
        Example:
            ```python
            processor = NLQueryProcessor()
            
            result = await processor.process_natural_query(
                "Show me libraries within walking distance in Chicago"
            )
            
            match result:
                case Ok(query_result):
                    print(f"Intent: {query_result.intent.primary_intent}")
                    print(f"Entities found: {len(query_result.entities)}")
                    config = query_result.config
                case Err(error):
                    print(f"Processing failed: {error}")
            ```
        """
        try:
            if not query or not query.strip():
                return Err(Error(
                    type=ErrorType.VALIDATION,
                    message="Query cannot be empty",
                    context={"query": query}
                ))
            
            query = query.strip()
            logger.info(f"Processing natural language query: '{query[:100]}{'...' if len(query) > 100 else ''}'")
            
            # Step 1: Extract entities
            entities = await self._extract_entities_async(query)
            logger.debug(f"Extracted {len(entities)} entities: {[e.entity_type.name for e in entities]}")
            
            # Step 2: Classify intent
            intent = await self._classify_intent_async(query)
            logger.debug(f"Classified intent: {intent.primary_intent.name} (confidence: {intent.confidence:.2f})")
            
            # Step 3: Translate to configuration
            translation = await self._translate_query_async(entities, intent)
            logger.debug(f"Translation completed with {len(translation.warnings)} warnings")
            
            # Step 4: Combine results
            all_suggestions = list(set(
                translation.suggestions + 
                self.intent_classifier.suggest_enhancements(intent)
            ))
            
            query_result = NLQueryResult(
                original_query=query,
                entities=entities,
                intent=intent,
                translation=translation,
                config=translation.config,
                suggestions=all_suggestions,
                warnings=translation.warnings
            )
            
            logger.info(f"Query processed successfully - Intent: {intent.primary_intent.name}, "
                       f"Entities: {len(entities)}, Confidence: {intent.confidence:.2f}")
            
            return Ok(query_result)
            
        except Exception as e:
            logger.error(f"Error processing natural language query: {e}", exc_info=True)
            return Err(Error(
                type=ErrorType.PROCESSING,
                message=f"Failed to process natural language query: {str(e)}",
                context={"query": query},
                cause=e
            ))
    
    async def _extract_entities_async(self, query: str) -> List[ExtractedEntity]:
        """Extract entities asynchronously."""
        # Run entity extraction in thread pool for CPU-bound work
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.entity_extractor.extract_entities, query
        )
    
    async def _classify_intent_async(self, query: str) -> IntentClassification:
        """Classify intent asynchronously."""
        # Run intent classification in thread pool for CPU-bound work
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.intent_classifier.classify_intent, query
        )
    
    async def _translate_query_async(
        self, entities: List[ExtractedEntity], intent: IntentClassification
    ) -> TranslationResult:
        """Translate query to configuration asynchronously."""
        # Run translation in thread pool for CPU-bound work
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.query_translator.translate, entities, intent
        )
    
    def explain_query_processing(self, query_result: NLQueryResult) -> str:
        """Generate human-readable explanation of query processing.
        
        Args:
            query_result: Result from process_natural_query()
            
        Returns:
            Human-readable explanation string
        """
        explanation_parts = []
        
        # Original query
        explanation_parts.append(f"Query: \"{query_result.original_query}\"")
        explanation_parts.append("")
        
        # Intent classification
        intent = query_result.intent
        explanation_parts.append(f"Detected Intent: {intent.primary_intent.name}")
        explanation_parts.append(f"Confidence: {intent.confidence:.1%}")
        if intent.reasoning:
            explanation_parts.append(f"Reasoning: {intent.reasoning}")
        explanation_parts.append("")
        
        # Entities found
        if query_result.entities:
            explanation_parts.append("Entities Extracted:")
            for entity in query_result.entities:
                entity_info = f"  • {entity.entity_type.name}: '{entity.text}'"
                if hasattr(entity, 'poi_category') and entity.poi_category:
                    entity_info += f" (category: {entity.poi_category})"
                elif hasattr(entity, 'minutes') and entity.minutes:
                    entity_info += f" (time: {entity.minutes} minutes)"
                elif hasattr(entity, 'location_name') and entity.location_name:
                    entity_info += f" (location: {entity.location_name})"
                explanation_parts.append(entity_info)
            explanation_parts.append("")
        
        # Analysis configuration
        config = query_result.config
        explanation_parts.append("Analysis Configuration:")
        
        if 'geocode_area' in config:
            explanation_parts.append(f"  • Location: {config['geocode_area']}, {config.get('state', 'N/A')}")
        elif 'poi_discovery_config' in config:
            poi_config = config['poi_discovery_config']
            explanation_parts.append(f"  • Location: {poi_config.location}")
        
        if 'poi_type' in config and 'poi_name' in config:
            explanation_parts.append(f"  • POI Type: {config['poi_type']}/{config['poi_name']}")
        elif 'poi_discovery_config' in config:
            poi_config = config['poi_discovery_config']
            if poi_config.poi_categories:
                explanation_parts.append(f"  • POI Categories: {', '.join(poi_config.poi_categories)}")
            else:
                explanation_parts.append("  • POI Categories: All available")
        
        if 'travel_time' in config:
            explanation_parts.append(f"  • Travel Time: {config['travel_time']} minutes")
        
        if 'travel_mode' in config:
            explanation_parts.append(f"  • Travel Mode: {config['travel_mode']}")
        
        if 'census_variables' in config:
            explanation_parts.append(f"  • Census Variables: {', '.join(config['census_variables'])}")
        
        explanation_parts.append("")
        
        # Warnings
        if query_result.warnings:
            explanation_parts.append("Warnings:")
            for warning in query_result.warnings:
                explanation_parts.append(f"  ⚠ {warning}")
            explanation_parts.append("")
        
        # Suggestions
        if query_result.suggestions:
            explanation_parts.append("Suggestions for Improvement:")
            for suggestion in query_result.suggestions:
                explanation_parts.append(f"  💡 {suggestion}")
        
        return "\n".join(explanation_parts)
    
    def get_example_queries(self) -> Dict[str, List[str]]:
        """Get example queries for each intent type.
        
        Returns:
            Dictionary mapping intent types to example queries
        """
        return {
            "Accessibility Analysis": [
                "Find hospitals within 30 minutes of downtown Boston",
                "Show me libraries accessible by walking in 15 minutes from Chicago",
                "What schools can I reach by bike in San Francisco?"
            ],
            
            "POI Discovery": [
                "What restaurants are near my location?", 
                "Show me all parks within 20 minutes of Portland, OR",
                "Discover healthcare facilities around Seattle"
            ],
            
            "Demographic Analysis": [
                "Show demographics around libraries in low-income areas",
                "What is the population served by hospitals in Boston?",
                "Analyze age demographics near schools in Denver"
            ],
            
            "Equity Analysis": [
                "Compare hospital access between high and low-income areas",
                "Show access disparities for grocery stores in minority communities",
                "Analyze equity of park access in different neighborhoods"
            ],
            
            "Coverage Analysis": [
                "How much area is covered by libraries in Chicago?",
                "What percentage of the city can reach a hospital in 15 minutes?",
                "Show total coverage area for emergency services"
            ],
            
            "Travel Time Analysis": [
                "How long does it take to reach the nearest hospital?",
                "Show average travel time to grocery stores by neighborhood",
                "What is the commute time to schools in different areas?"
            ],
            
            "Location Optimization": [
                "Where should we place a new library for maximum coverage?",
                "What is the best location for a new hospital?",
                "Recommend optimal sites for emergency services"
            ],
            
            "Comparison Analysis": [
                "Compare library access in Boston versus New York",
                "Show difference in healthcare access between urban and rural areas",
                "How does park access compare across different cities?"
            ]
        }