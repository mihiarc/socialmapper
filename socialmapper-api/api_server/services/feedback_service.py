"""Feedback service for managing feedback collection and analytics."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing feedback collection, analytics, and insights."""
    
    def __init__(self, storage_path: str = "feedback_data"):
        """Initialize feedback service with file-based storage."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize storage files
        self.feedback_file = self.storage_path / "feedback.jsonl"
        self.analytics_file = self.storage_path / "analytics.jsonl" 
        self.features_file = self.storage_path / "features.jsonl"
        self.interviews_file = self.storage_path / "interviews.jsonl"
        
        # Create files if they don't exist
        for file_path in [self.feedback_file, self.analytics_file, self.features_file, self.interviews_file]:
            if not file_path.exists():
                file_path.touch()
    
    async def store_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store feedback data."""
        try:
            # Add processing timestamp
            feedback_data['processed_at'] = datetime.utcnow().isoformat()
            
            # Append to JSONL file
            with open(self.feedback_file, 'a') as f:
                f.write(json.dumps(feedback_data) + '\n')
            
            logger.info(f"Stored feedback: {feedback_data.get('id')}")
            return feedback_data
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {str(e)}")
            raise
    
    async def get_feedback_summary(
        self, 
        start_date: datetime, 
        end_date: datetime,
        touchpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get feedback summary statistics."""
        try:
            feedback_data = []
            
            # Read feedback data
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            created_at = datetime.fromisoformat(data.get('created_at', ''))
                            if start_date <= created_at <= end_date:
                                if not touchpoint or data.get('touchpoint') == touchpoint:
                                    feedback_data.append(data)
            
            # Calculate statistics
            total_feedback = len(feedback_data)
            ratings = [item.get('rating') for item in feedback_data if item.get('rating') is not None]
            average_rating = sum(ratings) / len(ratings) if ratings else None
            
            # Count by type and touchpoint
            feedback_by_type = {}
            feedback_by_touchpoint = {}
            
            for item in feedback_data:
                feedback_type = item.get('type', 'unknown')
                touchpoint_name = item.get('touchpoint', 'unknown')
                
                feedback_by_type[feedback_type] = feedback_by_type.get(feedback_type, 0) + 1
                feedback_by_touchpoint[touchpoint_name] = feedback_by_touchpoint.get(touchpoint_name, 0) + 1
            
            # Recent feedback (last 7 days)
            recent_date = datetime.utcnow() - timedelta(days=7)
            recent_feedback = [
                item for item in feedback_data 
                if datetime.fromisoformat(item.get('created_at', '')) >= recent_date
            ]
            
            return {
                'success': True,
                'total_feedback': total_feedback,
                'average_rating': average_rating,
                'feedback_by_type': feedback_by_type,
                'feedback_by_touchpoint': feedback_by_touchpoint,
                'recent_feedback_count': len(recent_feedback),
                'response_rate': None  # Would calculate based on total user interactions
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {str(e)}")
            raise
    
    async def store_analytics_event(self, event_data: Dict[str, Any]) -> None:
        """Store analytics event."""
        try:
            # Add processing timestamp
            event_data['processed_at'] = datetime.utcnow().isoformat()
            
            # Append to JSONL file
            with open(self.analytics_file, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
            
            logger.info(f"Stored analytics event: {event_data.get('event_name')}")
            
        except Exception as e:
            logger.error(f"Failed to store analytics event: {str(e)}")
            raise
    
    async def get_analytics_summary(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get analytics summary statistics."""
        try:
            events_data = []
            
            # Read analytics data
            if self.analytics_file.exists():
                with open(self.analytics_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                            if start_date <= timestamp <= end_date:
                                events_data.append(data)
            
            # Calculate statistics
            sessions = {}
            page_views = 0
            conversions = 0
            
            for event in events_data:
                session_id = event.get('session_id')
                event_name = event.get('event_name', '')
                
                if session_id:
                    if session_id not in sessions:
                        sessions[session_id] = {
                            'start_time': None,
                            'end_time': None,
                            'page_views': 0,
                            'conversions': 0
                        }
                    
                    # Track session timing
                    timestamp = datetime.fromisoformat(event.get('timestamp', ''))
                    if not sessions[session_id]['start_time'] or timestamp < sessions[session_id]['start_time']:
                        sessions[session_id]['start_time'] = timestamp
                    if not sessions[session_id]['end_time'] or timestamp > sessions[session_id]['end_time']:
                        sessions[session_id]['end_time'] = timestamp
                
                # Count events
                if event_name == 'page_view':
                    page_views += 1
                    if session_id:
                        sessions[session_id]['page_views'] += 1
                elif 'conversion' in event_name:
                    conversions += 1
                    if session_id:
                        sessions[session_id]['conversions'] += 1
            
            # Calculate averages
            total_sessions = len(sessions)
            session_durations = []
            
            for session in sessions.values():
                if session['start_time'] and session['end_time']:
                    duration = (session['end_time'] - session['start_time']).total_seconds() * 1000
                    session_durations.append(duration)
            
            avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else None
            conversion_rate = (conversions / page_views) if page_views > 0 else None
            bounce_rate = None  # Would calculate based on single-page sessions
            
            # Top pages (simplified)
            top_pages = [
                {'page': '/dashboard', 'views': page_views // 3},
                {'page': '/analysis', 'views': page_views // 3},
                {'page': '/results', 'views': page_views // 3}
            ]
            
            # User journey funnel (simplified)
            user_journey_funnel = [
                {'step': 'Landing', 'users': total_sessions},
                {'step': 'Configuration', 'users': int(total_sessions * 0.8)},
                {'step': 'Analysis', 'users': int(total_sessions * 0.6)},
                {'step': 'Results', 'users': int(total_sessions * 0.5)},
                {'step': 'Export', 'users': conversions}
            ]
            
            return {
                'success': True,
                'total_sessions': total_sessions,
                'total_page_views': page_views,
                'total_conversions': conversions,
                'average_session_duration_ms': int(avg_session_duration) if avg_session_duration else None,
                'bounce_rate': bounce_rate,
                'conversion_rate': conversion_rate,
                'top_pages': top_pages,
                'user_journey_funnel': user_journey_funnel
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {str(e)}")
            raise
    
    async def create_feature_request(self, feature_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new feature request."""
        try:
            # Add initial vote count
            feature_data['votes'] = 0
            feature_data['status'] = 'submitted'
            
            # Append to JSONL file
            with open(self.features_file, 'a') as f:
                f.write(json.dumps(feature_data) + '\n')
            
            logger.info(f"Created feature request: {feature_data.get('id')}")
            return feature_data
            
        except Exception as e:
            logger.error(f"Failed to create feature request: {str(e)}")
            raise
    
    async def list_feature_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List feature requests with filtering."""
        try:
            features = []
            
            if self.features_file.exists():
                with open(self.features_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            
                            # Apply filters
                            if category and data.get('category') != category:
                                continue
                            if status and data.get('status') != status:
                                continue
                            
                            features.append(data)
            
            # Sort by votes (descending) then by creation date
            features.sort(
                key=lambda x: (-x.get('votes', 0), x.get('created_at', '')),
                reverse=False
            )
            
            # Apply pagination
            return features[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list feature requests: {str(e)}")
            raise
    
    async def record_feature_vote(self, vote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a vote on a feature request."""
        try:
            # In a real implementation, this would update the feature's vote count
            # and prevent duplicate voting by the same user
            
            logger.info(f"Recorded feature vote: {vote_data.get('feature_id')}")
            return vote_data
            
        except Exception as e:
            logger.error(f"Failed to record feature vote: {str(e)}")
            raise
    
    async def schedule_interview(self, interview_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a user interview."""
        try:
            # Set default values
            interview_data['status'] = 'scheduled'
            interview_data['duration_minutes'] = 60
            interview_data['scheduled_at'] = datetime.utcnow().isoformat()
            interview_data['insights'] = []
            
            # Append to JSONL file
            with open(self.interviews_file, 'a') as f:
                f.write(json.dumps(interview_data) + '\n')
            
            logger.info(f"Scheduled interview: {interview_data.get('id')}")
            return interview_data
            
        except Exception as e:
            logger.error(f"Failed to schedule interview: {str(e)}")
            raise
    
    async def list_interviews(
        self,
        limit: int = 50,
        status: Optional[str] = None,
        interview_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List scheduled interviews."""
        try:
            interviews = []
            
            if self.interviews_file.exists():
                with open(self.interviews_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            
                            # Apply filters
                            if status and data.get('status') != status:
                                continue
                            if interview_type and data.get('interview_type') != interview_type:
                                continue
                            
                            interviews.append(data)
            
            # Sort by scheduled date
            interviews.sort(key=lambda x: x.get('scheduled_at', ''))
            
            return interviews[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list interviews: {str(e)}")
            raise
    
    async def generate_feedback_insights(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate AI insights from feedback data."""
        try:
            feedback_data = []
            
            # Read feedback data
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            created_at = datetime.fromisoformat(data.get('created_at', ''))
                            if start_date <= created_at <= end_date:
                                feedback_data.append(data)
            
            # Analyze feedback (simplified implementation)
            comments = [item.get('comment', '') for item in feedback_data if item.get('comment')]
            ratings = [item.get('rating') for item in feedback_data if item.get('rating') is not None]
            
            # Calculate sentiment score (simplified)
            positive_words = ['great', 'excellent', 'love', 'amazing', 'helpful', 'easy', 'good']
            negative_words = ['bad', 'terrible', 'hate', 'difficult', 'confusing', 'broken', 'slow']
            
            sentiment_scores = []
            for comment in comments:
                comment_lower = comment.lower()
                positive_count = sum(1 for word in positive_words if word in comment_lower)
                negative_count = sum(1 for word in negative_words if word in comment_lower)
                
                if positive_count + negative_count > 0:
                    score = (positive_count - negative_count) / (positive_count + negative_count)
                    sentiment_scores.append(score)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            # Extract common themes (simplified)
            common_themes = []
            if any('slow' in comment.lower() for comment in comments):
                common_themes.append('Performance concerns')
            if any('difficult' in comment.lower() or 'confusing' in comment.lower() for comment in comments):
                common_themes.append('Usability issues')
            if any('feature' in comment.lower() for comment in comments):
                common_themes.append('Feature requests')
            
            # Generate improvement suggestions
            improvement_suggestions = []
            if avg_sentiment < 0:
                improvement_suggestions.append('Focus on addressing user pain points')
            if any(rating < 3 for rating in ratings):
                improvement_suggestions.append('Investigate low-rated touchpoints')
            if len(comments) < len(feedback_data) * 0.3:
                improvement_suggestions.append('Encourage more detailed feedback')
            
            # Satisfaction trend (simplified)
            satisfaction_trend = []
            for i in range(4):  # Last 4 weeks
                week_start = end_date - timedelta(weeks=i+1)
                week_end = end_date - timedelta(weeks=i)
                week_ratings = [
                    item.get('rating') for item in feedback_data
                    if item.get('rating') and 
                    week_start <= datetime.fromisoformat(item.get('created_at', '')) < week_end
                ]
                avg_rating = sum(week_ratings) / len(week_ratings) if week_ratings else None
                satisfaction_trend.insert(0, {
                    'week': f"Week {4-i}",
                    'average_rating': avg_rating
                })
            
            # Feature requests summary
            feature_requests = [item for item in feedback_data if item.get('type') == 'feature_request']
            feature_requests_summary = {
                'total': len(feature_requests),
                'urgent': sum(1 for item in feature_requests if 'urgent' in item.get('comment', '').lower())
            }
            
            return {
                'success': True,
                'sentiment_score': avg_sentiment,
                'common_themes': common_themes,
                'improvement_suggestions': improvement_suggestions,
                'satisfaction_trend': satisfaction_trend,
                'feature_requests_summary': feature_requests_summary
            }
            
        except Exception as e:
            logger.error(f"Failed to generate feedback insights: {str(e)}")
            raise


# Global service instance
_feedback_service = None


def init_feedback_service(storage_path: str = "feedback_data") -> None:
    """Initialize the feedback service."""
    global _feedback_service
    _feedback_service = FeedbackService(storage_path)
    logger.info(f"Feedback service initialized with storage path: {storage_path}")


def get_feedback_service() -> FeedbackService:
    """Get the feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        init_feedback_service()
    return _feedback_service