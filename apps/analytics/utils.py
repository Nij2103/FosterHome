"""
apps.analytics.utils

Utilities for Matplotlib SVG in-memory rendering via BytesIO and visual theme styling.
"""

import io
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt


# Palette matching UI theme
THEME_COLORS = {
    "primary": "#2E7D32",
    "primary_light": "#E8F5E9",
    "accent": "#4CAF50",
    "success": "#2E7D32",
    "warning": "#F59E0B",
    "danger": "#E53935",
    "indigo": "#388E3C",
    "purple": "#81C784",
    "gray": "#6B7280",
    "pie_colors": ["#2E7D32", "#4CAF50", "#81C784", "#66BB6A", "#A5D6A7", "#1B5E20"],
}


def render_fig_to_svg(fig) -> str:
    """
    Renders a Matplotlib Figure instance directly into an in-memory BytesIO SVG buffer,
    decodes it to a UTF-8 string, closes the figure to free memory, and returns the SVG string.
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", transparent=True)
    buffer.seek(0)
    svg_data = buffer.getvalue().decode("utf-8")
    buffer.close()
    plt.close(fig)
    return svg_data
