"""Feedback system models for user feedback collection and analytics."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseResponse


class FeedbackType(str, Enum):
    """Types of feedback that can be collected."""
    RATING = "rating"
    USABILITY = "usability"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"


class FeedbackTouchpoint(str, Enum):
    """Touchpoints where feedback is collected."""
    POST_ANALYSIS = "post_analysis"
    CONFIGURATION_WIZARD = "configuration_wizard"
    RESULTS_DASHBOARD = "results_dashboard"
    ERROR_STATE = "error_state"
    EXPORT_DOWNLOAD = "export_download"
    GENERAL_USAGE = "general_usage"


class FeedbackStatus(str, Enum):
    """Status of feedback processing."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class FeedbackContext(BaseModel):
    """Context information for feedback submission."""
    model_config = ConfigDict(extra="allow")
    
    job_id: Optional[str] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None
    session_duration: Optional[int] = None
    error_occurred: Optional[bool] = None
    feature_used: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    type: FeedbackType
    touchpoint: FeedbackTouchpoint
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5 stars")
    comment: Optional[str] = Field(None, max_length=2000)
    context: Optional[FeedbackContext] = None
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class FeedbackResponse(BaseResponse):
    """Response model for feedback submission."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: FeedbackType
    touchpoint: FeedbackTouchpoint
    rating: Optional[int] = None
    comment: Optional[str] = None
    context: Optional[FeedbackContext] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackSummary(BaseResponse):
    """Summary statistics for feedback collection."""
    total_feedback: int
    average_rating: Optional[float] = None
    feedback_by_type: Dict[FeedbackType, int]
    feedback_by_touchpoint: Dict[FeedbackTouchpoint, int]
    recent_feedback_count: int
    response_rate: Optional[float] = None


# Analytics Models
class UserAnalyticsEvent(BaseModel):
    """Model for user analytics events."""
    event_name: str
    event_category: str = Field(..., pattern="^(navigation|interaction|conversion|error)$")
    properties: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class UserJourneyStep(BaseModel):
    """Model for user journey tracking."""
    step_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None
    completed: bool = True
    error: Optional[str] = None


class UserSession(BaseModel):
    """Model for user session tracking."""
    session_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    page_views: int = 0
    interactions: int = 0
    conversion_events: List[str] = Field(default_factory=list)
    journey_steps: List[UserJourneyStep] = Field(default_factory=list)


# Feature Request Models
class FeaturePriority(str, Enum):
    """Priority levels for feature requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FeatureStatus(str, Enum):
    """Status of feature requests."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"
    COMPLETED = "completed"
    REJECTED = "rejected"


class FeatureRequestCreate(BaseModel):
    """Request model for creating feature requests."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(..., min_length=2, max_length=50)
    priority: FeaturePriority = FeaturePriority.MEDIUM


class FeatureRequest(BaseResponse):
    """Feature request model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    category: str
    priority: FeaturePriority
    status: FeatureStatus = FeatureStatus.SUBMITTED
    votes: int = 0
    github_issue_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureVoteRequest(BaseModel):
    """Request model for voting on features."""
    feature_id: str
    vote_type: str = Field(..., pattern="^(upvote|downvote)$")


class FeatureVote(BaseResponse):
    """Feature vote model."""
    feature_id: str
    user_id: Optional[str] = None
    vote_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# User Interview Models
class UserType(str, Enum):
    """Types of users for interview scheduling."""
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"


class InterviewType(str, Enum):
    """Types of interviews."""
    USABILITY = "usability"
    FEATURE_DISCUSSION = "feature_discussion"
    WORKFLOW_ANALYSIS = "workflow_analysis"
    GENERAL_FEEDBACK = "general_feedback"


class InterviewStatus(str, Enum):
    """Status of interview sessions."""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class InterviewRequest(BaseModel):
    """Request model for scheduling interviews."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    user_type: UserType
    research_focus: Optional[str] = Field(None, max_length=500)
    preferred_times: List[str] = Field(..., min_items=1, max_items=5)
    timezone: str
    interview_type: InterviewType


class InterviewSession(BaseResponse):
    """Interview session model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    participant_id: str
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=30, le=120)
    interview_type: InterviewType
    status: InterviewStatus = InterviewStatus.SCHEDULED
    recording_url: Optional[str] = None
    notes: Optional[str] = None
    insights: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Analytics Dashboard Models
class AnalyticsSummary(BaseResponse):
    """Summary of analytics data for dashboards."""
    total_sessions: int
    total_page_views: int
    total_conversions: int
    average_session_duration_ms: Optional[int] = None
    bounce_rate: Optional[float] = None
    conversion_rate: Optional[float] = None
    top_pages: List[Dict[str, Any]]
    user_journey_funnel: List[Dict[str, Any]]


class FeedbackInsights(BaseResponse):
    """Insights generated from feedback analysis."""
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    common_themes: List[str]
    improvement_suggestions: List[str]
    satisfaction_trend: List[Dict[str, Any]]
    feature_requests_summary: Dict[str, int]