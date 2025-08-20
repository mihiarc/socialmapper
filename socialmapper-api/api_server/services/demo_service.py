"""Service for managing and executing demo scenarios."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib

# from socialmapper import SocialMapperBuilder  # Not needed for demo submission
# from socialmapper.data import POICategory  # Not needed for demo submission

from ..services.cache_service import CacheService
from ..services.job_manager import JobManager
from ..services.enhanced_job_manager import JobPriority
from ..models.analysis import AnalysisRequest, AnalysisResponse

logger = logging.getLogger(__name__)


class DemoScenarioService:
    """Service for managing pre-configured demo scenarios."""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize the demo scenario service.
        
        Args:
            cache_service: Optional cache service for storing demo results
        """
        self.cache_service = cache_service
        self.scenarios = self._load_scenarios()
        self.job_manager = JobManager()
        
    def _load_scenarios(self) -> Dict[str, Dict]:
        """Load demo scenarios from configuration file."""
        scenarios_path = Path(__file__).parent.parent.parent / "demo_scenarios" / "scenarios.json"
        
        if not scenarios_path.exists():
            logger.warning(f"Demo scenarios file not found at {scenarios_path}")
            return {}
            
        try:
            with open(scenarios_path, 'r') as f:
                data = json.load(f)
                return {s['id']: s for s in data['scenarios']}
        except Exception as e:
            logger.error(f"Failed to load demo scenarios: {e}")
            return {}
    
    def list_scenarios(self) -> List[Dict]:
        """Get list of available demo scenarios.
        
        Returns:
            List of scenario metadata
        """
        return [
            {
                'id': s['id'],
                'name': s['name'],
                'description': s['description'],
                'icon': s['icon'],
                'category': s['category'],
                'city': s['location']['city'],
                'estimated_runtime': s['estimated_runtime_seconds']
            }
            for s in self.scenarios.values()
        ]
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get detailed information about a specific scenario.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            Scenario configuration or None if not found
        """
        return self.scenarios.get(scenario_id)
    
    async def run_scenario(self, scenario_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Execute a demo scenario.
        
        Args:
            scenario_id: The scenario to run
            use_cache: Whether to use cached results if available
            
        Returns:
            Analysis results
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        # Check cache first
        if use_cache and self.cache_service:
            cache_key = scenario['cache_key']
            cached_result = await self.cache_service.get_demo_data(cache_key)
            if cached_result:
                logger.info(f"Returning cached results for demo scenario: {scenario_id}")
                return cached_result
        
        # Build analysis configuration
        config = scenario['configuration']
        location = scenario['location']
        
        # Create analysis request
        analysis_request = AnalysisRequest(
            analysis_type=config['analysis_type'],
            location={
                'bbox': location['bbox'],
                'center': location['center']
            },
            poi_categories=config['poi_categories'],
            travel_mode=config['travel_mode'],
            travel_time_minutes=config['travel_time_minutes'],
            include_demographics=config['include_demographics'],
            demographic_variables=config.get('demographic_variables', [])
        )
        
        # Submit job with DEMO priority for faster processing
        job_id = await self.job_manager.submit_job(
            analysis_request.dict(),
            priority=JobPriority.DEMO,
            metadata={
                'scenario_id': scenario_id,
                'scenario_name': scenario['name'],
                'is_demo': True,
                'insights': scenario['insights']
            }
        )
        
        # Return the job ID immediately so the frontend can track progress
        return {
            'job_id': job_id,
            'scenario_metadata': {
                'id': scenario_id,
                'name': scenario['name'],
                'description': scenario['description'],
                'estimated_runtime_seconds': scenario['estimated_runtime_seconds']
            }
        }
    
    async def warm_cache(self):
        """Pre-generate and cache all demo scenarios.
        
        This should be run during off-peak hours to ensure demos are fast.
        """
        logger.info("Starting demo cache warming...")
        
        for scenario_id in self.scenarios:
            try:
                logger.info(f"Warming cache for scenario: {scenario_id}")
                # For cache warming, we just submit the job - we don't need to wait
                result = await self.run_scenario(scenario_id, use_cache=False)
                logger.info(f"Successfully submitted scenario for caching: {scenario_id}, job_id: {result['job_id']}")
            except Exception as e:
                logger.error(f"Failed to warm cache for {scenario_id}: {e}")
        
        logger.info("Demo cache warming complete")
    
    def get_scenario_config_for_builder(self, scenario_id: str) -> Dict:
        """Convert scenario configuration to SocialMapperBuilder format.
        
        Args:
            scenario_id: The scenario identifier
            
        Returns:
            Configuration dict for SocialMapperBuilder
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        config = scenario['configuration']
        location = scenario['location']
        
        # Map POI categories to SocialMapperBuilder format
        poi_categories = []
        for category in config['poi_categories']:
            # Convert string categories to POICategory enum values
            if hasattr(POICategory, category.upper()):
                poi_categories.append(getattr(POICategory, category.upper()))
        
        return {
            'location': f"{location['city']}",
            'bbox': location['bbox'],
            'poi_categories': poi_categories,
            'travel_mode': config['travel_mode'],
            'travel_time': config['travel_time_minutes'],
            'include_demographics': config['include_demographics'],
            'census_variables': config.get('demographic_variables', [])
        }
    
    def validate_scenario_data(self, scenario_id: str) -> Dict[str, Any]:
        """Validate that a scenario's configuration is valid.
        
        Args:
            scenario_id: The scenario to validate
            
        Returns:
            Validation results with any issues found
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {'valid': False, 'errors': ['Scenario not found']}
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['id', 'name', 'description', 'location', 'configuration']
        for field in required_fields:
            if field not in scenario:
                errors.append(f"Missing required field: {field}")
        
        # Validate location
        if 'location' in scenario:
            loc = scenario['location']
            if 'bbox' in loc:
                bbox = loc['bbox']
                if bbox['north'] <= bbox['south']:
                    errors.append("Invalid bbox: north must be greater than south")
                if bbox['east'] <= bbox['west']:
                    errors.append("Invalid bbox: east must be greater than west")
        
        # Validate configuration
        if 'configuration' in scenario:
            config = scenario['configuration']
            
            # Check travel time
            if config.get('travel_time_minutes', 0) <= 0:
                errors.append("Travel time must be positive")
            elif config.get('travel_time_minutes', 0) > 120:
                warnings.append("Travel time > 120 minutes may be slow")
            
            # Check POI categories
            if not config.get('poi_categories'):
                errors.append("At least one POI category required")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


# Singleton instance
_demo_service = None


def get_demo_service() -> DemoScenarioService:
    """Get or create the demo service singleton."""
    global _demo_service
    if _demo_service is None:
        from ..services.cache_service import get_cache_service
        _demo_service = DemoScenarioService(cache_service=get_cache_service())
    return _demo_service


import asyncio  # Add at the top with other imports