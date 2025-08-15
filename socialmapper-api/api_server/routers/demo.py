"""FastAPI router for demo scenarios."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..services.demo_service import get_demo_service
from ..services.cache_service import get_cache_service

router = APIRouter()


@router.get("/demo/scenarios", response_model=List[Dict])
async def list_demo_scenarios():
    """Get list of available demo scenarios.
    
    Returns:
        List of demo scenario metadata
    """
    demo_service = get_demo_service()
    return demo_service.list_scenarios()


@router.get("/demo/scenarios/{scenario_id}")
async def get_demo_scenario(scenario_id: str):
    """Get detailed information about a specific demo scenario.
    
    Args:
        scenario_id: The scenario identifier
        
    Returns:
        Scenario configuration and metadata
    """
    demo_service = get_demo_service()
    scenario = demo_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    
    return scenario


@router.post("/demo/scenarios/{scenario_id}/run")
async def run_demo_scenario(
    scenario_id: str,
    use_cache: bool = True,
    background_tasks: BackgroundTasks = None
):
    """Execute a demo scenario.
    
    Args:
        scenario_id: The scenario to run
        use_cache: Whether to use cached results if available
        background_tasks: FastAPI background tasks
        
    Returns:
        Analysis results with scenario insights
    """
    demo_service = get_demo_service()
    
    # Validate scenario exists
    scenario = demo_service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    
    try:
        # Run the scenario
        result = await demo_service.run_scenario(scenario_id, use_cache=use_cache)
        
        # Track usage analytics in background
        if background_tasks:
            background_tasks.add_task(
                track_demo_usage,
                scenario_id=scenario_id,
                cached=result.get('from_cache', False)
            )
        
        return result
        
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run scenario: {str(e)}")


@router.post("/demo/cache/warm")
async def warm_demo_cache(background_tasks: BackgroundTasks):
    """Pre-generate and cache all demo scenarios.
    
    This endpoint triggers cache warming in the background.
    Should be called during off-peak hours.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Status message
    """
    demo_service = get_demo_service()
    
    # Start cache warming in background
    background_tasks.add_task(demo_service.warm_cache)
    
    return {
        "status": "Cache warming started",
        "message": "Demo scenarios are being pre-generated in the background"
    }


@router.get("/demo/cache/status")
async def get_cache_status():
    """Get status of demo scenario cache.
    
    Returns:
        Cache statistics for each scenario
    """
    demo_service = get_demo_service()
    cache_service = get_cache_service()
    
    if not cache_service:
        return {"status": "Cache not configured"}
    
    cache_status = {}
    
    for scenario_id, scenario in demo_service.scenarios.items():
        cache_key = scenario['cache_key']
        cached_data = await cache_service.get_demo_data(cache_key)
        
        cache_status[scenario_id] = {
            "cached": cached_data is not None,
            "cache_key": cache_key,
            "scenario_name": scenario['name']
        }
        
        if cached_data:
            # Add cache metadata if available
            if isinstance(cached_data, dict):
                cache_status[scenario_id]["cached_at"] = cached_data.get('cached_at')
                cache_status[scenario_id]["cache_expires"] = cached_data.get('expires_at')
    
    return {
        "total_scenarios": len(demo_service.scenarios),
        "cached_scenarios": sum(1 for s in cache_status.values() if s['cached']),
        "scenarios": cache_status
    }


@router.post("/demo/scenarios/{scenario_id}/validate")
async def validate_demo_scenario(scenario_id: str):
    """Validate a demo scenario configuration.
    
    Args:
        scenario_id: The scenario to validate
        
    Returns:
        Validation results with any issues found
    """
    demo_service = get_demo_service()
    
    if scenario_id not in demo_service.scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    
    validation_result = demo_service.validate_scenario_data(scenario_id)
    
    return validation_result


@router.get("/demo/insights/{scenario_id}")
async def get_scenario_insights(scenario_id: str):
    """Get pre-computed insights for a demo scenario.
    
    These are the expected results and key findings that should
    be highlighted when the scenario is run.
    
    Args:
        scenario_id: The scenario identifier
        
    Returns:
        Scenario insights and key metrics
    """
    demo_service = get_demo_service()
    scenario = demo_service.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    
    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario['name'],
        "insights": scenario.get('insights', {}),
        "location": scenario['location']['city'],
        "analysis_focus": scenario['category']
    }


async def track_demo_usage(scenario_id: str, cached: bool):
    """Track demo scenario usage for analytics.
    
    Args:
        scenario_id: The scenario that was run
        cached: Whether cached results were used
    """
    # This would integrate with your analytics service
    # For now, just log the usage
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Demo scenario used: {scenario_id} (cached: {cached})")
    
    # You could also:
    # - Store in database for analytics
    # - Send to monitoring service
    # - Update usage counters in Redis