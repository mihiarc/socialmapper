"""Natural Language Processing module for SocialMapper.

This module provides natural language query processing capabilities,
allowing users to express spatial analysis requests in plain English
and automatically converting them to structured analysis configurations.

Example:
    ```python
    from socialmapper.nlp import NLQueryProcessor
    
    processor = NLQueryProcessor()
    config = await processor.process_natural_query(
        "Find hospitals within 20 minutes of low-income areas in Boston"
    )
    ```
"""

from .processor import NLQueryProcessor
from .entities import (
    EntityType,
    ExtractedEntity,
    LocationEntity,
    POIEntity,
    TimeConstraintEntity,
    DemographicEntity,
)
from .intents import QueryIntent, IntentClassifier
from .translator import QueryTranslator

__all__ = [
    "NLQueryProcessor", 
    "EntityType",
    "ExtractedEntity",
    "LocationEntity", 
    "POIEntity",
    "TimeConstraintEntity",
    "DemographicEntity",
    "QueryIntent",
    "IntentClassifier",
    "QueryTranslator",
]