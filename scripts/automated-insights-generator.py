#!/usr/bin/env python3
"""
Automated Insights Generator for SocialMapper Feedback System

This script generates weekly and monthly reports with actionable insights
from user feedback and analytics data for continuous product improvement.

Features:
- Sentiment analysis of feedback comments
- Trend identification across time periods  
- User journey bottleneck detection
- Feature request prioritization recommendations
- Performance impact correlation analysis
- Automated alert generation for critical issues
"""

import json
import logging
import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import statistics
import re
from collections import Counter, defaultdict

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
console = Console()


class SentimentAnalyzer:
    """Simple sentiment analysis for feedback comments."""
    
    POSITIVE_WORDS = [
        'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'love', 'perfect',
        'easy', 'helpful', 'intuitive', 'fast', 'efficient', 'clear', 'smooth',
        'useful', 'powerful', 'innovative', 'impressive', 'outstanding'
    ]
    
    NEGATIVE_WORDS = [
        'terrible', 'awful', 'hate', 'horrible', 'disgusting', 'worst', 'broken',
        'slow', 'confusing', 'difficult', 'frustrating', 'annoying', 'buggy',
        'clunky', 'complicated', 'unclear', 'poor', 'disappointing', 'useless'
    ]
    
    @classmethod
    def analyze_sentiment(cls, text: str) -> float:
        """
        Analyze sentiment of text.
        Returns float between -1 (very negative) and 1 (very positive).
        """
        if not text:
            return 0.0
            
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        positive_count = sum(1 for word in words if word in cls.POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in cls.NEGATIVE_WORDS)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
            
        return (positive_count - negative_count) / total_sentiment_words


class FeedbackAnalyzer:
    """Analyzes feedback data for patterns and insights."""
    
    def __init__(self, feedback_data: List[Dict[str, Any]]):
        self.feedback_data = feedback_data
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze_sentiment_trends(self) -> Dict[str, Any]:
        """Analyze sentiment trends over time."""
        daily_sentiment = defaultdict(list)
        
        for feedback in self.feedback_data:
            if feedback.get('comment'):
                date = feedback.get('created_at', '')[:10]  # Extract date part
                sentiment = self.sentiment_analyzer.analyze_sentiment(feedback['comment'])
                daily_sentiment[date].append(sentiment)
        
        # Calculate daily averages
        sentiment_trend = {}
        for date, sentiments in daily_sentiment.items():
            if sentiments:
                sentiment_trend[date] = statistics.mean(sentiments)
        
        return {
            'daily_sentiment': sentiment_trend,
            'overall_sentiment': statistics.mean([s for sentiments in daily_sentiment.values() for s in sentiments]) if daily_sentiment else 0,
            'sentiment_volatility': statistics.stdev([s for sentiments in daily_sentiment.values() for s in sentiments]) if len([s for sentiments in daily_sentiment.values() for s in sentiments]) > 1 else 0
        }
    
    def identify_common_issues(self) -> List[Dict[str, Any]]:
        """Identify frequently mentioned issues."""
        issue_keywords = {
            'performance': ['slow', 'loading', 'lag', 'timeout', 'freeze', 'crash'],
            'usability': ['confusing', 'difficult', 'hard', 'unclear', 'complicated'],
            'bugs': ['bug', 'error', 'broken', 'glitch', 'issue', 'problem'],
            'features': ['missing', 'need', 'want', 'request', 'add', 'include'],
            'ui_ux': ['design', 'layout', 'interface', 'visual', 'appearance']
        }
        
        issue_counts = defaultdict(int)
        issue_examples = defaultdict(list)
        
        for feedback in self.feedback_data:
            comment = feedback.get('comment', '').lower()
            if comment:
                for category, keywords in issue_keywords.items():
                    if any(keyword in comment for keyword in keywords):
                        issue_counts[category] += 1
                        if len(issue_examples[category]) < 3:  # Keep up to 3 examples
                            issue_examples[category].append(comment[:100] + '...' if len(comment) > 100 else comment)
        
        issues = []
        for category, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            issues.append({
                'category': category,
                'count': count,
                'percentage': (count / len(self.feedback_data)) * 100 if self.feedback_data else 0,
                'examples': issue_examples[category]
            })
        
        return issues
    
    def analyze_rating_patterns(self) -> Dict[str, Any]:
        """Analyze rating patterns and correlations."""
        ratings = [fb.get('rating') for fb in self.feedback_data if fb.get('rating')]
        touchpoints = defaultdict(list)
        
        for feedback in self.feedback_data:
            if feedback.get('rating') and feedback.get('touchpoint'):
                touchpoints[feedback['touchpoint']].append(feedback['rating'])
        
        touchpoint_ratings = {}
        for touchpoint, rating_list in touchpoints.items():
            if rating_list:
                touchpoint_ratings[touchpoint] = {
                    'average': statistics.mean(rating_list),
                    'count': len(rating_list),
                    'distribution': dict(Counter(rating_list))
                }
        
        return {
            'overall_rating': statistics.mean(ratings) if ratings else None,
            'rating_distribution': dict(Counter(ratings)),
            'touchpoint_ratings': touchpoint_ratings,
            'low_rating_percentage': (len([r for r in ratings if r <= 2]) / len(ratings)) * 100 if ratings else 0
        }


