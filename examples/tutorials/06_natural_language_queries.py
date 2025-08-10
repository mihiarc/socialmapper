"""Tutorial: Natural Language Queries in SocialMapper

This tutorial demonstrates how to use SocialMapper's Natural Language Processing
capabilities to perform spatial analysis using conversational queries.

Learn how to:
1. Process natural language queries
2. Understand entity extraction and intent classification
3. Use NLP results with SocialMapper analysis
4. Handle errors and improve queries
"""

import asyncio
import sys
from pathlib import Path

# Add socialmapper to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from socialmapper.nlp import NLQueryProcessor
from socialmapper.api import SocialMapperClient


async def tutorial_basic_nlp():
    """Tutorial 1: Basic Natural Language Processing"""
    
    print("=" * 60)
    print("Tutorial 1: Basic Natural Language Processing")
    print("=" * 60)
    
    print("\n🤖 The NLP system converts natural language into analysis configs")
    print("Let's start with a simple query:")
    
    query = "Find hospitals within 20 minutes of Boston, MA"
    print(f'\nQuery: "{query}"')
    
    # Initialize the NLP processor
    processor = NLQueryProcessor()
    
    # Process the natural language query
    result = await processor.process_natural_query(query)
    
    if result.is_ok():
        query_result = result.unwrap()
        
        print(f"\n✅ Query processed successfully!")
        print(f"📋 Detected Intent: {query_result.intent.primary_intent.name}")
        print(f"📊 Confidence: {query_result.intent.confidence:.1%}")
        print(f"🏷️  Entities Found: {len(query_result.entities)}")
        
        print(f"\n🔍 Extracted Entities:")
        for entity in query_result.entities:
            entity_info = f"   • {entity.entity_type.name}: '{entity.text}'"
            
            # Add specific information based on entity type
            if hasattr(entity, 'poi_category'):
                entity_info += f" → Category: {entity.poi_category}"
            elif hasattr(entity, 'minutes'):
                entity_info += f" → Time: {entity.minutes} minutes"
            elif hasattr(entity, 'location_name'):
                entity_info += f" → Location: {entity.location_name}"
                
            print(entity_info)
        
        print(f"\n📋 Generated Configuration Keys:")
        for key in query_result.config.keys():
            print(f"   • {key}")
            
        if query_result.suggestions:
            print(f"\n💡 Suggestions to improve your query:")
            for suggestion in query_result.suggestions:
                print(f"   • {suggestion}")
    
    else:
        error = result.unwrap_err()
        print(f"❌ Error: {error.message}")


async def tutorial_different_query_types():
    """Tutorial 2: Understanding Different Query Types"""
    
    print("\n\n" + "=" * 60)
    print("Tutorial 2: Different Query Types and Intents")  
    print("=" * 60)
    
    processor = NLQueryProcessor()
    
    # Different types of queries to demonstrate various intents
    query_examples = [
        ("Accessibility", "Show me libraries within walking distance in Seattle"),
        ("POI Discovery", "What restaurants are around downtown Chicago?"),
        ("Demographics", "Analyze population around schools in low-income areas"),
        ("Equity", "Compare grocery access between rich and poor neighborhoods"),
        ("Optimization", "Where should we build a new hospital in Denver?"),
    ]
    
    for query_type, query in query_examples:
        print(f"\n🎯 {query_type} Query: \"{query}\"")
        
        result = await processor.process_natural_query(query)
        
        if result.is_ok():
            query_result = result.unwrap()
            print(f"   Intent: {query_result.intent.primary_intent.name}")
            print(f"   Confidence: {query_result.intent.confidence:.1%}")
            
            # Show key entities
            entity_types = {e.entity_type.name for e in query_result.entities}
            if entity_types:
                print(f"   Entities: {', '.join(sorted(entity_types))}")
        else:
            print(f"   ❌ Error: {result.unwrap_err().message}")


