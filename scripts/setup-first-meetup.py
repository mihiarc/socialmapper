#!/usr/bin/env python3
"""
SocialMapper First Monthly Meetup Setup Script

This script helps set up the inaugural monthly community meetup by:
1. Creating calendar events and reminders
2. Generating registration templates
3. Setting up initial content and speakers
4. Creating promotional materials

Usage:
    python scripts/setup-first-meetup.py --date "2025-09-04" --time "14:00" --timezone "EST"
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import calendar

def generate_meetup_details(date_str: str, time_str: str, timezone: str) -> Dict[str, Any]:
    """Generate comprehensive meetup details for the first event."""
    
    # Parse the date and time
    meetup_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    # Calculate registration timeline
    registration_open = meetup_date - timedelta(weeks=3)
    week_reminder = meetup_date - timedelta(weeks=1)
    day_reminder = meetup_date - timedelta(days=1)
    hour_reminder = meetup_date - timedelta(hours=1)
    
    return {
        "event_details": {
            "title": "SocialMapper Community Meetup #1: Welcome & Getting Started",
            "date": date_str,
            "time": time_str,
            "timezone": timezone,
            "duration_minutes": 60,
            "platform": "Zoom Professional",
            "max_participants": 100,
            "registration_required": True
        },
        "timeline": {
            "registration_opens": registration_open.strftime("%Y-%m-%d"),
            "one_week_reminder": week_reminder.strftime("%Y-%m-%d"),
            "one_day_reminder": day_reminder.strftime("%Y-%m-%d"),
            "one_hour_reminder": hour_reminder.strftime("%Y-%m-%d %H:%M")
        },
        "agenda": {
            "welcome_and_updates": {
                "duration_minutes": 10,
                "presenter": "SocialMapper Maintainers",
                "topics": [
                    "Community launch and vision",
                    "Platform overview and recent updates",
                    "Community statistics and growth goals",
                    "Introduction to discussion categories and resources"
                ]
            },
            "featured_presentation": {
                "duration_minutes": 20,
                "presenter": "Community Member or Maintainer",
                "title": "Real-World Applications of Spatial Accessibility Analysis",
                "topics": [
                    "Case study: Library access analysis",
                    "Methodology walkthrough",
                    "Insights and policy implications",
                    "Q&A with audience"
                ]
            },
            "live_demo": {
                "duration_minutes": 20,
                "presenter": "SocialMapper Team",
                "title": "Getting Started with SocialMapper: From Installation to First Analysis",
                "topics": [
                    "Installation and setup",
                    "Basic POI discovery workflow",
                    "Generating your first accessibility map",
                    "Exporting results and next steps"
                ]
            },
            "community_qa": {
                "duration_minutes": 10,
                "format": "Open discussion",
                "topics": [
                    "Community questions and feedback",
                    "Feature requests and roadmap input",
                    "Upcoming meetup topics and speakers",
                    "Collaboration and networking opportunities"
                ]
            }
        }
    }

def create_eventbrite_description(meetup_details: Dict[str, Any]) -> str:
    """Generate Eventbrite event description."""
    
    description = f"""
🏘️ **Join the SocialMapper Community for our inaugural monthly meetup!**

## About This Meetup

Welcome to the first SocialMapper Community Virtual Meetup! This is your opportunity to connect with researchers, planners, developers, and data enthusiasts who are passionate about spatial accessibility analysis and demographic mapping.

## What to Expect

### 🎯 Welcome & Community Updates (10 minutes)
- Community launch celebration and vision
- Platform overview and latest feature updates  
- Introduction to community resources and discussion categories
- Growth goals and exciting opportunities ahead

### 📊 Featured Presentation: "Real-World Applications of Spatial Accessibility Analysis" (20 minutes)
Join us for an in-depth case study demonstrating how SocialMapper can reveal important insights about community access to essential services. We'll walk through:
- Complete analysis methodology from start to finish
- Real-world policy implications and decision-making impact
- Interactive Q&A session with the presenter
- Best practices for conducting similar analyses

### 💻 Live Demo: "Getting Started with SocialMapper" (20 minutes)
Perfect for newcomers and those wanting to refresh their skills:
- Step-by-step installation and configuration
- Your first POI discovery analysis
- Generating accessibility maps and isochrones
- Data export options and visualization tips
- Common troubleshooting and optimization techniques

### 🤝 Community Q&A & Networking (10 minutes)
- Open discussion and questions from attendees
- Feature requests and roadmap input
- Collaboration opportunities and introductions
- Preview of next month's topics and themes