class AnalyticsProcessor:
    """Processes user analytics data for insights."""
    
    def __init__(self, analytics_data: List[Dict[str, Any]]):
        self.analytics_data = analytics_data
    
    def analyze_user_journey_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify bottlenecks in user journey."""
        # Group events by session
        sessions = defaultdict(list)
        for event in self.analytics_data:
            session_id = event.get('session_id')
            if session_id:
                sessions[session_id].append(event)
        
        # Analyze common journey patterns
        journey_steps = ['landing', 'configuration', 'analysis', 'results', 'export']
        step_completion_rates = {}
        
        for step in journey_steps:
            completed_sessions = 0
            total_sessions_reaching_step = 0
            
            for session_events in sessions.values():
                # Check if session reached this step
                reached_step = any(step.lower() in event.get('event_name', '').lower() or 
                                 step.lower() in str(event.get('properties', {})).lower() 
                                 for event in session_events)
                
                if reached_step:
                    total_sessions_reaching_step += 1
                    
                    # Check if step was completed (simplified logic)
                    completed_step = any('completed' in event.get('event_name', '').lower() and 
                                       step.lower() in str(event.get('properties', {})).lower()
                                       for event in session_events)
                    
                    if completed_step:
                        completed_sessions += 1
            
            if total_sessions_reaching_step > 0:
                completion_rate = (completed_sessions / total_sessions_reaching_step) * 100
                step_completion_rates[step] = {
                    'completion_rate': completion_rate,
                    'sessions_reached': total_sessions_reaching_step,
                    'sessions_completed': completed_sessions
                }
        
        # Identify bottlenecks (steps with low completion rates)
        bottlenecks = []
        for step, data in step_completion_rates.items():
            if data['completion_rate'] < 70 and data['sessions_reached'] > 10:  # Arbitrary thresholds
                bottlenecks.append({
                    'step': step,
                    'completion_rate': data['completion_rate'],
                    'sessions_impacted': data['sessions_reached'] - data['sessions_completed'],
                    'severity': 'high' if data['completion_rate'] < 50 else 'medium'
                })
        
        return sorted(bottlenecks, key=lambda x: x['sessions_impacted'], reverse=True)
    
    def calculate_engagement_metrics(self) -> Dict[str, Any]:
        """Calculate user engagement metrics."""
        sessions = defaultdict(list)
        for event in self.analytics_data:
            session_id = event.get('session_id')
            if session_id:
                sessions[session_id].append(event)
        
        session_durations = []
        page_views_per_session = []
        bounce_sessions = 0
        
        for session_events in sessions.values():
            if len(session_events) == 1:
                bounce_sessions += 1
            
            page_views = len([e for e in session_events if e.get('event_name') == 'page_view'])
            page_views_per_session.append(page_views)
            
            # Calculate session duration (simplified)
            timestamps = [e.get('timestamp') for e in session_events if e.get('timestamp')]
            if len(timestamps) > 1:
                try:
                    start_time = min(datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps)
                    end_time = max(datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps)
                    duration = (end_time - start_time).total_seconds() / 60  # minutes
                    session_durations.append(duration)
                except:
                    pass
        
        return {
            'total_sessions': len(sessions),
            'bounce_rate': (bounce_sessions / len(sessions)) * 100 if sessions else 0,
            'avg_session_duration': statistics.mean(session_durations) if session_durations else 0,
            'avg_pages_per_session': statistics.mean(page_views_per_session) if page_views_per_session else 0,
            'engaged_sessions': len([d for d in session_durations if d > 5])  # Sessions > 5 minutes
        }


class InsightsGenerator:
    """Generates actionable insights from analyzed data."""
    
    def __init__(self, feedback_data: List[Dict], analytics_data: List[Dict]):
        self.feedback_analyzer = FeedbackAnalyzer(feedback_data)
        self.analytics_processor = AnalyticsProcessor(analytics_data)
    
    def generate_weekly_insights(self) -> Dict[str, Any]:
        """Generate weekly insights report."""
        sentiment_analysis = self.feedback_analyzer.analyze_sentiment_trends()
        common_issues = self.feedback_analyzer.identify_common_issues()
        rating_analysis = self.feedback_analyzer.analyze_rating_patterns()
        bottlenecks = self.analytics_processor.analyze_user_journey_bottlenecks()
        engagement = self.analytics_processor.calculate_engagement_metrics()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            sentiment_analysis, common_issues, rating_analysis, bottlenecks, engagement
        )
        
        return {
            'report_type': 'weekly',
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'overall_sentiment': sentiment_analysis['overall_sentiment'],
                'top_issues': common_issues[:3],
                'average_rating': rating_analysis['overall_rating'],
                'critical_bottlenecks': [b for b in bottlenecks if b['severity'] == 'high'],
                'engagement_score': self._calculate_engagement_score(engagement)
            },
            'detailed_analysis': {
                'sentiment': sentiment_analysis,
                'issues': common_issues,
                'ratings': rating_analysis,
                'user_journey': bottlenecks,
                'engagement': engagement
            },
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, sentiment, issues, ratings, bottlenecks, engagement) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Sentiment-based recommendations
        if sentiment['overall_sentiment'] < -0.2:
            recommendations.append({
                'priority': 'high',
                'category': 'user_satisfaction',
                'title': 'Address declining user satisfaction',
                'description': f'Overall sentiment is negative ({sentiment["overall_sentiment"]:.2f}). Focus on resolving top user complaints.',
                'actions': ['Review recent feedback', 'Identify pain points', 'Implement quick fixes']
            })
        
        # Issue-based recommendations
        if issues:
            top_issue = issues[0]
            if top_issue['count'] > 5:  # Arbitrary threshold
                recommendations.append({
                    'priority': 'high' if top_issue['percentage'] > 20 else 'medium',
                    'category': 'feature_improvement',
                    'title': f'Address {top_issue["category"]} concerns',
                    'description': f'{top_issue["category"].title()} issues mentioned in {top_issue["count"]} feedback items ({top_issue["percentage"]:.1f}%)',
                    'actions': [f'Investigate {top_issue["category"]} problems', 'Plan improvements', 'Test solutions']
                })
        
        # Rating-based recommendations  
        if ratings['overall_rating'] and ratings['overall_rating'] < 3.5:
            recommendations.append({
                'priority': 'high',
                'category': 'user_experience',
                'title': 'Improve overall user rating',
                'description': f'Average rating is {ratings["overall_rating"]:.1f}/5. Focus on core user experience improvements.',
                'actions': ['Analyze low-rated touchpoints', 'Improve onboarding', 'Fix critical usability issues']
            })
        
        # Journey bottleneck recommendations
        for bottleneck in bottlenecks[:2]:  # Top 2 bottlenecks
            recommendations.append({
                'priority': 'high' if bottleneck['severity'] == 'high' else 'medium',
                'category': 'conversion_optimization',
                'title': f'Optimize {bottleneck["step"]} step',
                'description': f'{bottleneck["step"].title()} step has {bottleneck["completion_rate"]:.1f}% completion rate, impacting {bottleneck["sessions_impacted"]} users.',
                'actions': [f'Analyze {bottleneck["step"]} user flows', 'Identify friction points', 'A/B test improvements']
            })
        
        # Engagement recommendations
        if engagement['bounce_rate'] > 70:
            recommendations.append({
                'priority': 'medium',
                'category': 'engagement',
                'title': 'Reduce bounce rate',
                'description': f'Bounce rate is {engagement["bounce_rate"]:.1f}%. Users may not be finding what they need quickly.',
                'actions': ['Improve landing page clarity', 'Add better onboarding', 'Optimize initial user experience']
            })
        
        return sorted(recommendations, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
    
    def _calculate_engagement_score(self, engagement: Dict[str, Any]) -> float:
        """Calculate overall engagement score (0-100)."""
        score = 0
        
        # Bounce rate impact (lower is better)
        bounce_score = max(0, 100 - engagement['bounce_rate'])
        score += bounce_score * 0.3
        
        # Session duration impact
        duration_score = min(100, engagement['avg_session_duration'] * 10)  # 10 minutes = 100 points
        score += duration_score * 0.3
        
        # Pages per session impact
        pages_score = min(100, engagement['avg_pages_per_session'] * 20)  # 5 pages = 100 points
        score += pages_score * 0.2
        
        # Engaged sessions impact
        if engagement['total_sessions'] > 0:
            engaged_rate = (engagement['engaged_sessions'] / engagement['total_sessions']) * 100
            score += engaged_rate * 0.2
        
        return round(score, 1)


class ReportGenerator:
    """Generates formatted reports and notifications."""
    
    def __init__(self, insights: Dict[str, Any]):
        self.insights = insights
    
    def generate_console_report(self) -> None:
        """Generate a rich console report."""
        console.print(Panel.fit(
            f"[bold blue]SocialMapper Analytics Report[/bold blue]\n"
            f"Generated: {self.insights['generated_at']}\n"
            f"Report Type: {self.insights['report_type'].title()}",
            title="📊 Analytics Dashboard"
        ))
        
        # Summary section
        summary = self.insights['summary']
        summary_text = Text()
        summary_text.append("📈 Engagement Score: ", style="bold")
        summary_text.append(f"{summary['engagement_score']}/100\n", style="green" if summary['engagement_score'] > 70 else "yellow" if summary['engagement_score'] > 40 else "red")
        
        summary_text.append("😊 Overall Sentiment: ", style="bold")
        sentiment_color = "green" if summary['overall_sentiment'] > 0.2 else "red" if summary['overall_sentiment'] < -0.2 else "yellow"
        summary_text.append(f"{summary['overall_sentiment']:.2f}\n", style=sentiment_color)
        
        if summary['average_rating']:
            summary_text.append("⭐ Average Rating: ", style="bold")
            rating_color = "green" if summary['average_rating'] > 4 else "yellow" if summary['average_rating'] > 3 else "red"
            summary_text.append(f"{summary['average_rating']:.1f}/5\n", style=rating_color)
        
        console.print(Panel(summary_text, title="📋 Executive Summary"))
        
        # Recommendations table
        if self.insights['recommendations']:
            table = Table(title="🎯 Priority Recommendations")
            table.add_column("Priority", style="bold")
            table.add_column("Category")
            table.add_column("Issue")
            table.add_column("Actions")
            
            for rec in self.insights['recommendations'][:5]:  # Top 5 recommendations
                priority_color = "red" if rec['priority'] == 'high' else "yellow" if rec['priority'] == 'medium' else "green"
                table.add_row(
                    f"[{priority_color}]{rec['priority'].upper()}[/{priority_color}]",
                    rec['category'].replace('_', ' ').title(),
                    rec['title'],
                    ', '.join(rec['actions'][:2])  # First 2 actions
                )
            
            console.print(table)
        
        # Issues breakdown
        if self.insights['summary']['top_issues']:
            issues_text = Text("🔍 Top Issues Mentioned:\n\n", style="bold")
            for i, issue in enumerate(self.insights['summary']['top_issues'], 1):
                issues_text.append(f"{i}. {issue['category'].title()}: ", style="bold")
                issues_text.append(f"{issue['count']} mentions ({issue['percentage']:.1f}%)\n")
            
            console.print(Panel(issues_text, title="⚠️  Issue Analysis"))
    
    def generate_json_report(self, output_path: Path) -> None:
        """Save insights as JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.insights, f, indent=2, default=str)
        
        console.print(f"✅ Report saved to {output_path}")
    
    def generate_email_report(self, recipient_email: str, smtp_config: Dict[str, str]) -> None:
        """Send email report to stakeholders."""
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['from_email']
            msg['To'] = recipient_email
            msg['Subject'] = f"SocialMapper Weekly Analytics Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create HTML email body
            html_body = self._create_html_email_body()
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port'])
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            console.print(f"✅ Email report sent to {recipient_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            console.print(f"❌ Failed to send email: {e}")
    
    def _create_html_email_body(self) -> str:
        """Create HTML email body."""
        summary = self.insights['summary']
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>🚀 SocialMapper Analytics Report</h2>
            <p><strong>Generated:</strong> {self.insights['generated_at']}</p>
            
            <h3>📊 Executive Summary</h3>
            <ul>
                <li><strong>Engagement Score:</strong> {summary['engagement_score']}/100</li>
                <li><strong>Overall Sentiment:</strong> {summary['overall_sentiment']:.2f}</li>
                {f"<li><strong>Average Rating:</strong> {summary['average_rating']:.1f}/5</li>" if summary['average_rating'] else ""}
            </ul>
            
            <h3>🎯 Priority Recommendations</h3>
            <ol>
        """
        
        for rec in self.insights['recommendations'][:3]:
            html += f"""
                <li>
                    <strong>[{rec['priority'].upper()}] {rec['title']}</strong><br>
                    {rec['description']}<br>
                    <em>Actions: {', '.join(rec['actions'])}</em>
                </li>
            """
        
        html += """
            </ol>
            
            <p>For detailed analytics, please check the full dashboard.</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This automated report is generated from SocialMapper user feedback and analytics data.
            </p>
        </body>
        </html>
        """
        
        return html


def load_feedback_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load feedback data from JSONL file."""
    feedback_data = []
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        feedback_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    return feedback_data


def load_analytics_data(data_path: Path) -> List[Dict[str, Any]]:
    """Load analytics data from JSONL file."""
    analytics_data = []
    
    if data_path.exists():
        with open(data_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        analytics_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    
    return analytics_data


def main():
    """Main execution function."""
    console.print("[bold blue]🚀 Starting SocialMapper Automated Insights Generation[/bold blue]")
    
    # Configuration
    data_dir = Path("feedback_data")
    output_dir = Path("reports")
    
    # Load data
    console.print("📂 Loading feedback and analytics data...")
    feedback_data = load_feedback_data(data_dir / "feedback.jsonl")
    analytics_data = load_analytics_data(data_dir / "analytics.jsonl")
    
    console.print(f"📊 Loaded {len(feedback_data)} feedback items and {len(analytics_data)} analytics events")
    
    if not feedback_data and not analytics_data:
        console.print("⚠️  No data found. Generating sample insights...")
        # Generate sample insights for demonstration
        sample_insights = {
            'report_type': 'weekly',
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'overall_sentiment': 0.3,
                'top_issues': [],
                'average_rating': 4.2,
                'critical_bottlenecks': [],
                'engagement_score': 75.5
            },
            'detailed_analysis': {},
            'recommendations': [
                {
                    'priority': 'medium',
                    'category': 'engagement',
                    'title': 'Improve user onboarding',
                    'description': 'Sample recommendation for better user experience',
                    'actions': ['Review onboarding flow', 'Add guided tour', 'Collect feedback']
                }
            ]
        }
    else:
        # Generate insights
        console.print("🔍 Analyzing data and generating insights...")
        generator = InsightsGenerator(feedback_data, analytics_data)
        sample_insights = generator.generate_weekly_insights()
    
    # Generate reports
    console.print("📝 Generating reports...")
    report_generator = ReportGenerator(sample_insights)
    
    # Console report
    report_generator.generate_console_report()
    
    # JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_generator.generate_json_report(output_dir / f"weekly_insights_{timestamp}.json")
    
    # Email report (if configured)
    email_config = {
        'smtp_host': 'smtp.gmail.com',  # Configure as needed
        'smtp_port': 587,
        'from_email': 'analytics@socialmapper.org',
        'username': 'your_email',
        'password': 'your_password'  # Use environment variables in production
    }
    
    # Uncomment to enable email reports
    # report_generator.generate_email_report('team@socialmapper.org', email_config)
    
    console.print("[bold green]✅ Automated insights generation completed![/bold green]")


if __name__ == "__main__":
    main()