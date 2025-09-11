# Natural Language Interface

SocialMapper now supports natural language queries, making spatial analysis accessible to users who prefer plain English over technical configurations. The Natural Language Processing (NLP) system automatically converts conversational queries into structured analysis configurations.

## Overview

The Natural Language Interface consists of three main components:

1. **Entity Extraction** - Identifies locations, POI types, time constraints, demographics, and travel modes
2. **Intent Classification** - Determines what type of analysis to perform  
3. **Query Translation** - Converts parsed information into analysis configurations

## Quick Start

```python
import asyncio
from socialmapper.nlp import NLQueryProcessor
from socialmapper.api import SocialMapperClient

async def natural_language_analysis():
    processor = NLQueryProcessor()
    
    # Process natural language query
    result = await processor.process_natural_query(
        "Find hospitals within 20 minutes of low-income areas in Boston"
    )
    
    if result.is_ok():
        query_result = result.unwrap()
        config = query_result.config
        
        # Use with SocialMapper client
        with SocialMapperClient() as client:
            analysis = client.run_analysis(config)
            
        print(f"Found {analysis.poi_count} hospitals")
    
asyncio.run(natural_language_analysis())
```

## Supported Query Types

### Accessibility Analysis
Find facilities within travel time or distance constraints.

**Examples:**
- `"Find hospitals within 30 minutes of downtown Boston"`
- `"Show me libraries accessible by walking in 15 minutes from Chicago"`
- `"What schools can I reach by bike in San Francisco?"`

**Generated Configuration:**
- Location geocoding
- POI type specification
- Travel time/distance constraints
- Travel mode settings

### POI Discovery
Discover what's available around a location.

**Examples:**
- `"What restaurants are near my location?"`
- `"Show me all parks within 20 minutes of Portland, OR"`
- `"Discover healthcare facilities around Seattle"`

**Features:**
- Automatic POI categorization
- Flexible location specification
- Travel time boundaries

### Demographic Analysis
Analyze population characteristics around facilities.

**Examples:**
- `"Show demographics around libraries in low-income areas"`
- `"What is the population served by hospitals in Boston?"`
- `"Analyze age demographics near schools in Denver"`

**Capabilities:**
- Automatic census variable selection
- Demographic constraint filtering
- Population aggregation

### Equity Analysis
Compare access across different demographic groups.

**Examples:**
- `"Compare hospital access between high and low-income areas"`
- `"Show access disparities for grocery stores in minority communities"`
- `"Analyze equity of park access in different neighborhoods"`

**Features:**
- Multi-group comparison
- Disparity metrics
- Equity visualization

### Coverage Analysis
Analyze service area coverage and reach.

**Examples:**
- `"How much area is covered by libraries in Chicago?"`
- `"What percentage of the city can reach a hospital in 15 minutes?"`
- `"Show total coverage area for emergency services"`

### Location Optimization
Find optimal locations for new facilities.

**Examples:**
- `"Where should we place a new library for maximum coverage?"`
- `"What is the best location for a new hospital?"`
- `"Recommend optimal sites for emergency services"`

**Capabilities:**
- Coverage maximization
- Gap identification
- Multi-criteria optimization

## Entity Types

The NLP system can extract and understand various types of entities from natural language:

### Location Entities
- **City, State**: "Boston, MA", "San Francisco, California"
- **City Only**: "Chicago", "Seattle", "Denver"  
- **Coordinates**: "42.3601, -71.0589"

### POI Entities
- **Healthcare**: hospitals, clinics, medical centers, pharmacies
- **Education**: schools, libraries, universities
- **Food**: restaurants, grocery stores, supermarkets
- **Recreation**: parks, recreation centers, gyms
- **Transportation**: bus stops, transit stations, gas stations
- **Services**: banks, post offices, government offices

### Time Constraints
- **Within/Under**: "within 15 minutes", "under 30 minutes"
- **Maximum**: "maximum of 45 minutes", "max 20 min"
- **Informal**: "20 minute walk", "5-min drive"

### Distance Constraints  
- **Miles**: "within 2 miles", "3.5 miles away"
- **Kilometers**: "within 5 km", "10 kilometers radius"
- **Meters**: "500 meters", "1000m"

### Demographics
- **Income**: "low-income", "high-income", "wealthy areas"
- **Age**: "elderly", "seniors", "young families"
- **Race/Ethnicity**: "minority communities", "diverse areas"
- **Urban/Rural**: "urban areas", "suburban", "rural communities"

