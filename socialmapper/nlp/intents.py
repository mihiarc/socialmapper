"""Intent classification for natural language queries.

This module classifies user intents and determines what type of spatial
analysis should be performed based on natural language input.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set
import re


class QueryIntent(Enum):
    """Types of analysis intents that can be inferred from queries."""
    
    ACCESSIBILITY_ANALYSIS = auto()      # "Find hospitals within X minutes"
    POI_DISCOVERY = auto()              # "What's near location X?"
    DEMOGRAPHIC_ANALYSIS = auto()       # "Show demographics around POIs"
    EQUITY_ANALYSIS = auto()           # "Compare access across demographics"
    COVERAGE_ANALYSIS = auto()         # "How much area is covered?"
    TRAVEL_TIME_ANALYSIS = auto()      # "How long to reach POIs?"
    LOCATION_OPTIMIZATION = auto()     # "Where should we place a new POI?"
    COMPARISON_ANALYSIS = auto()       # "Compare access in different areas"
    TREND_ANALYSIS = auto()           # "How has access changed over time?"
    WHAT_IF_ANALYSIS = auto()         # "What if we add a new POI?"


@dataclass
class IntentClassification:
    """Result of intent classification."""
    
    primary_intent: QueryIntent
    secondary_intents: List[QueryIntent]
    confidence: float
    reasoning: str
    suggested_analysis_type: str
    

class IntentClassifier:
    """Classifies the intent of natural language queries."""
    
    def __init__(self):
        self._setup_intent_patterns()
    
    def _setup_intent_patterns(self):
        """Setup patterns for intent classification."""
        
        # Intent keywords and phrases mapped to intents
        self.intent_patterns = {
            QueryIntent.ACCESSIBILITY_ANALYSIS: {
                'keywords': [
                    'find', 'locate', 'access', 'reach', 'within', 'near',
                    'accessible', 'available', 'close to', 'nearby'
                ],
                'phrases': [
                    r'\bfind\s+\w+\s+within\b',
                    r'\b\w+\s+within\s+\d+\s+minutes?\b',
                    r'\bhow many\s+\w+\s+are\s+accessible\b',
                    r'\bwhat\s+\w+\s+can\s+I\s+reach\b'
                ],
                'weight': 1.0
            },
            
            QueryIntent.POI_DISCOVERY: {
                'keywords': [
                    'what', 'discover', 'explore', 'around', 'nearby',
                    'available', 'options', 'choices'
                ],
                'phrases': [
                    r'\bwhat.*(?:is|are).*(?:around|near|in)\b',
                    r'\bshow me.*(?:around|near)\b',
                    r'\bdiscover.*(?:in|around|near)\b',
                    r'\bwhat.*options.*(?:in|around|near)\b'
                ],
                'weight': 1.0
            },
            
            QueryIntent.DEMOGRAPHIC_ANALYSIS: {
                'keywords': [
                    'demographics', 'population', 'income', 'age', 'race',
                    'ethnicity', 'education', 'poverty', 'wealth', 'census'
                ],
                'phrases': [
                    r'\bdemographics?\s+(?:of|in|around|near)\b',
                    r'\bpopulation\s+(?:around|near|served by)\b',
                    r'\bincome\s+(?:levels?|data|around|near)\b',
                    r'\bcensus\s+(?:data|information)\b'
                ],
                'weight': 1.2
            },
            
            QueryIntent.EQUITY_ANALYSIS: {
                'keywords': [
                    'equity', 'fair', 'equal', 'disparit', 'gap', 'inequality',
                    'compare', 'difference', 'bias', 'underserved', 'disadvantaged'
                ],
                'phrases': [
                    r'\bequity\s+(?:analysis|assessment)\b',
                    r'\bcompare\s+access\s+(?:across|between)\b',
                    r'\b(?:access|service)\s+(?:gaps?|disparities)\b',
                    r'\b(?:fair|equal)\s+access\b',
                    r'\bunderserved\s+(?:areas?|communities?|populations?)\b'
                ],
                'weight': 1.3
            },
            
            QueryIntent.COVERAGE_ANALYSIS: {
                'keywords': [
                    'coverage', 'area', 'served', 'reach', 'extent',
                    'how much', 'total area', 'square miles', 'percent'
                ],
                'phrases': [
                    r'\bhow much\s+area\b',
                    r'\btotal\s+(?:area|coverage)\b',
                    r'\bpercent(?:age)?\s+(?:of|covered|served)\b',
                    r'\barea\s+(?:covered|served|within)\b',
                    r'\bcoverage\s+(?:area|analysis)\b'
                ],
                'weight': 1.1
            },
            
            QueryIntent.TRAVEL_TIME_ANALYSIS: {
                'keywords': [
                    'time', 'minutes', 'hours', 'travel', 'commute',
                    'how long', 'duration', 'journey'
                ],
                'phrases': [
                    r'\bhow long\s+(?:to|does it take)\b',
                    r'\btravel\s+time\s+(?:to|from|between)\b',
                    r'\bcommute\s+time\b',
                    r'\b\d+\s+minutes?\s+(?:to|from|away)\b',
                    r'\bjourney\s+time\b'
                ],
                'weight': 1.0
            },
            
            QueryIntent.LOCATION_OPTIMIZATION: {
                'keywords': [
                    'where', 'best', 'optimal', 'place', 'locate', 'site',
                    'should', 'recommend', 'suggest', 'new'
                ],
                'phrases': [
                    r'\bwhere\s+(?:should|to)\s+(?:place|locate|build)\b',
                    r'\bbest\s+(?:location|place|site)\s+for\b',
                    r'\boptimal\s+(?:location|placement|site)\b',
                    r'\brecommend.*(?:location|site|place)\b',
                    r'\bwhere.*new.*(?:hospital|school|library)\b'
                ],
                'weight': 1.4
            },
            
            QueryIntent.COMPARISON_ANALYSIS: {
                'keywords': [
                    'compare', 'versus', 'vs', 'between', 'difference',
                    'contrast', 'against', 'relative'
                ],
                'phrases': [
                    r'\bcompare\s+(?:access|availability)\s+(?:in|between)\b',
                    r'\b\w+\s+(?:versus|vs\.?)\s+\w+\b',
                    r'\bdifference\s+(?:in|between)\s+access\b',
                    r'\bhow does.*compare\b',
                    r'\bcontrast.*(?:access|availability)\b'
                ],
                'weight': 1.2
            },
            
            QueryIntent.TREND_ANALYSIS: {
                'keywords': [
                    'trend', 'change', 'over time', 'historical', 'was',
                    'has changed', 'evolution', 'development', 'growth'
                ],
                'phrases': [
                    r'\b(?:has|have)\s+(?:changed|improved|declined)\b',
                    r'\bover\s+(?:time|years?|decades?)\b',
                    r'\btrend\s+(?:in|of|over)\b',
                    r'\bhistorical\s+(?:data|analysis|access)\b',
                    r'\bevolution\s+of\s+access\b'
                ],
                'weight': 1.3
            },
            
            QueryIntent.WHAT_IF_ANALYSIS: {
                'keywords': [
                    'what if', 'if we', 'scenario', 'hypothetical',
                    'suppose', 'assume', 'impact of', 'effect of'
                ],
                'phrases': [
                    r'\bwhat if\s+(?:we|there|I)\b',
                    r'\bif\s+(?:we|I|there)\s+(?:add|build|remove|close)\b',
                    r'\bscenario\s+(?:where|analysis)\b',
                    r'\bimpact\s+of\s+(?:adding|building|closing)\b',
                    r'\bsuppose\s+(?:we|there)\b'
                ],
                'weight': 1.4
            }
        }
        
        # Analysis type mapping
        self.analysis_type_mapping = {
            QueryIntent.ACCESSIBILITY_ANALYSIS: "standard_analysis",
            QueryIntent.POI_DISCOVERY: "poi_discovery",
            QueryIntent.DEMOGRAPHIC_ANALYSIS: "demographic_analysis",
            QueryIntent.EQUITY_ANALYSIS: "equity_analysis", 
            QueryIntent.COVERAGE_ANALYSIS: "coverage_analysis",
            QueryIntent.TRAVEL_TIME_ANALYSIS: "travel_time_analysis",
            QueryIntent.LOCATION_OPTIMIZATION: "optimization_analysis",
            QueryIntent.COMPARISON_ANALYSIS: "comparison_analysis",
            QueryIntent.TREND_ANALYSIS: "temporal_analysis",
            QueryIntent.WHAT_IF_ANALYSIS: "scenario_analysis"
        }
    
    def classify_intent(self, query: str) -> IntentClassification:
        """Classify the intent of a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            IntentClassification with primary and secondary intents
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        reasoning_parts = []
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            matches = []
            
            # Check keyword matches
            keyword_matches = 0
            for keyword in patterns['keywords']:
                if keyword.lower() in query_lower:
                    keyword_matches += 1
                    matches.append(f"keyword '{keyword}'")
            
            # Keyword score (normalized by number of keywords)
            if keyword_matches > 0:
                keyword_score = (keyword_matches / len(patterns['keywords'])) * 0.6
                score += keyword_score
            
            # Check phrase pattern matches
            phrase_matches = 0
            for phrase_pattern in patterns['phrases']:
                if re.search(phrase_pattern, query_lower):
                    phrase_matches += 1
                    matches.append(f"pattern '{phrase_pattern}'")
            
            # Phrase score (higher weight for phrase matches)
            if phrase_matches > 0:
                phrase_score = min(phrase_matches * 0.8, 1.0)
                score += phrase_score
            
            # Apply intent-specific weight
            score *= patterns['weight']
            
            if score > 0:
                intent_scores[intent] = score
                if matches:
                    reasoning_parts.append(f"{intent.name}: {', '.join(matches[:2])}")
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_intents:
            # Default fallback
            primary_intent = QueryIntent.ACCESSIBILITY_ANALYSIS
            confidence = 0.3
            reasoning = "No clear intent patterns found, defaulting to accessibility analysis"
        else:
            primary_intent = sorted_intents[0][0]
            confidence = min(sorted_intents[0][1], 1.0)
            reasoning = "; ".join(reasoning_parts[:3])
        
        # Secondary intents (scores within 80% of primary)
        secondary_intents = []
        if sorted_intents and len(sorted_intents) > 1:
            primary_score = sorted_intents[0][1]
            for intent, score in sorted_intents[1:]:
                if score >= primary_score * 0.8:
                    secondary_intents.append(intent)
        
        # Get suggested analysis type
        suggested_analysis_type = self.analysis_type_mapping.get(
            primary_intent, "standard_analysis"
        )
        
        return IntentClassification(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=confidence,
            reasoning=reasoning,
            suggested_analysis_type=suggested_analysis_type
        )
    
    def suggest_enhancements(self, classification: IntentClassification) -> List[str]:
        """Suggest query enhancements based on classified intent.
        
        Args:
            classification: Result from classify_intent()
            
        Returns:
            List of enhancement suggestions
        """
        suggestions = []
        
        if classification.primary_intent == QueryIntent.ACCESSIBILITY_ANALYSIS:
            suggestions.extend([
                "Consider specifying travel mode (walk, drive, bike)",
                "Add demographic constraints for equity analysis",
                "Specify time constraints if not already included"
            ])
        
        elif classification.primary_intent == QueryIntent.POI_DISCOVERY:
            suggestions.extend([
                "Add specific POI categories you're interested in", 
                "Consider adding travel time constraints",
                "Specify whether you want counts or detailed listings"
            ])
        
        elif classification.primary_intent == QueryIntent.DEMOGRAPHIC_ANALYSIS:
            suggestions.extend([
                "Specify which demographic variables to analyze",
                "Consider geographic scope (block groups vs zip codes)",
                "Add comparison groups or thresholds"
            ])
            
        elif classification.primary_intent == QueryIntent.EQUITY_ANALYSIS:
            suggestions.extend([
                "Specify demographic groups for comparison",
                "Add specific equity metrics of interest",
                "Consider multiple POI types for comprehensive analysis"
            ])
            
        elif classification.primary_intent == QueryIntent.LOCATION_OPTIMIZATION:
            suggestions.extend([
                "Specify constraints for optimization (budget, zoning, etc.)",
                "Add target demographic or coverage goals",
                "Consider multiple scenarios or alternatives"
            ])
        
        # Add general suggestions based on confidence
        if classification.confidence < 0.7:
            suggestions.append("Consider rephrasing query for better clarity")
            
        return suggestions[:3]  # Limit to top 3 suggestions