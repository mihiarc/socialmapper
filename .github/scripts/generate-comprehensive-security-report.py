#!/usr/bin/env python3
"""
Generate comprehensive security report in HTML and PDF formats.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import base64


class SecurityReportGenerator:
    """Generate comprehensive security reports."""
    
    def __init__(self, input_dir: str, metrics_file: str):
        self.input_dir = Path(input_dir)
        self.metrics = self.load_metrics(metrics_file)
        self.timestamp = datetime.now().isoformat()
    
    def load_metrics(self, metrics_file: str) -> Dict:
        """Load security metrics from JSON file."""
        with open(metrics_file, 'r') as f:
            return json.load(f)
    
    def generate_html_report(self) -> str:
        """Generate HTML security report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocialMapper Security Report - {self.timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header .timestamp {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .score-section {{
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
        }}
        .score-circle {{
            width: 200px;
            height: 200px;
            margin: 0 auto 20px;
            position: relative;
        }}
        .score-value {{
            font-size: 4em;
            font-weight: bold;
            color: {self.get_score_color()};
        }}
        .score-label {{
            font-size: 1.2em;
            color: #666;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .critical {{ color: #dc3545; }}
        .high {{ color: #fd7e14; }}
        .medium {{ color: #ffc107; }}
        .low {{ color: #28a745; }}
        .details-section {{
            padding: 40px;
        }}
        .details-section h2 {{
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .category-list {{
            list-style: none;
        }}
        .category-item {{
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .category-name {{
            font-weight: 500;
        }}
        .category-count {{
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        .tools-section {{
            padding: 40px;
            background: #f8f9fa;
        }}
        .tool-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .tool-name {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .tool-metrics {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .tool-metric {{
            flex: 1;
            min-width: 100px;
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .recommendations {{
            padding: 40px;
        }}
        .recommendation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        .footer {{
            background: #333;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 SocialMapper Security Report</h1>
            <div class="timestamp">Generated: {self.timestamp}</div>
        </div>
        
        <div class="score-section">
            <div class="score-circle">
                <svg viewBox="0 0 200 200">
                    <circle cx="100" cy="100" r="90" fill="none" stroke="#e0e0e0" stroke-width="20"/>
                    <circle cx="100" cy="100" r="90" fill="none" stroke="{self.get_score_color()}" 
                            stroke-width="20" stroke-dasharray="{self.get_score_dasharray()}" 
                            stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
                    <div class="score-value">{self.metrics.get('security_score', 0)}</div>
                    <div class="score-label">Security Score</div>
                </div>
            </div>
            <h2>{self.get_score_grade()}</h2>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Issues</div>
                <div class="metric-value">{self.metrics.get('total_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Critical</div>
                <div class="metric-value critical">{self.metrics.get('critical_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">High</div>
                <div class="metric-value high">{self.metrics.get('high_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Medium</div>
                <div class="metric-value medium">{self.metrics.get('medium_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Low</div>
                <div class="metric-value low">{self.metrics.get('low_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Vulnerabilities</div>
                <div class="metric-value">{self.metrics.get('vulnerabilities', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Secrets Detected</div>
                <div class="metric-value">{self.metrics.get('secrets', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">License Issues</div>
                <div class="metric-value">{self.metrics.get('license_issues', 0)}</div>
            </div>
        </div>
        
        <div class="details-section">
            <h2>Issues by Category</h2>
            <ul class="category-list">
                {self.generate_category_list()}
            </ul>
        </div>
        
        <div class="tools-section">
            <h2>Security Tools Results</h2>
            {self.generate_tools_section()}
        </div>
        
        <div class="recommendations">
            <h2>Recommendations</h2>
            {self.generate_recommendations()}
        </div>
        
        <div class="footer">
            <p>SocialMapper Security Report | Generated by CI/CD Pipeline</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def get_score_color(self) -> str:
        """Get color based on security score."""
        score = self.metrics.get('security_score', 0)
        if score >= 90:
            return '#28a745'
        elif score >= 70:
            return '#ffc107'
        elif score >= 50:
            return '#fd7e14'
        return '#dc3545'
    
    def get_score_dasharray(self) -> str:
        """Calculate SVG dasharray for score circle."""
        score = self.metrics.get('security_score', 0)
        circumference = 2 * 3.14159 * 90
        filled = (score / 100) * circumference
        return f"{filled} {circumference}"
    
    def get_score_grade(self) -> str:
        """Get grade based on security score."""
        score = self.metrics.get('security_score', 0)
        if score >= 90:
            return "Excellent Security Posture"
        elif score >= 70:
            return "Good Security Posture"
        elif score >= 50:
            return "Fair Security Posture - Improvements Needed"
        return "Poor Security Posture - Immediate Action Required"
    
    def generate_category_list(self) -> str:
        """Generate HTML for category list."""
        categories = self.metrics.get('categories', {})
        if not categories:
            return '<li class="category-item">No issues found</li>'
        
        html = ''
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            html += f'''
                <li class="category-item">
                    <span class="category-name">{category.replace('-', ' ').title()}</span>
                    <span class="category-count">{count}</span>
                </li>
            '''
        return html
    
    def generate_tools_section(self) -> str:
        """Generate HTML for tools section."""
        tools = self.metrics.get('tools', {})
        if not tools:
            return '<p>No security tools results available</p>'
        
        html = ''
        for tool, results in tools.items():
            html += f'''
                <div class="tool-card">
                    <div class="tool-name">{tool.title()}</div>
                    <div class="tool-metrics">
            '''
            for severity, count in results.items():
                severity_class = severity if severity in ['critical', 'high', 'medium', 'low'] else ''
                html += f'''
                    <div class="tool-metric">
                        <div class="{severity_class}">{count}</div>
                        <div>{severity.title()}</div>
                    </div>
                '''
            html += '''
                    </div>
                </div>
            '''
        return html
    
    def generate_recommendations(self) -> str:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        if self.metrics.get('critical_issues', 0) > 0:
            recommendations.append({
                'priority': 'Critical',
                'text': f"Address {self.metrics['critical_issues']} critical security issues immediately. These pose immediate risk to the application."
            })
        
        if self.metrics.get('secrets', 0) > 0:
            recommendations.append({
                'priority': 'Critical',
                'text': f"Remove {self.metrics['secrets']} detected secrets from the codebase and rotate affected credentials."
            })
        
        if self.metrics.get('high_issues', 0) > 5:
            recommendations.append({
                'priority': 'High',
                'text': "Prioritize fixing high-severity issues in the next sprint."
            })
        
        if self.metrics.get('dependency_issues', 0) > 0:
            recommendations.append({
                'priority': 'Medium',
                'text': "Update dependencies to patch known vulnerabilities."
            })
        
        if self.metrics.get('container_issues', 0) > 0:
            recommendations.append({
                'priority': 'Medium',
                'text': "Review and update container base images to address security issues."
            })
        
        if not recommendations:
            recommendations.append({
                'priority': 'Info',
                'text': "Continue regular security scanning and maintain security best practices."
            })
        
        html = ''
        for rec in recommendations:
            html += f'''
                <div class="recommendation">
                    <strong>[{rec['priority']}]</strong> {rec['text']}
                </div>
            '''
        return html
    
    def save_html_report(self, output_file: str):
        """Save HTML report to file."""
        html = self.generate_html_report()
        with open(output_file, 'w') as f:
            f.write(html)
    
    def save_pdf_report(self, output_file: str):
        """Save PDF report (requires additional libraries)."""
        # Note: This would require wkhtmltopdf or similar tool
        # For now, we'll create a simple text version
        pdf_content = f"""
SOCIALMAPPER SECURITY REPORT
Generated: {self.timestamp}

SECURITY SCORE: {self.metrics.get('security_score', 0)}/100

ISSUE SUMMARY:
- Total Issues: {self.metrics.get('total_issues', 0)}
- Critical: {self.metrics.get('critical_issues', 0)}
- High: {self.metrics.get('high_issues', 0)}
- Medium: {self.metrics.get('medium_issues', 0)}
- Low: {self.metrics.get('low_issues', 0)}

SECURITY METRICS:
- Vulnerabilities: {self.metrics.get('vulnerabilities', 0)}
- Secrets Detected: {self.metrics.get('secrets', 0)}
- License Issues: {self.metrics.get('license_issues', 0)}
- Compliance Violations: {self.metrics.get('compliance_violations', 0)}

For detailed report, please refer to the HTML version.
"""
        with open(output_file, 'w') as f:
            f.write(pdf_content)


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive security report')
    parser.add_argument('--input-dir', required=True, help='Directory containing security reports')
    parser.add_argument('--metrics-file', required=True, help='Security metrics JSON file')
    parser.add_argument('--output-html', required=True, help='Output HTML report file')
    parser.add_argument('--output-pdf', required=True, help='Output PDF report file')
    
    args = parser.parse_args()
    
    generator = SecurityReportGenerator(args.input_dir, args.metrics_file)
    generator.save_html_report(args.output_html)
    generator.save_pdf_report(args.output_pdf)
    
    print(f"Security reports generated:")
    print(f"  HTML: {args.output_html}")
    print(f"  PDF: {args.output_pdf}")


if __name__ == '__main__':
    main()