### Travel Modes
- **Walking**: "walking", "on foot", "pedestrian"
- **Driving**: "driving", "by car", "vehicle"
- **Biking**: "biking", "bicycle", "cycling"
- **Transit**: "public transit", "bus", "train"

## Query Processing Pipeline

### 1. Entity Extraction
```python
from socialmapper.nlp import EntityExtractor

extractor = EntityExtractor()
entities = extractor.extract_entities(
    "Find hospitals within 20 minutes of Boston, MA"
)

for entity in entities:
    print(f"{entity.entity_type.name}: {entity.text}")
    # Output:
    # POI_TYPE: hospitals
    # TIME_CONSTRAINT: 20 minutes  
    # LOCATION: Boston, MA
```

### 2. Intent Classification
```python
from socialmapper.nlp import IntentClassifier

classifier = IntentClassifier()
intent = classifier.classify_intent(
    "Compare access between rich and poor areas"
)

print(f"Primary Intent: {intent.primary_intent.name}")
print(f"Confidence: {intent.confidence:.1%}")
# Output:
# Primary Intent: EQUITY_ANALYSIS
# Confidence: 95.0%
```

### 3. Query Translation
```python
from socialmapper.nlp import QueryTranslator

translator = QueryTranslator()
result = translator.translate(entities, intent)

print("Generated Configuration:")
for key, value in result.config.items():
    print(f"  {key}: {value}")
```

## Advanced Features

### Query Explanation
Get detailed explanations of how queries are processed:

```python
processor = NLQueryProcessor()
result = await processor.process_natural_query(
    "Find libraries within walking distance in Chicago"
)

if result.is_ok():
    query_result = result.unwrap()
    explanation = processor.explain_query_processing(query_result)
    print(explanation)
```

**Sample Output:**
```
Query: "Find libraries within walking distance in Chicago"

Detected Intent: ACCESSIBILITY_ANALYSIS
Confidence: 85%
Reasoning: Found accessibility keywords and location

Entities Extracted:
  • POI_TYPE: 'libraries' (category: education)
  • TRAVEL_MODE: 'walking' (mode: walk)
  • LOCATION: 'Chicago' (city)

Analysis Configuration:
  • Location: Chicago, 
  • POI Type: amenity/library
  • Travel Time: 15 minutes
  • Travel Mode: walk

Suggestions for Improvement:
  💡 Consider specifying the state for more accurate geocoding
  💡 Add specific time constraint if 15 minutes is not desired
```

### Batch Processing
Process multiple queries efficiently:

```python
queries = [
    "Find hospitals in Boston",
    "Show parks near Seattle", 
    "Compare library access in different neighborhoods"
]

results = []
for query in queries:
    result = await processor.process_natural_query(query)
    results.append(result)
```

### Custom Entity Patterns
Extend the system with custom entity patterns:

```python
from socialmapper.nlp.entities import EntityExtractor

extractor = EntityExtractor()

# Add custom POI patterns
extractor.poi_patterns[r'\b(?:coffee shops?|cafes?)\b'] = {
    'category': 'food_and_drink',
    'osm_type': 'amenity', 
    'osm_name': 'cafe'
}
```

## Integration Patterns

### With API Client
```python
async def nlp_analysis_workflow(query: str):
    processor = NLQueryProcessor()
    
    # Process query
    result = await processor.process_natural_query(query)
    
    if result.is_err():
        return f"Error: {result.unwrap_err().message}"
    
    query_result = result.unwrap()
    
    # Run analysis
    with SocialMapperClient() as client:
        if query_result.intent.primary_intent == QueryIntent.POI_DISCOVERY:
            # Use POI discovery method
            analysis = client.discover_nearby_pois(
                location=extract_location(query_result),
                travel_time=extract_time(query_result),
                poi_categories=extract_poi_categories(query_result)
            )
        else:
            # Use standard analysis
            analysis = client.run_analysis(query_result.config)
    
    return analysis
```

### With Batch Processing
```python
from socialmapper.nlp import NLQueryProcessor
from socialmapper.api import SocialMapperClient

def process_queries_batch(queries: list[str]) -> list[dict]:
    """Process multiple natural language queries in batch."""
    processor = NLQueryProcessor()
    client = SocialMapperClient()
    results = []
    
    for query in queries:
        result = processor.process_natural_query(query)
        
        if result.is_ok():
            query_result = result.unwrap()
            results.append({
                "query": query,
                "intent": query_result.intent.primary_intent.name,
                "confidence": query_result.intent.confidence,
                "entities": len(query_result.entities),
                "config": query_result.config,
                "suggestions": query_result.suggestions
            })
        else:
            results.append({
                "query": query,
                "error": result.unwrap_err().message
            })
    
    return results
```

