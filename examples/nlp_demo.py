"""Demo of Natural Language Processing capabilities in SocialMapper.

This example demonstrates how to use the NLQueryProcessor to convert
natural language queries into structured analysis configurations.
"""

import asyncio
import sys
from pathlib import Path

# Add socialmapper to path for demo
sys.path.insert(0, str(Path(__file__).parent.parent))

from socialmapper.nlp import NLQueryProcessor
from socialmapper.api import SocialMapperClient


async def demonstrate_nlp_capabilities():
    """Demonstrate various NLP processing capabilities."""
    
    print("🤖 SocialMapper Natural Language Processing Demo")
    print("=" * 50)
    
    processor = NLQueryProcessor()
    
    # Example queries to demonstrate different intents
    example_queries = [
        # Accessibility Analysis
        "Find hospitals within 20 minutes of Boston, MA by driving",
        
        # POI Discovery  
        "What restaurants are near Seattle within walking distance?",
        
        # Demographic Analysis
        "Show demographics around libraries in low-income areas of Chicago",
        
        # Equity Analysis
        "Compare grocery store access between high and low-income neighborhoods in Denver",
        
        # Location Optimization
        "Where should we place a new library for maximum coverage in Portland, OR?",
        
        # Complex multi-constraint query
        "Find grocery stores within 15 minutes by walking in San Francisco, CA for elderly residents",
    ]
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n🔍 Query {i}: \"{query}\"")
        print("-" * 60)
        
        # Process the natural language query
        result = await processor.process_natural_query(query)
        
        if result.is_ok():
            query_result = result.unwrap()
            
            # Show processing results
            print(f"📋 Intent: {query_result.intent.primary_intent.name}")
            print(f"📊 Confidence: {query_result.intent.confidence:.1%}")
            print(f"🏷️  Entities Found: {len(query_result.entities)}")
            
            # Show extracted entities
            for entity in query_result.entities:
                entity_info = f"   • {entity.entity_type.name}: '{entity.text}'"
                if hasattr(entity, 'poi_category') and entity.poi_category:
                    entity_info += f" → {entity.poi_category}"
                elif hasattr(entity, 'minutes'):
                    entity_info += f" → {entity.minutes} min"
                elif hasattr(entity, 'location_name'):
                    entity_info += f" → {entity.location_name}"
                elif hasattr(entity, 'mode'):
                    entity_info += f" → {entity.mode}"
                print(entity_info)
            
            # Show warnings and suggestions
            if query_result.warnings:
                print(f"⚠️  Warnings:")
                for warning in query_result.warnings:
                    print(f"   • {warning}")
            
            if query_result.suggestions:
                print(f"💡 Suggestions:")
                for suggestion in query_result.suggestions[:2]:  # Limit to 2 suggestions
                    print(f"   • {suggestion}")
                    
        else:
            error = result.unwrap_err()
            print(f"❌ Error: {error.message}")


async def interactive_nlp_demo():
    """Interactive demo allowing user to input queries."""
    
    print("\n" + "=" * 50)
    print("🎯 Interactive Natural Language Query Demo")
    print("=" * 50)
    print("Enter natural language queries to see how they're processed.")
    print("Examples:")
    print("  • 'Find hospitals within 30 minutes of my location'")
    print("  • 'What parks are near Chicago by walking?'") 
    print("  • 'Compare library access in rich vs poor areas'")
    print("Type 'quit' to exit.\n")
    
    processor = NLQueryProcessor()
    
    while True:
        try:
            query = input("🔍 Enter query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue
            
            print(f"\nProcessing: \"{query}\"")
            
            result = await processor.process_natural_query(query)
            
            if result.is_ok():
                query_result = result.unwrap()
                
                # Generate detailed explanation
                explanation = processor.explain_query_processing(query_result)
                print("\n" + explanation)
                
                # Ask if user wants to see the full configuration
                show_config = input("\nShow full configuration? (y/n): ").lower().startswith('y')
                if show_config:
                    print("\n📋 Generated Configuration:")
                    import json
                    print(json.dumps(query_result.config, indent=2, default=str))
                    
            else:
                error = result.unwrap_err()
                print(f"❌ Error processing query: {error.message}")
                
            print("\n" + "-" * 50)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\nThank you for trying the NLP demo! 👋")


async def integration_example():
    """Show integration with SocialMapper client."""
    
    print("\n" + "=" * 50)
    print("🔗 Integration with SocialMapper Client")
    print("=" * 50)
    
    processor = NLQueryProcessor()
    
    # Process natural language query
    query = "Find libraries within 15 minutes by walking in Boston, MA"
    print(f"Query: \"{query}\"")
    
    result = await processor.process_natural_query(query)
    
    if result.is_ok():
        query_result = result.unwrap()
        config = query_result.config
        
        print(f"✅ Query processed successfully!")
        print(f"Intent: {query_result.intent.primary_intent.name}")
        
        # Use the configuration with SocialMapper client
        print("\n🚀 Running analysis with generated configuration...")
        
        try:
            with SocialMapperClient() as client:
                # For demo purposes, we'll show how you would use the config
                # In practice, you'd run: analysis_result = client.run_analysis(config)
                print("📝 Configuration ready for analysis:")
                
                # Show key configuration parameters
                if 'geocode_area' in config:
                    print(f"   • Location: {config['geocode_area']}, {config.get('state', 'N/A')}")
                if 'poi_type' in config and 'poi_name' in config:
                    print(f"   • POI: {config['poi_type']}/{config['poi_name']}")
                if 'travel_time' in config:
                    print(f"   • Travel Time: {config['travel_time']} minutes")
                if 'travel_mode' in config:
                    print(f"   • Travel Mode: {config['travel_mode']}")
                
                print("\n💡 To run actual analysis, uncomment the analysis line in the code.")
                
        except Exception as e:
            print(f"Note: Client setup error (expected for demo): {e}")
    
    else:
        error = result.unwrap_err()
        print(f"❌ Query processing failed: {error.message}")


def show_supported_query_types():
    """Display supported query types and examples."""
    
    print("\n" + "=" * 50)
    print("📚 Supported Query Types and Examples")
    print("=" * 50)
    
    processor = NLQueryProcessor()
    examples = processor.get_example_queries()
    
    for category, queries in examples.items():
        print(f"\n🎯 {category}:")
        for query in queries:
            print(f"   • \"{query}\"")


async def main():
    """Main demo function."""
    
    print("Welcome to the SocialMapper Natural Language Processing Demo!")
    print("\nThis demo will show you how to:")
    print("1. Process natural language queries")
    print("2. Extract entities and classify intents")
    print("3. Generate analysis configurations")
    print("4. Use NLP with SocialMapper client")
    
    # Show supported query types
    show_supported_query_types()
    
    # Run automated examples
    await demonstrate_nlp_capabilities()
    
    # Show integration example
    await integration_example()
    
    # Ask if user wants interactive demo
    if input("\nWould you like to try the interactive demo? (y/n): ").lower().startswith('y'):
        await interactive_nlp_demo()
    
    print("\n🎉 Demo completed! The NLP system can help make SocialMapper more accessible")
    print("   to users who prefer natural language over technical configurations.")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())