async def tutorial_nlp_with_analysis():
    """Tutorial 3: Using NLP with Actual Analysis"""
    
    print("\n\n" + "=" * 60)
    print("Tutorial 3: NLP Integration with Analysis")
    print("=" * 60)
    
    print("\n🔗 Now let's use NLP results to run actual spatial analysis")
    
    processor = NLQueryProcessor()
    
    # Use a simple, reliable query for demonstration
    query = "Find libraries within 15 minutes in Boston, MA"
    print(f'Query: "{query}"')
    
    # Process the query
    result = await processor.process_natural_query(query)
    
    if result.is_ok():
        query_result = result.unwrap()
        config = query_result.config
        
        print(f"\n✅ Query processed: {query_result.intent.primary_intent.name}")
        
        # Show the configuration that will be used
        print(f"\n📋 Analysis Configuration:")
        if 'geocode_area' in config:
            print(f"   • Location: {config['geocode_area']}, {config.get('state', 'N/A')}")
        if 'poi_type' in config and 'poi_name' in config:
            print(f"   • POI: {config['poi_type']}/{config['poi_name']}")
        if 'travel_time' in config:
            print(f"   • Travel Time: {config['travel_time']} minutes")
        if 'travel_mode' in config:
            print(f"   • Travel Mode: {config['travel_mode']}")
        
        print(f"\n🚀 Running analysis with NLP-generated configuration...")
        
        try:
            # Use the configuration with SocialMapper client
            with SocialMapperClient() as client:
                # Note: In a real scenario, you might want to add error handling
                # and check if required API keys are available
                
                print("   📝 Configuration ready for analysis")
                print("   💡 To run live analysis, ensure you have:")
                print("      • Census API key configured")
                print("      • Network connectivity")
                print("      • Sufficient API rate limits")
                
                # For demo purposes, we show the configuration instead of running
                # Uncomment the next line to run actual analysis:
                # analysis_result = client.run_analysis(config)
                
        except Exception as e:
            print(f"   Note: Demo mode - actual analysis not run ({e})")
    
    else:
        error = result.unwrap_err()
        print(f"❌ Query processing failed: {error.message}")


async def tutorial_query_refinement():
    """Tutorial 4: Query Refinement and Error Handling"""
    
    print("\n\n" + "=" * 60) 
    print("Tutorial 4: Query Refinement and Error Handling")
    print("=" * 60)
    
    processor = NLQueryProcessor()
    
    print("\n🎯 Let's see how the system handles unclear queries:")
    
    # Examples of queries that might need refinement
    unclear_queries = [
        "Find stuff nearby",  # Too vague
        "Show me things in Boston",  # No POI type
        "Hospitals in some city",  # No specific location
        "Find libraries",  # No location or constraints
    ]
    
    for query in unclear_queries:
        print(f'\n🔍 Query: "{query}"')
        
        result = await processor.process_natural_query(query)
        
        if result.is_ok():
            query_result = result.unwrap()
            
            print(f"   Intent: {query_result.intent.primary_intent.name}")
            print(f"   Confidence: {query_result.intent.confidence:.1%}")
            
            if query_result.warnings:
                print(f"   ⚠️  Warnings:")
                for warning in query_result.warnings:
                    print(f"      • {warning}")
            
            if query_result.suggestions:
                print(f"   💡 Suggestions:")
                for suggestion in query_result.suggestions[:2]:  # Show top 2
                    print(f"      • {suggestion}")
        
        else:
            error = result.unwrap_err()
            print(f"   ❌ Error: {error.message}")
    
    print(f"\n✨ Better Query Examples:")
    better_queries = [
        "Find grocery stores within 15 minutes of Boston, MA",
        "Show me parks within walking distance in Seattle, WA", 
        "Compare hospital access in high vs low-income areas of Denver",
        "Find libraries accessible by public transit in 20 minutes"
    ]
    
    for query in better_queries:
        print(f'   • "{query}"')


async def tutorial_advanced_features():
    """Tutorial 5: Advanced NLP Features"""
    
    print("\n\n" + "=" * 60)
    print("Tutorial 5: Advanced NLP Features")
    print("=" * 60)
    
    processor = NLQueryProcessor()
    
    print("\n📖 Query Explanation Feature:")
    print("The system can explain how it interpreted your query")
    
    query = "Find grocery stores within 15 minutes by walking in San Francisco for elderly residents"
    print(f'\nQuery: "{query}"')
    
    result = await processor.process_natural_query(query)
    
    if result.is_ok():
        query_result = result.unwrap()
        
        # Generate detailed explanation
        explanation = processor.explain_query_processing(query_result)
        print("\n" + "─" * 50)
        print("DETAILED EXPLANATION:")
        print("─" * 50)
        print(explanation)
    
    print(f"\n\n📚 Supported Query Examples by Category:")
    examples = processor.get_example_queries()
    
    for category, queries in list(examples.items())[:3]:  # Show first 3 categories
        print(f"\n🎯 {category}:")
        for query in queries[:2]:  # Show 2 examples per category
            print(f"   • \"{query}\"")