### With Command Line
```python
import click
from socialmapper.nlp import NLQueryProcessor
from socialmapper.api import SocialMapperClient

@click.command()
@click.argument('query')
async def analyze_query(query: str):
    """Analyze a natural language query."""
    
    processor = NLQueryProcessor()
    result = await processor.process_natural_query(query)
    
    if result.is_ok():
        query_result = result.unwrap()
        
        click.echo(f"Intent: {query_result.intent.primary_intent.name}")
        click.echo(f"Confidence: {query_result.intent.confidence:.1%}")
        
        # Run analysis
        with SocialMapperClient() as client:
            analysis = client.run_analysis(query_result.config)
            click.echo(f"Found {analysis.poi_count} POIs")
    else:
        click.echo(f"Error: {result.unwrap_err().message}")
```

## Error Handling

The NLP system provides detailed error information and suggestions:

### Common Error Types
- **Empty Query**: Query string is empty or whitespace only
- **Ambiguous Intent**: Multiple possible interpretations  
- **Missing Entities**: Required information not found
- **Invalid Configuration**: Generated config fails validation

### Error Recovery
```python
result = await processor.process_natural_query(query)

match result:
    case Ok(query_result):
        if query_result.warnings:
            print("Warnings:", query_result.warnings)
        if query_result.suggestions:
            print("Suggestions:", query_result.suggestions)
        
        config = query_result.config
        
    case Err(error):
        print(f"Error: {error.message}")
        if error.context:
            print(f"Context: {error.context}")
```

## Performance Considerations

### Async Processing
All NLP operations are async-aware and can be run concurrently:

```python
async def process_multiple_queries(queries: List[str]):
    processor = NLQueryProcessor()
    
    # Process queries concurrently
    tasks = [
        processor.process_natural_query(query) 
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

### Caching
Entity extraction and intent classification results can be cached:

```python
from functools import lru_cache

class CachedNLProcessor(NLQueryProcessor):
    @lru_cache(maxsize=100)
    def _cached_entity_extraction(self, query: str):
        return self.entity_extractor.extract_entities(query)
```

## Best Practices

### Query Formulation
- **Be Specific**: Include location, POI type, and constraints
- **Use Natural Language**: Write as you would speak
- **Include Context**: Mention demographic groups or specific needs

**Good Examples:**
- `"Find grocery stores within 15 minutes by walking for elderly residents in Portland"`
- `"Compare hospital access between high and low-income areas in Denver"`

**Avoid:**
- `"Find stuff"` (too vague)
- `"Analysis"` (no specific intent)

### Error Handling
- Always check result status before using
- Display warnings and suggestions to users
- Provide fallback options for failed queries

### Integration
- Use async/await for better performance
- Implement proper error boundaries
- Cache frequently used configurations

## Examples and Demos

See the complete example in `examples/nlp_demo.py` for:
- Interactive query processing
- Integration with SocialMapper client
- Error handling patterns
- Batch processing examples

## Extending the System

### Adding New Intents
```python
from socialmapper.nlp.intents import QueryIntent

class CustomQueryIntent(Enum):
    ENVIRONMENTAL_ANALYSIS = auto()
    SAFETY_ANALYSIS = auto()

# Add to intent classifier patterns
classifier.intent_patterns[CustomQueryIntent.ENVIRONMENTAL_ANALYSIS] = {
    'keywords': ['pollution', 'air quality', 'environmental', 'toxic'],
    'phrases': [r'\benvironmental\s+(?:impact|analysis|assessment)\b'],
    'weight': 1.2
}
```

### Custom Entity Types
```python
from socialmapper.nlp.entities import EntityType, ExtractedEntity

class WeatherEntity(ExtractedEntity):
    weather_condition: str
    temperature_range: Optional[tuple[int, int]] = None
    
    def __post_init__(self):
        self.entity_type = EntityType.WEATHER  # Add to EntityType enum
```

The Natural Language Interface makes SocialMapper accessible to a broader audience, enabling users to perform sophisticated spatial analysis using conversational queries rather than technical configurations.