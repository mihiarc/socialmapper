"""Internal reporting utilities for SocialMapper."""

import logging
from html import escape
from typing import Any

logger = logging.getLogger(__name__)


def create_analysis_report(
    data: dict[str, Any],
    output_format: str = "html",
    template: str = "default",
    include_maps: bool = True,
) -> str | bytes:
    """Generate a formatted report from analysis data.

    Parameters
    ----------
    data : dict
        Analysis results from API functions.
    output_format : str
        Output format ('html' or 'pdf').
    template : str
        Report template name.
    include_maps : bool
        Whether to include map visualizations.

    Returns
    -------
    str or bytes
        HTML string or PDF bytes.
    """
    if template != "default":
        logger.warning(f"Template '{template}' is not supported, using 'default'")
    if not include_maps:
        logger.warning("include_maps=False is not yet supported, maps will be included")

    if output_format == "pdf":
        raise NotImplementedError(
            "PDF report generation is not yet supported. Use output_format='html' instead."
        )

    return _render_html_report(data, template, include_maps)


def _render_html_report(
    data: dict[str, Any],
    template: str,
    include_maps: bool,
) -> str:
    """Render analysis data as an HTML report."""
    sections = []
    sections.append("<html><head><title>SocialMapper Analysis Report</title></head><body>")
    sections.append("<h1>SocialMapper Analysis Report</h1>")

    if "metadata" in data:
        meta = data["metadata"]
        sections.append("<h2>Analysis Parameters</h2><ul>")
        for key, value in meta.items():
            sections.append(f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>")
        sections.append("</ul>")

    if "locations" in data:
        sections.append(f"<h2>Locations Analyzed ({len(data['locations'])})</h2>")
        for loc_data in data["locations"]:
            loc_name = escape(str(loc_data.get("location", "Unknown")))
            sections.append(f"<h3>{loc_name}</h3>")
            if "error" in loc_data:
                sections.append(f"<p class='error'>Error: {escape(str(loc_data['error']))}</p>")
            elif "aggregated" in loc_data:
                sections.append("<table border='1'><tr><th>Variable</th><th>Total</th><th>Mean</th></tr>")
                for var, stats in loc_data["aggregated"].items():
                    total = stats.get("total", "N/A")
                    mean = stats.get("mean", "N/A")
                    if isinstance(mean, float):
                        mean = f"{mean:,.1f}"
                    if isinstance(total, (int, float)):
                        total = f"{total:,.0f}"
                    sections.append(f"<tr><td>{escape(str(var))}</td><td>{escape(str(total))}</td><td>{escape(str(mean))}</td></tr>")
                sections.append("</table>")

    if "comparison" in data:
        sections.append("<h2>Comparison</h2>")
        for var, comp in data["comparison"].items():
            sections.append(f"<h3>{escape(str(var))}</h3>")
            sections.append(f"<p>Highest: {escape(str(comp.get('highest', 'N/A')))}</p>")
            sections.append(f"<p>Lowest: {escape(str(comp.get('lowest', 'N/A')))}</p>")

    if "census_data" in data and isinstance(data["census_data"], dict):
        cd = data["census_data"]
        if hasattr(cd, "data"):
            sections.append(f"<h2>Census Data ({len(cd.data)} block groups)</h2>")

    sections.append("</body></html>")

    logger.info("Generated HTML analysis report")
    return "\n".join(sections)
