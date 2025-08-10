"""Feedback collection and analytics API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer

from ..models.feedback import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackSummary,
    UserAnalyticsEvent,
    FeatureRequestCreate,
    FeatureRequest,
    FeatureVoteRequest,
    FeatureVote,
    InterviewRequest,
    InterviewSession,
    AnalyticsSummary,
    FeedbackInsights,
    FeedbackType,
    FeedbackTouchpoint,
)
from ..services.feedback_service import (
    get_feedback_service,
    FeedbackService,
)

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

router = APIRouter()


def get_optional_token(token=Depends(security)) -> Optional[str]:
    """Get optional authentication token."""
    return token.credentials if token else None


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    token: Optional[str] = Depends(get_optional_token)
) -> FeedbackResponse:
    """
    Submit user feedback.
    
    Collects feedback from various touchpoints in the application.
    Supports anonymous feedback submission with optional user identification.
    """
    try:
        feedback_service = get_feedback_service()
        
        # Add request metadata
        feedback_data = feedback.model_dump()
        feedback_data['id'] = str(uuid4())
        feedback_data['created_at'] = datetime.utcnow()
        
        # Store feedback (in production, this would save to database)
        result = await feedback_service.store_feedback(feedback_data)
        
        logger.info(f"Feedback submitted: {feedback.type} from {feedback.touchpoint}")
        
        return FeedbackResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/feedback/summary", response_model=FeedbackSummary)
async def get_feedback_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    touchpoint: Optional[FeedbackTouchpoint] = Query(None, description="Filter by touchpoint"),
    token: Optional[str] = Depends(get_optional_token)
) -> FeedbackSummary:
    """
    Get feedback summary statistics.
    
    Provides aggregated feedback metrics for analytics dashboards.
    Includes ratings, response rates, and distribution by type/touchpoint.
    """
    try:
        feedback_service = get_feedback_service()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        summary = await feedback_service.get_feedback_summary(
            start_date=start_date,
            end_date=end_date,
            touchpoint=touchpoint
        )
        
        return FeedbackSummary(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback summary")


@router.post("/analytics/events")
async def track_analytics_event(
    event: UserAnalyticsEvent,
    token: Optional[str] = Depends(get_optional_token)
) -> Dict[str, str]:
    """
    Track user analytics events.
    
    Records user behavior events for journey analysis and improvement insights.
    Supports privacy-compliant event tracking with consent management.
    """
    try:
        feedback_service = get_feedback_service()
        
        # Add timestamp if not provided
        if not event.timestamp:
            event.timestamp = datetime.utcnow()
        
        # Store analytics event
        await feedback_service.store_analytics_event(event.model_dump())
        
        logger.info(f"Analytics event tracked: {event.event_name}")
        
        return {"status": "success", "message": "Event tracked successfully"}
        
    except Exception as e:
        logger.error(f"Failed to track analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track analytics event")


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    token: Optional[str] = Depends(get_optional_token)
) -> AnalyticsSummary:
    """
    Get user analytics summary.
    
    Provides aggregated user behavior metrics including session data,
    conversion rates, and user journey funnel analysis.
    """
    try:
        feedback_service = get_feedback_service()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        summary = await feedback_service.get_analytics_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return AnalyticsSummary(**summary)
        
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics summary")


@router.post("/features", response_model=FeatureRequest)
async def create_feature_request(
    feature: FeatureRequestCreate,
    token: Optional[str] = Depends(get_optional_token)
) -> FeatureRequest:
    """
    Create a new feature request.
    
    Allows users to submit feature requests that are tracked and prioritized.
    Integrates with GitHub Issues for public roadmap management.
    """
    try:
        feedback_service = get_feedback_service()
        
        # Create feature request
        feature_data = feature.model_dump()
        feature_data['id'] = str(uuid4())
        feature_data['created_at'] = datetime.utcnow()
        feature_data['updated_at'] = datetime.utcnow()
        
        result = await feedback_service.create_feature_request(feature_data)
        
        logger.info(f"Feature request created: {feature.title}")
        
        return FeatureRequest(**result)
        
    except Exception as e:
        logger.error(f"Failed to create feature request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create feature request")


@router.get("/features", response_model=List[FeatureRequest])
async def list_feature_requests(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    token: Optional[str] = Depends(get_optional_token)
) -> List[FeatureRequest]:
    """
    List feature requests with filtering and pagination.
    
    Returns a list of feature requests sorted by votes and creation date.
    Supports filtering by category and status.
    """
    try:
        feedback_service = get_feedback_service()
        
        features = await feedback_service.list_feature_requests(
            limit=limit,
            offset=offset,
            category=category,
            status=status
        )
        
        return [FeatureRequest(**feature) for feature in features]
        
    except Exception as e:
        logger.error(f"Failed to list feature requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list feature requests")


@router.post("/features/vote", response_model=FeatureVote)
async def vote_on_feature(
    vote: FeatureVoteRequest,
    token: Optional[str] = Depends(get_optional_token)
) -> FeatureVote:
    """
    Vote on a feature request.
    
    Allows users to upvote or downvote feature requests for prioritization.
    Supports anonymous voting with duplicate prevention.
    """
    try:
        feedback_service = get_feedback_service()
        
        # Create vote record
        vote_data = vote.model_dump()
        vote_data['created_at'] = datetime.utcnow()
        
        result = await feedback_service.record_feature_vote(vote_data)
        
        logger.info(f"Feature vote recorded: {vote.vote_type} for {vote.feature_id}")
        
        return FeatureVote(**result)
        
    except Exception as e:
        logger.error(f"Failed to record feature vote: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record vote")


@router.post("/interviews", response_model=InterviewSession)
async def request_interview(
    interview: InterviewRequest,
    token: Optional[str] = Depends(get_optional_token)
) -> InterviewSession:
    """
    Request a user interview session.
    
    Allows users to schedule interviews for UX research and feedback collection.
    Integrates with calendar scheduling systems.
    """
    try:
        feedback_service = get_feedback_service()
        
        # Create interview request
        interview_data = interview.model_dump()
        interview_data['id'] = str(uuid4())
        interview_data['participant_id'] = str(uuid4())  # Anonymous participant ID
        interview_data['created_at'] = datetime.utcnow()
        
        result = await feedback_service.schedule_interview(interview_data)
        
        logger.info(f"Interview requested: {interview.interview_type} by {interview.user_type}")
        
        return InterviewSession(**result)
        
    except Exception as e:
        logger.error(f"Failed to request interview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to request interview")


@router.get("/interviews", response_model=List[InterviewSession])
async def list_interviews(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    status: Optional[str] = Query(None, description="Filter by status"),
    interview_type: Optional[str] = Query(None, description="Filter by interview type"),
    token: Optional[str] = Depends(get_optional_token)
) -> List[InterviewSession]:
    """
    List scheduled interviews.
    
    Returns a list of interview sessions with filtering options.
    Used for research team dashboard and scheduling management.
    """
    try:
        feedback_service = get_feedback_service()
        
        interviews = await feedback_service.list_interviews(
            limit=limit,
            status=status,
            interview_type=interview_type
        )
        
        return [InterviewSession(**interview) for interview in interviews]
        
    except Exception as e:
        logger.error(f"Failed to list interviews: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list interviews")


@router.get("/insights", response_model=FeedbackInsights)
async def get_feedback_insights(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    token: Optional[str] = Depends(get_optional_token)
) -> FeedbackInsights:
    """
    Get AI-generated insights from feedback data.
    
    Analyzes feedback content to extract themes, sentiment, and improvement suggestions.
    Provides actionable insights for product development.
    """
    try:
        feedback_service = get_feedback_service()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        insights = await feedback_service.generate_feedback_insights(
            start_date=start_date,
            end_date=end_date
        )
        
        return FeedbackInsights(**insights)
        
    except Exception as e:
        logger.error(f"Failed to generate feedback insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")