async def tutorial_batch_processing():
    """Tutorial 6: Batch Processing Multiple Queries"""
    
    print("\n\n" + "=" * 60)
    print("Tutorial 6: Batch Processing")
    print("=" * 60)
    
    processor = NLQueryProcessor()
    
    print("\n⚡ Processing multiple queries efficiently:")
    
    # Batch of queries for different cities
    queries = [
        "Find hospitals within 30 minutes of Boston, MA",
        "Show parks within walking distance in Seattle, WA",
        "Analyze library access in Chicago, IL", 
        "Compare grocery access in Denver, CO neighborhoods"
    ]
    
    print(f"Processing {len(queries)} queries...")
    
    # Process all queries concurrently
    tasks = [processor.process_natural_query(query) for query in queries]
    results = await asyncio.gather(*tasks)
    
    print(f"\n📊 Batch Processing Results:")
    for i, (query, result) in enumerate(zip(queries, results), 1):
        if result.is_ok():
            query_result = result.unwrap()
            print(f"   {i}. ✅ {query_result.intent.primary_intent.name} "
                  f"({query_result.intent.confidence:.1%})")
        else:
            print(f"   {i}. ❌ Failed")


async def tutorial_integration_patterns():
    """Tutorial 7: Integration Patterns"""
    
    print("\n\n" + "=" * 60)
    print("Tutorial 7: Integration Patterns") 
    print("=" * 60)
    
    print("\n🔧 Common integration patterns:")
    
    print("\n1. Simple Query-to-Analysis:")
    print("""
    async def analyze_query(query: str):
        processor = NLQueryProcessor()
        result = await processor.process_natural_query(query)
        
        if result.is_ok():
            config = result.unwrap().config
            with SocialMapperClient() as client:
                return client.run_analysis(config)
    """)
    
    print("\n2. With Error Handling:")
    print("""
    async def safe_analyze_query(query: str):
        try:
            processor = NLQueryProcessor()
            result = await processor.process_natural_query(query)
            
            match result:
                case Ok(query_result):
                    # Check confidence threshold
                    if query_result.intent.confidence < 0.7:
                        return {"status": "low_confidence", 
                               "suggestions": query_result.suggestions}
                    
                    config = query_result.config
                    # Proceed with analysis...
                    
                case Err(error):
                    return {"status": "error", "message": error.message}
                    
        except Exception as e:
            return {"status": "exception", "message": str(e)}
    """)
    
    print("\n3. Query Refinement Loop:")
    print("""
    async def interactive_analysis():
        processor = NLQueryProcessor()
        
        while True:
            query = input("Enter query: ")
            result = await processor.process_natural_query(query)
            
            if result.is_ok():
                query_result = result.unwrap()
                
                if query_result.suggestions:
                    print("Suggestions:", query_result.suggestions)
                    
                # Run analysis or ask for refinement
            else:
                print("Error:", result.unwrap_err().message)
    """)


async def run_complete_tutorial():
    """Run the complete NLP tutorial"""
    
    print("🎓 SocialMapper Natural Language Processing Tutorial")
    print("=" * 60)
    print("\nThis tutorial will teach you how to use natural language")
    print("to perform spatial analysis with SocialMapper.")
    print("\nPress Enter to start each section...")
    
    try:
        # Tutorial sections
        input("\nPress Enter to start Tutorial 1...")
        await tutorial_basic_nlp()
        
        input("\nPress Enter for Tutorial 2...")
        await tutorial_different_query_types()
        
        input("\nPress Enter for Tutorial 3...")
        await tutorial_nlp_with_analysis()
        
        input("\nPress Enter for Tutorial 4...")
        await tutorial_query_refinement()
        
        input("\nPress Enter for Tutorial 5...")
        await tutorial_advanced_features()
        
        input("\nPress Enter for Tutorial 6...")
        await tutorial_batch_processing()
        
        input("\nPress Enter for Tutorial 7...")
        await tutorial_integration_patterns()
        
    except KeyboardInterrupt:
        print("\n\nTutorial interrupted. Thank you!")
        return
    
    print("\n\n" + "=" * 60)
    print("🎉 Tutorial Complete!")
    print("=" * 60)
    print("\nYou've learned how to:")
    print("✅ Process natural language queries")
    print("✅ Understand intents and entities")
    print("✅ Use NLP results with SocialMapper")
    print("✅ Handle errors and refine queries")
    print("✅ Use advanced features and batch processing")
    print("✅ Implement integration patterns")
    
    print("\n🚀 Next Steps:")
    print("• Try the interactive demo: examples/nlp_demo.py")
    print("• Read the documentation: docs/features/natural-language-interface.md")
    print("• Experiment with your own queries!")
    
    print("\n💡 Remember: The more specific your queries, the better the results!")


if __name__ == "__main__":
    # Run the complete tutorial
    asyncio.run(run_complete_tutorial())