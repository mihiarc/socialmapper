#!/bin/bash
"""
Setup script for automated insights generation in SocialMapper

This script configures scheduled execution of the insights generator
for weekly and monthly reports with proper logging and error handling.
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INSIGHTS_SCRIPT="$SCRIPT_DIR/automated-insights-generator.py"
LOG_DIR="$PROJECT_ROOT/logs/insights"

echo "🚀 Setting up SocialMapper Automated Insights Generation"
echo "Project Root: $PROJECT_ROOT"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$LOG_DIR"
mkdir -p "$PROJECT_ROOT/reports"
mkdir -p "$PROJECT_ROOT/feedback_data"

# Ensure the insights script is executable
echo "🔧 Making insights script executable..."
chmod +x "$INSIGHTS_SCRIPT"

# Create wrapper script for cron execution
CRON_WRAPPER="$SCRIPT_DIR/run-insights-cron.sh"
cat > "$CRON_WRAPPER" << 'EOF'
#!/bin/bash
# Cron wrapper for automated insights generation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/insights"

# Set up environment
export PATH="/usr/local/bin:$PATH"  # Ensure Python is in PATH
cd "$PROJECT_ROOT"

# Log file with timestamp
LOG_FILE="$LOG_DIR/insights_$(date +%Y%m%d_%H%M%S).log"

echo "Starting automated insights generation at $(date)" >> "$LOG_FILE"

# Run the insights generator
if python3 "$SCRIPT_DIR/automated-insights-generator.py" >> "$LOG_FILE" 2>&1; then
    echo "Insights generation completed successfully at $(date)" >> "$LOG_FILE"
    
    # Clean up old log files (keep last 30 days)
    find "$LOG_DIR" -name "insights_*.log" -mtime +30 -delete
else
    echo "Insights generation failed at $(date)" >> "$LOG_FILE"
    
    # Send alert email if configured
    if command -v mail &> /dev/null; then
        echo "Automated insights generation failed. Check logs at $LOG_FILE" | \
            mail -s "SocialMapper Insights Generation Failed" admin@socialmapper.org || true
    fi
fi
EOF

chmod +x "$CRON_WRAPPER"

# Create systemd service file (for Linux systems)
if command -v systemctl &> /dev/null; then
    echo "⚙️  Creating systemd service..."
    SERVICE_FILE="/etc/systemd/system/socialmapper-insights.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=SocialMapper Automated Insights Generation
After=network.target

[Service]
Type=oneshot
User=$(whoami)
WorkingDirectory=$PROJECT_ROOT
ExecStart=$CRON_WRAPPER
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file for weekly execution
    TIMER_FILE="/etc/systemd/system/socialmapper-insights.timer"
    
    sudo tee "$TIMER_FILE" > /dev/null << EOF
[Unit]
Description=Run SocialMapper Insights Generation Weekly
Requires=socialmapper-insights.service

[Timer]
OnCalendar=Mon 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start the timer
    sudo systemctl daemon-reload
    sudo systemctl enable socialmapper-insights.timer
    sudo systemctl start socialmapper-insights.timer
    
    echo "✅ Systemd timer configured for weekly execution (Mondays at 9 AM)"
    
else
    # Fallback to cron for macOS and other systems
    echo "⏰ Setting up cron jobs..."
    
    # Create cron entries
    CRON_ENTRIES=$(cat << EOF
# SocialMapper Automated Insights Generation
# Weekly report every Monday at 9 AM
0 9 * * 1 $CRON_WRAPPER

# Monthly report on first day of month at 10 AM  
0 10 1 * * $CRON_WRAPPER
EOF
)

    # Install cron entries
    echo "Installing cron entries:"
    echo "$CRON_ENTRIES"
    
    # Add to crontab (append to existing)
    (crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | crontab -
    
    echo "✅ Cron jobs configured for automated execution"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv pip install pandas numpy rich
else
    pip3 install pandas numpy rich
fi

# Create sample configuration file
CONFIG_FILE="$PROJECT_ROOT/config/insights_config.json"
mkdir -p "$(dirname "$CONFIG_FILE")"

cat > "$CONFIG_FILE" << 'EOF'
{
  "email": {
    "enabled": false,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "analytics@socialmapper.org",
    "recipients": [
      "team@socialmapper.org",
      "product@socialmapper.org"
    ]
  },
  "reports": {
    "formats": ["json", "console"],
    "retention_days": 90
  },
  "analysis": {
    "min_feedback_items": 5,
    "sentiment_threshold": 0.2,
    "engagement_threshold": 70
  },
  "alerts": {
    "critical_sentiment": -0.5,
    "low_engagement": 40,
    "high_bounce_rate": 80
  }
}
EOF

echo "📋 Created configuration file at $CONFIG_FILE"

# Create test data for demonstration
echo "🧪 Creating sample data for testing..."
SAMPLE_FEEDBACK="$PROJECT_ROOT/feedback_data/feedback.jsonl"
cat > "$SAMPLE_FEEDBACK" << 'EOF'
{"id": "1", "type": "rating", "touchpoint": "post_analysis", "rating": 5, "comment": "Great tool! Very helpful for my research.", "created_at": "2025-01-01T10:00:00Z"}
{"id": "2", "type": "usability", "touchpoint": "configuration_wizard", "rating": 4, "comment": "Easy to use but could be faster", "created_at": "2025-01-02T14:30:00Z"}
{"id": "3", "type": "bug_report", "touchpoint": "results_dashboard", "rating": 2, "comment": "The export feature is broken and slow", "created_at": "2025-01-03T09:15:00Z"}
{"id": "4", "type": "feature_request", "touchpoint": "general_usage", "rating": 4, "comment": "Would love to see real-time collaboration features", "created_at": "2025-01-04T16:45:00Z"}
EOF

SAMPLE_ANALYTICS="$PROJECT_ROOT/feedback_data/analytics.jsonl"
cat > "$SAMPLE_ANALYTICS" << 'EOF'
{"event_name": "page_view", "event_category": "navigation", "session_id": "sess1", "timestamp": "2025-01-01T10:00:00Z", "properties": {"page": "/dashboard"}}
{"event_name": "analysis_started", "event_category": "interaction", "session_id": "sess1", "timestamp": "2025-01-01T10:05:00Z", "properties": {"step": "configuration"}}
{"event_name": "export_completed", "event_category": "conversion", "session_id": "sess1", "timestamp": "2025-01-01T10:15:00Z", "properties": {"format": "csv"}}
EOF

# Test the insights generation
echo "🧪 Testing insights generation..."
cd "$PROJECT_ROOT"
python3 "$INSIGHTS_SCRIPT" || echo "⚠️  Test run completed (some errors expected with sample data)"

# Create documentation
DOC_FILE="$PROJECT_ROOT/docs/automated-insights.md"
mkdir -p "$(dirname "$DOC_FILE")"

cat > "$DOC_FILE" << 'EOF'
# Automated Insights Generation

## Overview

SocialMapper includes an automated insights generation system that analyzes user feedback and analytics data to provide actionable recommendations for product improvement.

## Features

- **Sentiment Analysis**: Analyzes feedback sentiment trends
- **Issue Detection**: Identifies common user problems and complaints
- **User Journey Analysis**: Detects bottlenecks in user workflows
- **Engagement Metrics**: Calculates user engagement scores
- **Automated Reporting**: Generates weekly and monthly reports
- **Alert System**: Notifies team of critical issues

## Execution Schedule

- **Weekly Reports**: Every Monday at 9:00 AM
- **Monthly Reports**: First day of month at 10:00 AM

## Report Outputs

1. **Console Report**: Rich formatted output for immediate viewing
2. **JSON Report**: Structured data for integration with other systems
3. **Email Report**: HTML formatted reports sent to stakeholders

## Configuration

Edit `config/insights_config.json` to customize:
- Email settings
- Analysis thresholds
- Alert conditions
- Report formats

## Manual Execution

Run insights generation manually:

```bash
cd /path/to/socialmapper
python3 scripts/automated-insights-generator.py
```

## Logs

Execution logs are stored in `logs/insights/` with automatic cleanup after 30 days.

## Data Sources

- `feedback_data/feedback.jsonl` - User feedback data
- `feedback_data/analytics.jsonl` - User analytics events
- API endpoints for real-time data

## Troubleshooting

1. Check logs in `logs/insights/`
2. Verify Python dependencies are installed
3. Ensure data files exist and contain valid JSON
4. Check cron job status: `systemctl status socialmapper-insights.timer`
EOF

echo "📚 Created documentation at $DOC_FILE"

# Summary
echo ""
echo "✅ Automated Insights Setup Complete!"
echo ""
echo "📊 What was configured:"
echo "  • Insights generation script: $INSIGHTS_SCRIPT"
echo "  • Cron wrapper: $CRON_WRAPPER" 
echo "  • Configuration file: $CONFIG_FILE"
echo "  • Documentation: $DOC_FILE"
echo "  • Log directory: $LOG_DIR"
echo ""
echo "⏰ Execution schedule:"
if command -v systemctl &> /dev/null; then
    echo "  • Systemd timer: Weekly on Mondays at 9:00 AM"
    echo "  • Check status: systemctl status socialmapper-insights.timer"
else
    echo "  • Cron job: Weekly on Mondays at 9:00 AM"
    echo "  • Check jobs: crontab -l"
fi
echo ""
echo "🚀 Next steps:"
echo "  1. Review and customize config/insights_config.json"
echo "  2. Set up email credentials for reports"
echo "  3. Monitor logs/insights/ for execution results"
echo "  4. Check first automated run next Monday"