## Who Should Attend

- **Researchers** using spatial analysis for academic work
- **Urban planners** analyzing accessibility and equity
- **Policy makers** making data-driven community decisions
- **Developers** building applications with geospatial data
- **Students** learning spatial analysis and GIS techniques
- **Community advocates** working on accessibility issues
- **Anyone curious** about spatial analysis and demographic mapping

## What You'll Learn

By the end of this meetup, you'll:
- Understand the SocialMapper community resources and support system
- Know how to perform basic spatial accessibility analysis
- Have seen real-world applications and use cases
- Be connected with other community members and experts
- Know how to get help and contribute to the community
- Have ideas for your own analyses and research projects

## Prerequisites

- **No experience required!** We welcome all skill levels
- Internet connection for video conferencing
- Optional: Python installed if you want to follow along with demos
- Curiosity about spatial analysis and community data

## Registration Information

- **Cost**: Free for all community members
- **Platform**: Zoom (link provided after registration)  
- **Recording**: Session will be recorded and shared with community
- **Materials**: Presentation slides and demo code shared via GitHub
- **Capacity**: Limited to 100 participants (register early!)

## After the Meetup

- **Recording**: Available within 24 hours on our YouTube channel
- **Resources**: All materials shared in community GitHub repository
- **Discussion**: Continue conversations in GitHub Discussions
- **Follow-up**: Optional office hours for additional questions
- **Next Steps**: Get involved in community showcases and contributions

## Technical Requirements

- Computer with internet connection and web browser
- Audio capability (speakers/headphones recommended)
- Optional: Microphone for participation in Q&A
- Optional: Python environment for following along with demos

## Community Guidelines

