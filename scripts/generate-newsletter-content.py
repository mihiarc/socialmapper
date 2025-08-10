#!/usr/bin/env python3
"""
SocialMapper Newsletter Content Generator

This script automates the monthly newsletter content generation by:
1. Collecting data from GitHub (releases, discussions, stats)
2. Processing community content and highlights
3. Generating formatted newsletter content
4. Creating email templates and social media posts

Usage:
    python scripts/generate-newsletter-content.py --month "September 2025"
    python scripts/generate-newsletter-content.py --output-dir newsletter-content
"""

import argparse
import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

class GitHubDataCollector:
    """Collects data from GitHub API for newsletter content."""
    
    def __init__(self, repo: str = "mihiarc/socialmapper"):
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {}
        
        # Use GitHub token if available for higher rate limits
        if os.getenv('GITHUB_TOKEN'):
            self.headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    def get_recent_releases(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get releases from the past N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        url = f"{self.api_base}/repos/{self.repo}/releases"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        releases = response.json()
        recent_releases = []
        
        for release in releases:
            published_at = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
            if published_at >= cutoff_date.replace(tzinfo=published_at.tzinfo):
                recent_releases.append({
                    'title': release['tag_name'],
                    'name': release['name'],
                    'description': self._clean_markdown(release['body'])[:300] + '...' if len(release['body']) > 300 else self._clean_markdown(release['body']),
                    'url': release['html_url'],
                    'published_at': published_at.strftime('%Y-%m-%d'),
                    'assets': len(release['assets'])
                })
        
        return recent_releases
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get current repository statistics."""
        url = f"{self.api_base}/repos/{self.repo}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        repo_data = response.json()
        
        return {
            'stars': repo_data['stargazers_count'],
            'forks': repo_data['forks_count'],
            'watchers': repo_data['subscribers_count'],
            'open_issues': repo_data['open_issues_count'],
            'language': repo_data['language'],
            'size_kb': repo_data['size']
        }
    
    def get_community_discussions(self, days: int = 30) -> Dict[str, List[Dict]]:
        """Get recent community discussions by category."""
        # Note: This requires GitHub CLI for GraphQL access
        # Using gh CLI to get discussions data
        
        query = '''
        query {
          repository(owner: "mihiarc", name: "socialmapper") {
            discussions(first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                title
                body
                createdAt
                updatedAt
                category { name }
                author { login }
                comments(first: 1) { totalCount }
                upvoteCount
                url
              }
            }
          }
        }
        '''
        
        try:
            result = subprocess.run(
                ['gh', 'api', 'graphql', '-f', f'query={query}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                discussions = data['data']['repository']['discussions']['nodes']
                
                # Filter by date and categorize
                cutoff_date = datetime.now() - timedelta(days=days)
                categorized = {
                    'Show & Tell': [],
                    'Feature Requests': [],
                    'General Q&A': [],
                    'Research & Papers': [],
                    'API & Development': [],
                    'Tutorials & Learning': [],
                    'Announcements': []
                }
                
                for discussion in discussions:
                    created_at = datetime.fromisoformat(discussion['createdAt'].replace('Z', '+00:00'))
                    if created_at >= cutoff_date.replace(tzinfo=created_at.tzinfo):
                        category = discussion['category']['name']
                        if category in categorized:
                            categorized[category].append({
                                'title': discussion['title'],
                                'author': discussion['author']['login'],
                                'comments': discussion['comments']['totalCount'],
                                'upvotes': discussion['upvoteCount'],
                                'created_at': created_at.strftime('%Y-%m-%d'),
                                'url': discussion['url'],
                                'preview': self._clean_markdown(discussion['body'])[:150] + '...' if len(discussion['body']) > 150 else self._clean_markdown(discussion['body'])
                            })
                
                return categorized
            else:
                print(f"Warning: Could not fetch discussions: {result.stderr}")
                return {}
                
        except FileNotFoundError:
            print("Warning: GitHub CLI not found. Skipping discussions data.")
            return {}
        except Exception as e:
            print(f"Warning: Error fetching discussions: {e}")
            return {}
    
    def get_top_contributors(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get top contributors from the past month."""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get commits
        url = f"{self.api_base}/repos/{self.repo}/commits"
        params = {'since': since_date, 'per_page': 100}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        commits = response.json()
        contributors = {}
        
        for commit in commits:
            if commit['author']:
                author = commit['author']['login']
                if author not in contributors:
                    contributors[author] = {
                        'name': commit['author']['login'],
                        'avatar_url': commit['author']['avatar_url'],
                        'commits': 0,
                        'profile_url': commit['author']['html_url']
                    }
                contributors[author]['commits'] += 1
        
        # Sort by commit count and return top 5
        top_contributors = sorted(
            contributors.values(),
            key=lambda x: x['commits'],
            reverse=True
        )[:5]
        
        return top_contributors
    
    def _clean_markdown(self, text: str) -> str:
        """Clean markdown formatting for email content."""
        if not text:
            return ""
        
        # Remove markdown formatting for email
        import re
        
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '[Code Example]', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        return text.strip()

class NewsletterContentGenerator:
    """Generates formatted newsletter content."""
    
    def __init__(self, github_collector: GitHubDataCollector):
        self.github = github_collector
    
    def generate_monthly_content(self, month: str, year: int) -> Dict[str, Any]:
        """Generate complete monthly newsletter content."""
        print(f"🔄 Collecting data for {month} {year}...")
        
        # Collect all data
        releases = self.github.get_recent_releases()
        stats = self.github.get_repository_stats()
        discussions = self.github.get_community_discussions()
        contributors = self.github.get_top_contributors()
        
        # Calculate additional stats
        total_discussions = sum(len(topics) for topics in discussions.values())
        most_active_category = max(discussions.keys(), key=lambda k: len(discussions[k])) if discussions else "General Q&A"
        
        newsletter_content = {
            'metadata': {
                'month': month,
                'year': year,
                'generated_at': datetime.now().isoformat(),
                'newsletter_title': f"SocialMapper Insights - {month} {year}"
            },
            'stats': {
                'github_stars': stats['stars'],
                'community_members': stats['watchers'],
                'total_discussions': total_discussions,
                'monthly_releases': len(releases),
                'top_contributors_count': len(contributors),
                'most_active_category': most_active_category
            },
            'releases': releases,
            'discussions': discussions,
            'contributors': contributors,
            'featured_content': self._select_featured_content(discussions),
            'community_highlights': self._generate_community_highlights(discussions, contributors),
            'upcoming_events': self._generate_upcoming_events(month, year),
            'tips_and_tricks': self._generate_monthly_tip(),
            'research_roundup': self._generate_research_roundup()
        }
        
        return newsletter_content
    
    def _select_featured_content(self, discussions: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Select featured content for the newsletter."""
        featured = {
            'analysis_of_month': None,
            'community_question': None,
            'feature_request_highlight': None
        }
        
        # Find top Show & Tell
        if discussions.get('Show & Tell'):
            show_tell = discussions['Show & Tell']
            if show_tell:
                # Sort by engagement (upvotes + comments)
                top_analysis = max(
                    show_tell,
                    key=lambda x: x['upvotes'] + x['comments']
                )
                featured['analysis_of_month'] = top_analysis
        
        # Find top Q&A
        if discussions.get('General Q&A'):
            qa_discussions = discussions['General Q&A']
            if qa_discussions:
                top_question = max(
                    qa_discussions,
                    key=lambda x: x['comments']
                )
                featured['community_question'] = top_question
        
        # Find top feature request
        if discussions.get('Feature Requests'):
            feature_requests = discussions['Feature Requests']
            if feature_requests:
                top_request = max(
                    feature_requests,
                    key=lambda x: x['upvotes']
                )
                featured['feature_request_highlight'] = top_request
        
        return featured
    
    def _generate_community_highlights(self, discussions: Dict[str, List[Dict]], contributors: List[Dict]) -> List[Dict[str, Any]]:
        """Generate community highlight stories."""
        highlights = []
        
        # Top contributor highlight
        if contributors:
            top_contributor = contributors[0]
            highlights.append({
                'type': 'contributor',
                'title': f"Contributor Spotlight: {top_contributor['name']}",
                'description': f"Made {top_contributor['commits']} contributions this month!",
                'action_url': top_contributor['profile_url']
            })
        
        # Most active discussion category
        if discussions:
            most_active = max(discussions.keys(), key=lambda k: len(discussions[k]))
            if discussions[most_active]:
                highlights.append({
                    'type': 'category',
                    'title': f"Most Active: {most_active}",
                    'description': f"{len(discussions[most_active])} new discussions this month",
                    'action_url': f"https://github.com/mihiarc/socialmapper/discussions/categories/{most_active.lower().replace(' ', '-').replace('&', 'and')}"
                })
        
        return highlights
    
    def _generate_upcoming_events(self, month: str, year: int) -> List[Dict[str, Any]]:
        """Generate upcoming events section."""
        # Calculate next meetup (first Thursday of next month)
        current = datetime(year, list(calendar.month_name).index(month), 1)
        next_month = current.replace(month=current.month + 1) if current.month < 12 else current.replace(year=current.year + 1, month=1)
        
        # Find first Thursday
        first_day = next_month.replace(day=1)
        days_to_thursday = (3 - first_day.weekday()) % 7  # Thursday is weekday 3
        first_thursday = first_day + timedelta(days=days_to_thursday)
        
        events = [
            {
                'type': 'meetup',
                'title': f"Monthly Community Meetup",
                'date': first_thursday.strftime('%B %d, %Y'),
                'time': '2:00 PM EST / 11:00 AM PST',
                'description': 'Join us for community updates, featured analysis presentations, and live Q&A.',
                'registration_url': 'https://github.com/mihiarc/socialmapper/discussions',
                'platform': 'Zoom (Virtual)'
            }
        ]
        
        return events
    
    def _generate_monthly_tip(self) -> Dict[str, Any]:
        """Generate tip of the month content."""
        tips = [
            {
                'title': 'Optimize Large Analysis Performance',
                'description': 'For analyzing large geographic areas, use the ZCTA geographic level instead of block groups to improve performance.',
                'code_example': 'config = SocialMapperBuilder().with_geographic_level("zcta").build()',
                'documentation_url': 'https://mihiarc.github.io/socialmapper/user-guide/demographics/'
            },
            {
                'title': 'Batch Processing Multiple Locations',
                'description': 'Use custom POI coordinates to analyze multiple specific locations in a single analysis.',
                'code_example': 'client.analyze_custom_pois("locations.csv", travel_time=15)',
                'documentation_url': 'https://mihiarc.github.io/socialmapper/tutorials/custom-pois-tutorial/'
            },
            {
                'title': 'Export Results for GIS Software',
                'description': 'Export your results as GeoParquet for efficient loading in QGIS, ArcGIS, or Python.',
                'code_example': 'config = builder.with_exports(geoparquet=True).build()',
                'documentation_url': 'https://mihiarc.github.io/socialmapper/user-guide/exporting-results/'
            }
        ]
        
        # Select tip based on current month
        current_month = datetime.now().month
        return tips[current_month % len(tips)]
    
    def _generate_research_roundup(self) -> Dict[str, Any]:
        """Generate research and publications section."""
        return {
            'title': 'Research & Academic Usage',
            'description': 'Recent academic applications and research using SocialMapper',
            'call_to_action': 'Using SocialMapper in your research? Share your work in our Research & Papers discussions!',
            'featured_topics': [
                'Urban accessibility and equity analysis',
                'Public health service catchment areas',
                'Transportation planning and modal choice',
                'Environmental justice and demographics'
            ],
            'collaboration_opportunities': [
                'Academic partnership program - connect with other researchers',
                'Citation support - help with proper attribution and methodology',
                'Conference presentation opportunities',
                'Open datasets for validation and comparison'
            ]
        }

def create_email_template(content: Dict[str, Any], output_path: Path) -> str:
    """Create HTML email template from content."""
    
    template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content['metadata']['newsletter_title']}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6; 
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{ 
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-box {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }}
        
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            margin-top: 5px;
        }}
        
        .highlight-box {{
            background: #f0f8ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 6px 6px 0;
        }}
        
        .success-box {{
            background: #f0fff4;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 6px 6px 0;
        }}
        
        .cta-button {{
            display: inline-block;
            background: #667eea;
            color: white !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 10px 0;
            transition: background 0.3s;
        }}
        
        .cta-button:hover {{
            background: #5a6fd8;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .list-unstyled {{
            list-style: none;
            padding: 0;
        }}
        
        .list-unstyled li {{
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .list-unstyled li:last-child {{
            border-bottom: none;
        }}
        
        @media (max-width: 480px) {{
            body {{ padding: 10px; }}
            .stats-grid {{ grid-template-columns: 1fr 1fr; }}
            .header {{ padding: 20px; }}
            .content {{ padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏘️ SocialMapper Insights</h1>
            <p>{content['metadata']['month']} {content['metadata']['year']} | Your Monthly Community Update</p>
        </div>
        
        <div class="content">
            <!-- Community Stats Section -->
            <div class="section">
                <h2>📊 Community Growth</h2>
                <p>Here's how our community grew this month:</p>
                <div class="stats-grid">
                    <div class="stat-box">
                        <span class="stat-number">{content['stats']['github_stars']}</span>
                        <div class="stat-label">GitHub Stars</div>
                    </div>
                    <div class="stat-box">
                        <span class="stat-number">{content['stats']['total_discussions']}</span>
                        <div class="stat-label">New Discussions</div>
                    </div>
                    <div class="stat-box">
                        <span class="stat-number">{content['stats']['monthly_releases']}</span>
                        <div class="stat-label">Releases</div>
                    </div>
                    <div class="stat-box">
                        <span class="stat-number">{content['stats']['top_contributors_count']}</span>
                        <div class="stat-label">Contributors</div>
                    </div>
                </div>
                <p><strong>Most Active Category:</strong> {content['stats']['most_active_category']}</p>
            </div>'''
    
    # Platform Updates Section
    if content['releases']:
        template += '''
            <div class="section">
                <h2>🚀 Platform Updates</h2>
                <p>Latest releases and improvements:</p>'''
        
        for release in content['releases'][:3]:  # Show top 3 releases
            template += f'''
                <div class="success-box">
                    <h3>{release['title']}</h3>
                    <p>{release['description']}</p>
                    <p><small>Released: {release['published_at']}</small></p>
                    <a href="{release['url']}" class="cta-button">View Release Notes</a>
                </div>'''
        
        template += '''</div>'''
    
    # Featured Content Section
    featured = content['featured_content']
    if featured['analysis_of_month']:
        analysis = featured['analysis_of_month']
        template += f'''
            <div class="section">
                <h2>⭐ Analysis of the Month</h2>
                <div class="highlight-box">
                    <h3>{analysis['title']}</h3>
                    <p><strong>By:</strong> {analysis['author']} | <strong>Engagement:</strong> {analysis['upvotes']} upvotes, {analysis['comments']} comments</p>
                    <p>{analysis['preview']}</p>
                    <a href="{analysis['url']}" class="cta-button">Read Full Analysis</a>
                </div>
            </div>'''
    
    # Community Highlights
    if content['community_highlights']:
        template += '''
            <div class="section">
                <h2>🤝 Community Highlights</h2>'''
        
        for highlight in content['community_highlights']:
            template += f'''
                <div class="highlight-box">
                    <h3>{highlight['title']}</h3>
                    <p>{highlight['description']}</p>
                    <a href="{highlight['action_url']}" class="cta-button">Learn More</a>
                </div>'''
        
        template += '''</div>'''
    
    # Upcoming Events
    if content['upcoming_events']:
        template += '''
            <div class="section">
                <h2>🗓️ Upcoming Events</h2>'''
        
        for event in content['upcoming_events']:
            template += f'''
                <div class="success-box">
                    <h3>{event['title']}</h3>
                    <p><strong>Date:</strong> {event['date']}</p>
                    <p><strong>Time:</strong> {event['time']}</p>
                    <p><strong>Platform:</strong> {event['platform']}</p>
                    <p>{event['description']}</p>
                    <a href="{event['registration_url']}" class="cta-button">Register Now</a>
                </div>'''
        
        template += '''</div>'''
    
    # Tip of the Month
    tip = content['tips_and_tricks']
    template += f'''
            <div class="section">
                <h2>💡 Tip of the Month</h2>
                <div class="highlight-box">
                    <h3>{tip['title']}</h3>
                    <p>{tip['description']}</p>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto;"><code>{tip['code_example']}</code></pre>
                    <a href="{tip['documentation_url']}" class="cta-button">Read Documentation</a>
                </div>
            </div>'''
    
    # Research Roundup
    research = content['research_roundup']
    template += f'''
            <div class="section">
                <h2>📚 Research & Academic Usage</h2>
                <p>{research['description']}</p>
                
                <h4>Featured Research Topics:</h4>
                <ul class="list-unstyled">'''
    
    for topic in research['featured_topics']:
        template += f'<li>• {topic}</li>'
    
    template += f'''
                </ul>
                
                <div class="highlight-box">
                    <p><strong>Academic Partnership Opportunities:</strong></p>
                    <ul>'''
    
    for opportunity in research['collaboration_opportunities']:
        template += f'<li>{opportunity}</li>'
    
    template += f'''
                    </ul>
                    <p style="margin-top: 15px;">{research['call_to_action']}</p>
                </div>
            </div>'''
    
    # Footer
    template += '''
        </div>
        
        <div class="footer">
            <p><strong>SocialMapper</strong> - Open source spatial analysis for everyone</p>
            <p>
                <a href="https://github.com/mihiarc/socialmapper">View on GitHub</a> | 
                <a href="https://mihiarc.github.io/socialmapper/">Documentation</a> | 
                <a href="https://github.com/mihiarc/socialmapper/discussions">Community Discussions</a>
            </p>
            <p style="margin-top: 20px; font-size: 12px;">
                <a href="{{unsubscribe_url}}">Unsubscribe</a> | 
                <a href="{{preferences_url}}">Email Preferences</a>
            </p>
            <p style="font-size: 12px;">
                Have feedback? <a href="mailto:community@socialmapper.org">Reply to this email</a>
            </p>
        </div>
    </div>
</body>
</html>'''
    
    # Save template
    email_file = output_path / "newsletter_email.html"
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(template)
    
    return str(email_file)

def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(description="Generate SocialMapper newsletter content")
    parser.add_argument("--month", default=datetime.now().strftime('%B'), help="Newsletter month")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Newsletter year")
    parser.add_argument("--output-dir", default="newsletter-content", help="Output directory")
    parser.add_argument("--repo", default="mihiarc/socialmapper", help="GitHub repository")
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"🚀 Generating SocialMapper newsletter for {args.month} {args.year}")
    
    # Initialize collectors and generators
    github_collector = GitHubDataCollector(args.repo)
    content_generator = NewsletterContentGenerator(github_collector)
    
    try:
        # Generate newsletter content
        newsletter_content = content_generator.generate_monthly_content(args.month, args.year)
        
        # Save raw content data
        with open(output_path / "newsletter_data.json", "w") as f:
            json.dump(newsletter_content, f, indent=2)
        print(f"✅ Newsletter data saved to {output_path}/newsletter_data.json")
        
        # Create email template
        email_template_path = create_email_template(newsletter_content, output_path)
        print(f"✅ Email template created: {email_template_path}")
        
        # Create plain text version
        with open(output_path / "newsletter_plain.txt", "w") as f:
            f.write(f"""SOCIALMAPPER INSIGHTS - {newsletter_content['metadata']['month'].upper()} {newsletter_content['metadata']['year']}

Community Growth This Month:
- GitHub Stars: {newsletter_content['stats']['github_stars']}
- New Discussions: {newsletter_content['stats']['total_discussions']}  
- Releases: {newsletter_content['stats']['monthly_releases']}
- Contributors: {newsletter_content['stats']['top_contributors_count']}

""")
            
            if newsletter_content['releases']:
                f.write("PLATFORM UPDATES:\n")
                for release in newsletter_content['releases'][:3]:
                    f.write(f"- {release['title']}: {release['description']}\n")
                    f.write(f"  View: {release['url']}\n\n")
            
            featured = newsletter_content['featured_content']
            if featured['analysis_of_month']:
                analysis = featured['analysis_of_month']
                f.write(f"FEATURED ANALYSIS:\n")
                f.write(f"- {analysis['title']} by {analysis['author']}\n")
                f.write(f"  {analysis['preview']}\n")
                f.write(f"  Read more: {analysis['url']}\n\n")
            
            f.write("COMMUNITY RESOURCES:\n")
            f.write("- Documentation: https://mihiarc.github.io/socialmapper/\n")
            f.write("- Community Discussions: https://github.com/mihiarc/socialmapper/discussions\n")
            f.write("- Examples: https://github.com/mihiarc/socialmapper/tree/main/examples\n\n")
            
            f.write("Questions? Reply to this email or visit our community discussions.")
        
        print(f"✅ Plain text version created: {output_path}/newsletter_plain.txt")
        
        # Create social media posts
        social_posts = {
            "twitter": f"""🏘️ SocialMapper Insights - {args.month} {args.year} is here!

This month's highlights:
📊 {newsletter_content['stats']['github_stars']} GitHub stars
💬 {newsletter_content['stats']['total_discussions']} new community discussions
🚀 {newsletter_content['stats']['monthly_releases']} platform releases
👥 {newsletter_content['stats']['top_contributors_count']} contributors

#SpatialAnalysis #OpenSource #Community #GIS #UrbanPlanning

Full newsletter: [LINK]""",

            "linkedin": f"""📧 Our monthly SocialMapper Insights newsletter for {args.month} {args.year} is now available!

This month we're celebrating:
🌟 {newsletter_content['stats']['github_stars']} GitHub stars - thank you for your support!
💬 {newsletter_content['stats']['total_discussions']} new community discussions across our forum
🚀 {newsletter_content['stats']['monthly_releases']} new platform releases with enhanced features
👥 {newsletter_content['stats']['top_contributors_count']} amazing contributors advancing our open source project

The newsletter features platform updates, community spotlights, upcoming events, and practical tips for spatial accessibility analysis.

Whether you're a researcher, urban planner, policy maker, or developer working with geospatial data, you'll find valuable insights and community connections.

#SpatialAnalysis #UrbanPlanning #OpenSource #GIS #CommunityDevelopment #DataScience #Accessibility"""
        }
        
        for platform, post in social_posts.items():
            with open(output_path / f"social_{platform}.txt", "w") as f:
                f.write(post)
        
        print(f"✅ Social media posts created: {output_path}/")
        
        print("\n🎉 Newsletter generation complete!")
        print("\n📋 Next steps:")
        print(f"1. Review generated content in {output_path}/")
        print("2. Upload HTML template to your email service provider")
        print("3. Schedule email for first Monday of the month")
        print("4. Post social media updates")
        print("5. Update community with newsletter availability")
        
        print(f"\n📊 Content Summary:")
        print(f"- {len(newsletter_content.get('releases', []))} releases featured")
        print(f"- {sum(len(v) for v in newsletter_content.get('discussions', {}).values())} discussions processed")
        print(f"- {len(newsletter_content.get('contributors', []))} contributors highlighted")
        print(f"- {len(newsletter_content.get('upcoming_events', []))} upcoming events listed")
        
    except Exception as e:
        print(f"❌ Error generating newsletter: {e}")
        raise

if __name__ == "__main__":
    import calendar
    main()