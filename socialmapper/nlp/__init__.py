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

from .entities import (
    DemographicEntity,
    EntityType,
    ExtractedEntity,
    LocationEntity,
    POIEntity,
    TimeConstraintEntity,
)
from .intents import IntentClassifier, QueryIntent
from .processor import NLQueryProcessor
from .translator import QueryTranslator

__all__ = [
    "DemographicEntity",
    "EntityType",
    "ExtractedEntity",
    "IntentClassifier",
    "LocationEntity",
    "NLQueryProcessor",
    "POIEntity",
    "QueryIntent",
    "QueryTranslator",
    "TimeConstraintEntity",
]