Please review our [Community Guidelines](https://github.com/mihiarc/socialmapper/blob/main/.github/COMMUNITY_GUIDELINES.md) before attending. We're committed to creating a welcoming, inclusive environment for all participants.

## Questions?

- Check our [FAQ](https://mihiarc.github.io/socialmapper/faq/)
- Post in [GitHub Discussions](https://github.com/mihiarc/socialmapper/discussions)
- Email: community@socialmapper.org (coming soon)

## Stay Connected

- 📧 **Newsletter**: Monthly updates and community highlights
- 💬 **GitHub Discussions**: Ongoing community conversations  
- 📺 **YouTube**: Recorded sessions and tutorials
- 🗓️ **Monthly Meetups**: First Thursday of every month

---

**We're excited to meet you and welcome you to the SocialMapper community!** 

This is just the beginning of what we hope will be a vibrant, collaborative community advancing spatial analysis and making geospatial insights accessible to everyone.

*See you there!* 🚀

---

*Event organized by the SocialMapper maintainers and community volunteers. For accessibility accommodations or special requirements, please contact us at registration or via GitHub Discussions.*
"""
    
    return description.strip()

def create_github_announcement(meetup_details: Dict[str, Any]) -> str:
    """Generate GitHub announcement post for the meetup."""
    
    event = meetup_details["event_details"]
    timeline = meetup_details["timeline"]
    
    announcement = f"""
# 🗓️ First SocialMapper Community Meetup - {event["date"]}!

## We're launching our monthly meetup series!

Join us for the **inaugural SocialMapper Community Virtual Meetup** on **{event["date"]} at {event["time"]} {event["timezone"]}**.

### 📅 Event Details
- **Date & Time**: {event["date"]} at {event["time"]} {event["timezone"]}
- **Duration**: {event["duration_minutes"]} minutes
- **Platform**: {event["platform"]}
- **Capacity**: {event["max_participants"]} participants
- **Cost**: Free for all community members
- **Registration**: Required (link coming soon!)

### 🎯 What We'll Cover

#### Welcome & Community Updates (10 min)
- Community launch celebration
- Platform updates and new features
- Community resources tour
- Growth goals and opportunities

#### Featured Presentation: Real-World Applications (20 min)  
- In-depth spatial accessibility case study
- Complete methodology walkthrough
- Policy implications and real-world impact
- Interactive Q&A session

#### Live Demo: Getting Started (20 min)
- Installation and setup walkthrough
- First POI discovery analysis
- Map generation and visualization
- Export options and best practices

#### Community Q&A & Networking (10 min)
- Open questions and discussion
- Feature requests and roadmap input
- Collaboration opportunities
- Next month's preview

### 🎯 Who Should Attend

Perfect for:
- **New users** wanting to get started with SocialMapper
- **Experienced users** looking to connect with the community  
- **Researchers** using spatial analysis in their work
- **Planners and policy makers** analyzing accessibility
- **Developers** building with geospatial data
- **Students** learning spatial analysis techniques

### ✅ How to Prepare

**No experience required!** But optionally:
- [ ] Install SocialMapper: `pip install socialmapper`
- [ ] Get a Census API key: https://api.census.gov/data/key_signup.html
- [ ] Browse our [documentation](https://mihiarc.github.io/socialmapper/)
- [ ] Check out [example analyses](https://github.com/mihiarc/socialmapper/tree/main/examples)

### 📝 Registration Timeline

- **{timeline["registration_opens"]}**: Registration opens
- **{timeline["one_week_reminder"]}**: One week reminder sent  
- **{timeline["one_day_reminder"]}**: Final reminder and prep materials
- **{timeline["one_hour_reminder"]}**: Meeting link and last-minute details

### 🎤 Want to Present Next Month?

We're already planning future meetups! If you have:
- An interesting SocialMapper analysis or use case
- A tutorial or technique to share
- A research project using spatial accessibility

Post in [Show & Tell](https://github.com/mihiarc/socialmapper/discussions/categories/show-tell) or comment below!

### 📺 Can't Attend Live?

- All sessions will be **recorded** and available within 24 hours
- **Materials shared** via GitHub (slides, code, datasets)
- **Follow-up discussions** in this thread and community forums
- **Office hours** available for additional questions

### 🤝 Community Building Goals

This meetup series is designed to:
- Build connections between community members
- Share knowledge and best practices
- Showcase real-world applications and impact
- Gather feedback for platform development
- Support learning and skill development
- Foster collaboration and partnerships

### 🗓️ Future Meetups

Mark your calendars! We'll meet monthly on the **first Thursday** of each month:
- **October**: Advanced techniques and optimization
- **November**: Academic research showcase
- **December**: Year in review and 2026 roadmap

### ❓ Questions?

Comment below or:
- Post in [General Q&A](https://github.com/mihiarc/socialmapper/discussions/categories/general-q-a)
- Check our [FAQ](https://mihiarc.github.io/socialmapper/faq/)
- Review [Community Guidelines](https://github.com/mihiarc/socialmapper/blob/main/.github/COMMUNITY_GUIDELINES.md)

---

**Registration link coming soon!** 🎟️

We're finalizing the Eventbrite setup and will update this post with the registration link within 24 hours.

**This is the beginning of something exciting!** We can't wait to meet the amazing community we're building together.

See you there! 🚀

---

*Reply to this post to let us know you're planning to attend and what you're most excited to learn!*
"""
    
    return announcement.strip()

def create_email_templates(meetup_details: Dict[str, Any]) -> Dict[str, str]:
    """Generate email templates for the meetup series."""
    
    templates = {}
    
    # Registration confirmation email
    templates["registration_confirmation"] = f"""
Subject: You're registered for SocialMapper Community Meetup #1! 🎉

Hi [Name],

Thanks for registering for our first SocialMapper Community Meetup! We're excited to meet you and welcome you to our community.

## Event Details
- **Date**: {meetup_details['event_details']['date']}
- **Time**: {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']}
- **Duration**: {meetup_details['event_details']['duration_minutes']} minutes
- **Platform**: Zoom (link will be sent 24 hours before the event)

## What to Expect
This inaugural meetup will cover:
- Community welcome and platform overview
- Real-world spatial accessibility case study
- Getting started demo and tutorial
- Q&A and networking opportunities

## Optional Preparation
While no preparation is required, you might enjoy:
- Browsing our documentation: https://mihiarc.github.io/socialmapper/
- Installing SocialMapper: `pip install socialmapper`
- Reviewing example analyses: https://github.com/mihiarc/socialmapper/tree/main/examples

## Important Reminders
- We'll send the Zoom link 24 hours before the event
- The session will be recorded and shared with the community
- All materials (slides, code) will be available on GitHub
- Questions are welcome via chat or microphone during Q&A

## Stay Connected
- GitHub Discussions: https://github.com/mihiarc/socialmapper/discussions
- Documentation: https://mihiarc.github.io/socialmapper/
- Monthly newsletter signup coming soon!

Questions? Reply to this email or post in our GitHub Discussions.

Looking forward to meeting you!

The SocialMapper Team
"""
    
    # One week reminder email
    templates["one_week_reminder"] = f"""
Subject: SocialMapper Meetup #1 is next week - Prep materials enclosed! 📚

Hi [Name],

Our first SocialMapper Community Meetup is next week! Here's everything you need to know:

## Meetup Details
- **Date**: {meetup_details['event_details']['date']} 
- **Time**: {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']}
- **Platform**: Zoom (link coming in 24 hours)

## This Week's Agenda
1. **Community Welcome** - Meet the team and community
2. **Featured Analysis** - Real-world accessibility case study  
3. **Live Demo** - Getting started tutorial
4. **Q&A** - Your questions answered

## Optional Preparation
To get the most from our demo session:

### Install SocialMapper
```bash
pip install socialmapper
```

### Get a Census API Key (free)
1. Visit: https://api.census.gov/data/key_signup.html
2. Sign up for a free key
3. Save it as environment variable: `CENSUS_API_KEY=your_key_here`

### Browse Examples
Check out real analyses: https://github.com/mihiarc/socialmapper/tree/main/examples

## Submit Questions in Advance
Have specific questions? Submit them here: [Meetup #1 Q&A Thread]

## Can't Attend Live?
- Recording will be available within 24 hours
- All materials shared on GitHub
- Follow-up discussion thread for questions
- Optional office hours the following week

We're looking forward to seeing you next week!

Best regards,
The SocialMapper Team
"""
    
    # Day before reminder email  
    templates["day_before_reminder"] = f"""
Subject: Tomorrow: SocialMapper Meetup #1 + Zoom Link 🔗

Hi [Name],

Tomorrow is our first SocialMapper Community Meetup! Here's your Zoom link and final details:

## Join Information
- **Zoom Link**: [ZOOM_LINK_HERE]
- **Meeting ID**: [MEETING_ID]  
- **Passcode**: [PASSCODE]
- **Time**: {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']} (that's in [LOCAL_TIME_CONVERSION])

## Final Agenda
- **2:00-2:10 PM**: Welcome & Community Updates
- **2:10-2:30 PM**: Featured Analysis Presentation  
- **2:30-2:50 PM**: Live Demo - Getting Started with SocialMapper
- **2:50-3:00 PM**: Community Q&A & Networking

## Technical Check
- Test your audio/video: https://zoom.us/test
- Join 5 minutes early for technical setup
- Have questions ready for our Q&A session
- Follow-along materials: https://github.com/mihiarc/socialmapper/tree/main/examples

## Community Guidelines
Please review our guidelines: https://github.com/mihiarc/socialmapper/blob/main/.github/COMMUNITY_GUIDELINES.md

We aim to create a welcoming, educational environment for all skill levels!

## Excited to Meet You!
This is the launch of something special - a collaborative community advancing spatial analysis and accessibility research.

Questions? Reply to this email or join a few minutes early tomorrow.

See you tomorrow!
The SocialMapper Team

---
Can't make it? The recording will be available at: https://youtube.com/@socialmapper
"""
    
    return templates

def create_social_media_posts(meetup_details: Dict[str, Any]) -> Dict[str, str]:
    """Generate social media promotional posts."""
    
    posts = {}
    
    # Twitter/X announcement
    posts["twitter_announcement"] = f"""
🏘️ Exciting news! We're launching monthly SocialMapper Community Meetups!

📅 First meetup: {meetup_details['event_details']['date']}
🕐 Time: {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']}
💻 Platform: Virtual (Zoom)
💰 Cost: FREE

Topics:
✅ Getting started demo
✅ Real-world case study  
✅ Community Q&A
✅ Networking

Perfect for researchers, planners, developers & students interested in spatial accessibility analysis!

Registration: [LINK]

#SpatialAnalysis #GIS #OpenSource #Community #UrbanPlanning #DataScience

🧵 1/3
"""
    
    # LinkedIn announcement
    posts["linkedin_announcement"] = f"""
🎉 We're thrilled to announce the launch of monthly SocialMapper Community Virtual Meetups!

Join us for our inaugural session on {meetup_details['event_details']['date']} at {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']}.

🎯 Who should attend:
• Urban planners analyzing accessibility and equity
• Researchers conducting spatial analysis
• Policy makers using data for community decisions  
• Developers working with geospatial data
• Students learning GIS and spatial analysis
• Anyone curious about demographic mapping

📋 What we'll cover:
• Real-world spatial accessibility case study
• Getting started tutorial (perfect for newcomers)
• Community resources and support systems
• Q&A with experts and networking opportunities

This is completely FREE and designed for all skill levels. Whether you're just getting started or you're an experienced practitioner, you'll find value in connecting with our growing community.

The session will be recorded and all materials shared for those who can't attend live.

Registration link in comments! 👇

#UrbanPlanning #SpatialAnalysis #GIS #CommunityDevelopment #DataScience #OpenSource #Accessibility #Demographics
"""
    
    # Reddit post for relevant communities
    posts["reddit_announcement"] = f"""
Title: [Event] Free Virtual Meetup: Getting Started with Spatial Accessibility Analysis

Hi r/GIS community!

I wanted to share an upcoming virtual meetup that might interest folks here. We're launching monthly SocialMapper Community Meetups - the first one is {meetup_details['event_details']['date']} at {meetup_details['event_details']['time']} {meetup_details['event_details']['timezone']}.

**What is SocialMapper?**
It's an open-source Python toolkit for spatial analysis that bridges OpenStreetMap POI data with US Census demographics. Think: "How many people can reach the nearest library within a 15-minute walk?" with full demographic breakdowns.

**What we'll cover in Meetup #1:**
- Real-world case study walkthrough (methodology → insights → policy impact)
- Live demo: Installation to first analysis in 20 minutes
- Community Q&A and networking

**Who might find this useful:**
- Urban planners working on accessibility and equity
- Researchers doing spatial analysis
- Anyone curious about demographic mapping
- Python developers working with geospatial data

It's completely free, beginner-friendly, and will be recorded. All materials shared on GitHub.

**Registration:** [Link in profile - not posting direct link to avoid spam filter]

Happy to answer questions in comments! 

Mods: Let me know if this isn't appropriate for the community - I'm genuinely trying to share something valuable for folks doing spatial analysis work.
"""
    
    return posts

def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(description="Setup first SocialMapper Community Meetup")
    parser.add_argument("--date", default="2025-09-04", help="Meetup date (YYYY-MM-DD)")
    parser.add_argument("--time", default="14:00", help="Meetup time (HH:MM in 24-hour format)")
    parser.add_argument("--timezone", default="EST", help="Timezone")
    parser.add_argument("--output-dir", default="meetup-materials", help="Output directory for generated materials")
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"🚀 Setting up SocialMapper Community Meetup #1 for {args.date} at {args.time} {args.timezone}")
    
    # Generate meetup details
    meetup_details = generate_meetup_details(args.date, args.time, args.timezone)
    
    # Save meetup details
    with open(output_path / "meetup_details.json", "w") as f:
        json.dump(meetup_details, f, indent=2)
    print(f"✅ Meetup details saved to {output_path}/meetup_details.json")
    
    # Generate Eventbrite description
    eventbrite_description = create_eventbrite_description(meetup_details)
    with open(output_path / "eventbrite_description.md", "w") as f:
        f.write(eventbrite_description)
    print(f"✅ Eventbrite description saved to {output_path}/eventbrite_description.md")
    
    # Generate GitHub announcement
    github_announcement = create_github_announcement(meetup_details)
    with open(output_path / "github_announcement.md", "w") as f:
        f.write(github_announcement)
    print(f"✅ GitHub announcement saved to {output_path}/github_announcement.md")
    
    # Generate email templates
    email_templates = create_email_templates(meetup_details)
    for template_name, template_content in email_templates.items():
        with open(output_path / f"email_{template_name}.txt", "w") as f:
            f.write(template_content)
    print(f"✅ Email templates saved to {output_path}/")
    
    # Generate social media posts
    social_posts = create_social_media_posts(meetup_details)
    for platform, post_content in social_posts.items():
        with open(output_path / f"social_{platform}.txt", "w") as f:
            f.write(post_content)
    print(f"✅ Social media posts saved to {output_path}/")
    
    print("\n🎉 Meetup setup complete!")
    print("\n📋 Next steps:")
    print("1. Review generated materials in", output_path)
    print("2. Set up Eventbrite event using the description")
    print("3. Post GitHub announcement in Discussions")
    print("4. Configure email automation with templates")
    print("5. Schedule social media posts")
    print("6. Set up Zoom meeting and configure settings")
    
    print(f"\n📅 Timeline reminders:")
    print(f"- Registration opens: {meetup_details['timeline']['registration_opens']}")  
    print(f"- One week reminder: {meetup_details['timeline']['one_week_reminder']}")
    print(f"- Day before reminder: {meetup_details['timeline']['one_day_reminder']}")
    print(f"- Meetup day: {args.date} at {args.time} {args.timezone}")

if __name__ == "__main__":
    main()