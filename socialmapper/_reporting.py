"""Internal reporting utilities for SocialMapper."""

import json
import logging
import html
from typing import Dict, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def create_analysis_report(
    analysis_data: Dict[str, Any],
    format: str,
    template: str,
    include_maps: bool
) -> Union[str, bytes]:
    """Create an analysis report from data.

    Args:
        analysis_data: Analysis results
        format: Output format (html or pdf)
        template: Report template
        include_maps: Whether to include maps

    Returns
    -------
        HTML string or PDF bytes
    """
    if format not in ["html", "pdf"]:
        raise ValueError(f"Format must be 'html' or 'pdf', got '{format}'")

    # Generate HTML content
    html_content = generate_html_report(analysis_data, template, include_maps)

    if format == "html":
        return html_content
    else:
        # Convert HTML to PDF
        return convert_html_to_pdf(html_content)


def generate_html_report(
    data: Dict[str, Any],
    template: str,
    include_maps: bool
) -> str:
    """Generate HTML report content."""
    # Extract components
    isochrone = data.get("isochrone")
    census_data = data.get("census_data", {})
    pois = data.get("pois", [])
    metadata = data.get("metadata", {})

    # Calculate statistics
    stats = calculate_statistics(census_data)

    # Build HTML
    html_str = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SocialMapper Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .timestamp {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SocialMapper Analysis Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
"""

    # Location Information
    if isochrone:
        # Escape user-provided data to prevent XSS
        location = html.escape(str(isochrone['properties']['location']))
        travel_time = int(isochrone['properties']['travel_time'])
        travel_mode = html.escape(str(isochrone['properties']['travel_mode']).title())
        area = float(isochrone['properties']['area_sq_km'])

        html_str += f"""
    <div class="section">
        <h2>Location Analysis</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{location}</div>
                <div class="stat-label">Location</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{travel_time} min</div>
                <div class="stat-label">Travel Time</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{travel_mode}</div>
                <div class="stat-label">Travel Mode</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{area:.1f} km²</div>
                <div class="stat-label">Coverage Area</div>
            </div>
        </div>
    </div>
"""

    # Census Data Statistics
    if census_data and stats:
        html_str += f"""
    <div class="section">
        <h2>Demographic Statistics</h2>
        <div class="stats-grid">
"""
        for key, value in stats.items():
            if value is not None:
                label = key.replace('_', ' ').title()
                if isinstance(value, (int, float)):
                    if value > 1000000:
                        display_value = f"{value/1000000:.1f}M"
                    elif value > 1000:
                        display_value = f"{value/1000:.1f}K"
                    else:
                        display_value = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
                else:
                    display_value = str(value)

                # Escape labels to prevent XSS
                escaped_label = html.escape(label)
                escaped_value = html.escape(str(display_value))
                html_str += f"""
            <div class="stat-card">
                <div class="stat-value">{escaped_value}</div>
                <div class="stat-label">{escaped_label}</div>
            </div>
"""
        html_str += """
        </div>
    </div>
"""

    # Census Block Groups Table
    if census_data:
        html_str += """
    <div class="section">
        <h2>Census Block Groups</h2>
        <table>
            <thead>
                <tr>
                    <th>GEOID</th>
"""
        # Add column headers for each variable
        if census_data:
            first_geoid = next(iter(census_data.keys()))
            for var in census_data[first_geoid].keys():
                html_str += f"                    <th>{var.replace('_', ' ').title()}</th>\n"
        html_str += """                </tr>
            </thead>
            <tbody>
"""
        # Add data rows (limit to first 20 for readability)
        for i, (geoid, data) in enumerate(census_data.items()):
            if i >= 20:
                html_str += f"""
                <tr>
                    <td colspan="100%" style="text-align: center; font-style: italic;">
                        ... and {len(census_data) - 20} more block groups
                    </td>
                </tr>
"""
                break

            # Escape GEOID to prevent XSS
            escaped_geoid = html.escape(str(geoid))
            html_str += f"                <tr>\n                    <td>{escaped_geoid}</td>\n"
            for value in data.values():
                if isinstance(value, (int, float)):
                    display_val = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
                else:
                    display_val = html.escape(str(value)) if value is not None else "N/A"
                html_str += f"                    <td>{display_val}</td>\n"
            html_str += "                </tr>\n"

        html_str += """            </tbody>
        </table>
    </div>
"""

    # POIs section
    if pois:
        html_str += f"""
    <div class="section">
        <h2>Points of Interest</h2>
        <p>Found {len(pois)} POIs in the analysis area</p>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Distance (km)</th>
                </tr>
            </thead>
            <tbody>
"""
        for poi in pois[:20]:  # Limit to first 20
            # Escape POI data to prevent XSS
            poi_name = html.escape(str(poi.get('name', 'Unknown')))
            poi_type = html.escape(str(poi.get('type', 'Unknown')))
            distance = poi.get('distance_km', 0)
            html_str += f"""
                <tr>
                    <td>{poi_name}</td>
                    <td>{poi_type}</td>
                    <td>{distance:.2f}</td>
                </tr>
"""
        if len(pois) > 20:
            html_str += f"""
                <tr>
                    <td colspan="3" style="text-align: center; font-style: italic;">
                        ... and {len(pois) - 20} more POIs
                    </td>
                </tr>
"""
        html_str += """            </tbody>
        </table>
    </div>
"""

    # Footer
    html_str += """
    <div class="footer">
        <p>Generated by SocialMapper API</p>
    </div>
</body>
</html>
"""

    return html_str


def calculate_statistics(census_data: Dict[str, Dict]) -> Dict[str, Any]:
    """Calculate aggregate statistics from census data."""
    if not census_data:
        return {}

    stats = {}
    # Collect all variables
    all_vars = set()
    for data in census_data.values():
        all_vars.update(data.keys())

    for var in all_vars:
        values = []
        for data in census_data.values():
            if var in data and data[var] is not None:
                values.append(data[var])

        if values:
            if all(isinstance(v, (int, float)) for v in values):
                # Numeric variable
                if 'population' in var.lower() or 'count' in var.lower():
                    stats[f"total_{var}"] = sum(values)
                else:
                    stats[f"avg_{var}"] = sum(values) / len(values)

    stats["block_group_count"] = len(census_data)
    return stats


def convert_html_to_pdf(html_content: str) -> bytes:
    """Convert HTML to PDF (simplified version)."""
    # This is a simplified implementation
    # In production, you would use a library like weasyprint or pdfkit
    logger.warning("PDF generation not fully implemented. Returning HTML as bytes.")
    return html_content.encode('utf-8')